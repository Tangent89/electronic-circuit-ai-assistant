from flask import Flask, request, jsonify, send_from_directory, redirect, Response, stream_with_context
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI

import rag_service

# 后端整体职责：
# 1) 提供 /chat 与 /feedback 接口
# 2) 统一封装多模型（云端 + 本地 Ollama）调用
# 3) 在需要时注入 RAG 检索上下文，提升课程问答相关性
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, 'APIKey.env'))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-v2:16b")
# RAG：存在 database/rag_index/store.json 且未禁用时，在问答前注入知识库片段
RAG_ENABLED = os.getenv("RAG_ENABLED", "1").strip().lower() not in ("0", "false", "no", "off")
# 多轮对话：前端可传 history=[{role, content}]，此处限制注入上下文的上限，
# 防止长对话把 token 撑爆（条数与字符数双重限制，均为保守值）。
MAX_HISTORY_MESSAGES = int(os.getenv("CHAT_HISTORY_MAX_MESSAGES", "20"))
MAX_HISTORY_CHARS = int(os.getenv("CHAT_HISTORY_MAX_CHARS", "16000"))

# 统一初始化各家 OpenAI Client
clients = {
    "deepseek": OpenAI(
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"),  # DeepSeek 兼容端点
    "tencent": OpenAI(
        api_key=os.getenv("TENCENT_API_KEY"),
        base_url="https://api.hunyuan.cloud.tencent.com/v1"),  # 混元
    "zhipu": OpenAI(
        api_key=os.getenv("ZHIPU_API_KEY"),
        base_url="https://open.bigmodel.cn/api/paas/v4"),  # 智谱
    "qwen": OpenAI(
        api_key=os.getenv("QWEN_API_KEY"),   # 千问
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"),
}
# 默认模型映射
DEFAULT_MODEL = {
    "deepseek": "deepseek-v4-flash",
    "tencent": "hunyuan-standard",
    "zhipu": "glm-4-flashx",
    "qwen": "qwen-max",
}

SYSTEM_PROMPT = (
    "你是一名专业的电子线路实验课程助教，精通数字电路、模拟电路和射频电路的理论与实验操作。"
    "你的主要职责是协助学生完成实验学习，具体包括以下几个方面："
    "解答问题：准确回答学生关于电路原理、器件特性、实验步骤、仪器使用（如示波器、信号发生器、频谱分析仪等）以及故障排查等方面的问题。对于复杂概念，能用通俗易懂的方式解释，并结合实际电路举例说明。"
    "生成试题：能够根据课程内容自动生成不同难度（基础、进阶、挑战）和不同题型（选择题、填空题、简答题、分析设计题、实验操作题）的练习题或考试题。试题应紧扣教学大纲，覆盖数电、模电、射频电路的关键知识点。"
    "提供答案解析：对于每道试题，不仅要给出正确答案，还要提供详细的解析，包括解题思路、关键公式、常见错误分析，并尽可能给出多种解题方法（例如理论分析、仿真验证、实验测量等），帮助学生从多角度理解知识点。"
    "智能化批改与反馈：对于主观题、设计题和实验报告，能够进行智能化批改与评分。能够识别学生的常见错误，指出问题所在，并给出有针对性的改进建议；对于电路设计类题目，能够评估设计的合理性、性能指标，并建议优化方向。"
    "实验指导：强调实验安全与规范操作，提醒学生注意仪器正确使用、电路连接规范、避免短路等常见风险。对于实验过程中可能出现的现象，能预判并提供排查思路。"
    "个性化学习建议：根据学生的提问记录和答题情况，识别其知识薄弱点，推荐相关的复习内容或进阶实验，帮助其规划学习路径。"
    "你始终以耐心、专业、鼓励的态度与学生互动，确保回答准确、清晰，并引导学生主动思考和探索。"
    "注意数学公式的输出格式，数学公式需要以适合html环境下的格式进行输出"
)

app = Flask(__name__, static_folder="dist", static_url_path="")
CORS(app)


@app.route("/")  # 路由配置
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/chat", methods=["GET", "POST"])
def chat():
    # POST: 处理问答请求；GET: 返回前端页面（便于直接访问 /chat）
    if request.method == "POST":
        data = request.get_json() or {}
        # message 做类型收敛，避免前端传来非字符串时下游 .strip() 报错
        user_message = str(data.get("message") or "")
        mode = data.get("mode", "deepseek")  # 默认使用 deepseek 模型
        stream = bool(data.get("stream", False))
        use_rag = bool(data.get("use_rag", True))
        # 多轮对话上下文（可选）：不传则退化为单轮问答，与旧版本行为一致
        history = normalize_history(data.get("history"))
        # RAG 检索片段只注入「本轮」问题；历史轮次保持原样，既不重复注入也省 token
        user_effective = prepare_user_message_for_rag(user_message, use_rag)
        messages = build_messages(history, user_effective)

        if stream:
            # 流式模式：以 SSE 持续推送 chunk，前端逐段渲染
            @stream_with_context
            def event_stream():
                for event in stream_model_sse(mode, messages):
                    yield event

            headers = {
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
            return Response(event_stream(), mimetype="text/event-stream", headers=headers)

        response_text = call_model(mode, messages)
        return jsonify({"response": response_text})
    else:
        # GET 请求返回前端静态页面
        return send_from_directory("dist", "index.html")


def normalize_history(raw) -> list[dict]:
    """
    把前端传来的 history 规整成 OpenAI 格式的消息列表。

    前端可能传 null / 非列表 / 缺字段 / 夹杂内部字段（html、isStreaming 等），
    这里统一过滤，只保留 role ∈ {user, assistant} 且 content 为非空字符串的项。
    """
    if not isinstance(raw, list):
        return []
    cleaned: list[dict] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role not in ("user", "assistant"):
            continue
        if not isinstance(content, str) or not content.strip():
            continue
        cleaned.append({"role": role, "content": content})
    return cleaned


def trim_history(history: list[dict]) -> list[dict]:
    """
    从最近的消息往前保留，受「条数」与「字符数」双重限制。

    截断后若首条是 assistant，会一并去掉，保证上下文以 user 消息开头
    （否则部分厂商会对消息顺序报错，也容易让模型把助手发言当成新指令）。
    """
    kept: list[dict] = []
    total = 0
    for item in reversed(history[-MAX_HISTORY_MESSAGES:]):
        total += len(item["content"])
        if kept and total > MAX_HISTORY_CHARS:
            break
        kept.append(item)
    kept.reverse()
    while kept and kept[0]["role"] != "user":
        kept.pop(0)
    return kept


def build_messages(history: list[dict], user_message: str) -> list[dict]:
    """组装最终发给大模型的消息列表：system + 历史 + 本轮问题。"""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(trim_history(history))
    messages.append({"role": "user", "content": user_message})
    return messages


def prepare_user_message_for_rag(raw: str, use_rag: bool) -> str:
    """若启用 RAG 且索引已就绪，将检索到的课程片段拼入用户内容。"""
    if not RAG_ENABLED or not use_rag:
        return raw
    if not rag_service.is_rag_ready():
        return raw
    return rag_service.build_rag_user_content(raw)


def call_model(mode: str, messages: list[dict]) -> str:  # 调用指定模型并返回文本结果
    # 统一分发入口：local -> Ollama，本地外其余走云端兼容 OpenAI 接口
    if mode == "local":
        return call_local_model(messages)
    elif mode in clients:
        return call_api_model(mode, messages)  # Response 对象
    else:
        return "不支持的模型类型"


# ---------------------------
# 调用 API 模型的函数
def call_api_model(vendor: str, messages: list[dict]):
    client = clients[vendor]
    model = DEFAULT_MODEL[vendor]

    try:
        chat = client.chat.completions.create(
            model=model,
            messages=messages,
            timeout=300,  # SDK 原生参数；也可用 client.timeout = 30
            # stream=True        # 前端流式显示
        )
        return chat.choices[0].message.content.strip()
    except Exception as e:
        # SDK 已细分异常，如 RateLimitError / APIConnectionError
        print(f"[{vendor}] API 调用异常:", e)
        return "调用模型时发生错误，请稍后重试。"


def call_api_model_stream(vendor: str, messages: list[dict]):
    client = clients[vendor]
    model = DEFAULT_MODEL[vendor]
    stream = client.chat.completions.create(
        model=model,
        messages=messages,
        timeout=300,
        stream=True,
    )

    # 兼容不同厂商返回结构，统一提取增量文本 delta.content
    for chunk in stream:
        choices = getattr(chunk, "choices", None) or []
        if not choices:
            continue
        delta = getattr(choices[0], "delta", None)
        if not delta:
            continue
        text = getattr(delta, "content", None)
        if text:
            yield text


def sse_event(payload: dict) -> str:
    # SSE 格式：每条消息以 "data: <json>\n\n" 结尾
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def stream_model_sse(mode: str, messages: list[dict]):
    # 将不同来源的流式文本统一包装为前端约定事件：
    # chunk: 增量文本；error: 错误提示；done: 流结束
    try:
        if mode in clients:
            for text in call_api_model_stream(mode, messages):
                yield sse_event({"type": "chunk", "content": text})
        elif mode == "local":
            for text in call_local_model_stream(messages):
                yield sse_event({"type": "chunk", "content": text})
        else:
            yield sse_event({"type": "error", "message": "不支持的模型类型"})
        yield sse_event({"type": "done"})
    except Exception as e:
        print("[stream] API 调用异常:", e)
        yield sse_event({"type": "error", "message": "调用模型时发生错误，请稍后重试。"})
        yield sse_event({"type": "done"})


# 调用本地部署 deepseek 模型（Ollama）的函数
def call_local_model(messages: list[dict]):
    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "stream": False,
                "messages": messages,
            },
            timeout=300,
        )
        resp.raise_for_status()
        payload = resp.json()
        message = (payload.get("message") or {}).get("content", "")
        return message.strip() or "模型未返回有效内容。"
    except requests.RequestException as e:
        print("[local] Ollama 调用异常:", e)
        return "本地模型调用失败，请确认 Ollama 服务已启动且模型已拉取。"
    except Exception as e:
        print("[local] 未知异常:", e)
        return "本地模型调用发生未知错误，请稍后重试。"


def call_local_model_stream(messages: list[dict]):
    try:
        with requests.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "stream": True,
                    "messages": messages,
                },
                stream=True,
                timeout=300,
        ) as resp:
            resp.raise_for_status()
            # Ollama 流式接口按行返回 JSON；每行都可能包含 message.content 增量
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg = payload.get("message") or {}
                content = msg.get("content", "")
                if content:
                    yield content

                if payload.get("done") is True:
                    break
    except Exception as e:
        print("[local-stream] Ollama 调用异常:", e)
        yield "本地模型流式调用失败，请确认 Ollama 服务和模型状态。"


# 新增路由，方法为 POST，用于接收前端的反馈数据。
@app.route("/feedback", methods=["POST"])
def feedback():
    # 轻量反馈持久化：读取历史 -> 追加当前记录 -> 回写 JSON 文件
    data = request.get_json()
    # 使用 zoneinfo 获取当前北京时间
    try:
        beijing_time = datetime.now(ZoneInfo("Asia/Shanghai"))
    except Exception as e:
        print("加载时区数据失败，请确认 tzdata 模块是否安装:", e)
        # 此处可做默认处理，例如使用 UTC 时间
        beijing_time = datetime.utcnow()
    data["timestamp"] = beijing_time.isoformat()
    # 使用 basedir 定位文件路径
    file_path = os.path.join(basedir, "feedback_data.json")
    # data 示例:
    # {
    #   "name": "张三",
    #   "email": "zhangsan@example.com",
    #   "message": "应用很好，但希望增加新功能……",
    #   "timestamp": "2025-04-08T12:34:56"
    # }

    # 存储到一个 JSON 文件中
    try:
        # 先读取原有存在的反馈数据
        with open(file_path, "r", encoding="utf-8") as f:
            feedback_list = json.load(f)
    except FileNotFoundError:
        feedback_list = []  # 文件不存在时，初始化为空列表
    except Exception as e:
        print("读取反馈数据文件失败：", e)
        feedback_list = []
    feedback_list.append(data)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(feedback_list, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("写入反馈数据文件错误：", e)

    return jsonify({"status": "success"})


@app.errorhandler(404)
def spa_fallback(_err):
    """
    前端使用 history 模式路由（createWebHistory），因此 /questions、
    /analog-circuit-experiments/1 这类前端路由并不存在于后端。
    浏览器直接访问或在此类子页面按 F5 刷新时，后端需回落到 index.html，
    由前端路由接管，否则会返回 404 并白屏。

    仅对「浏览器页面导航」回落（GET/HEAD 且 Accept 含 text/html），
    缺失的静态资源、接口请求仍返回 404，避免掩盖真实错误。
    """
    accept = request.headers.get("Accept", "")
    if request.method in ("GET", "HEAD") and "text/html" in accept:
        return send_from_directory(app.static_folder, "index.html")
    return jsonify({"error": "not found"}), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
