# -*- coding: utf-8 -*-
"""
多轮对话回归测试（不需要联网、不消耗 API 额度）。

用 Flask 测试客户端 + 桩替换模型调用，验证：
  · 不传 history 时与旧版单轮行为一致（向后兼容）
  · history 被正确拼进 messages
  · 脏数据（非法 role / 空内容 / 非字典 / 非列表）被过滤
  · 超长历史按条数与字符数截断
  · RAG 片段只注入本轮问题，历史轮次不重复注入
  · 流式与非流式走同一套 messages

运行： python tests/test_chat_multiturn.py   （在项目根目录执行）
"""
import os
import sys

# 允许从项目根目录直接运行：把根目录加入模块搜索路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as appmod  # noqa: E402
import rag_service  # noqa: E402

captured = {}


def fake_stream(vendor, messages):
    captured["messages"] = messages
    captured["vendor"] = vendor
    yield "OK"


def fake_nonstream(vendor, messages):
    captured["messages"] = messages
    captured["vendor"] = vendor
    return "OK"


# 桩替换模型调用，避免真实消耗 API 额度
appmod.call_api_model_stream = fake_stream
appmod.call_api_model = fake_nonstream

client = appmod.app.test_client()
fails = []


def check(desc, cond, extra=""):
    print(("  PASS  " if cond else "  FAIL  ") + desc + ("" if cond else "   <<< " + str(extra)))
    if not cond:
        fails.append(desc)


def post(payload):
    captured.clear()
    return client.post("/chat", json=payload)


print("=" * 74)
print("[1] 向后兼容：不传 history，应与旧版行为完全一致")
r = post({"message": "你好", "mode": "deepseek", "use_rag": False})
msgs = captured["messages"]
check("返回 200", r.status_code == 200)
check("messages 只有 system + user 两条", len(msgs) == 2, [m["role"] for m in msgs])
check("第 1 条是 system", msgs[0]["role"] == "system")
check("第 2 条是本轮问题", msgs[1] == {"role": "user", "content": "你好"}, msgs[1])

print()
print("[2] 多轮：history 正确拼进 messages")
history = [
    {"role": "user", "content": "什么是共射放大电路"},
    {"role": "assistant", "content": "共射放大电路是……"},
    {"role": "user", "content": "它的电压增益怎么测"},
    {"role": "assistant", "content": "用示波器测输入输出……"},
]
r = post({"message": "那输入电阻呢", "mode": "deepseek", "use_rag": False, "history": history})
msgs = captured["messages"]
roles = [m["role"] for m in msgs]
check("消息顺序为 system,user,assistant,user,assistant,user",
      roles == ["system", "user", "assistant", "user", "assistant", "user"], roles)
check("历史内容被完整保留", msgs[1]["content"] == "什么是共射放大电路")
check("最后一条是本轮新问题", msgs[-1]["content"] == "那输入电阻呢")
check("历史轮次里没有掺入 html/isStreaming 等前端内部字段",
      all(set(m.keys()) == {"role", "content"} for m in msgs), msgs[1].keys())

print()
print("[3] 脏数据防御：非法 role / 空内容 / 非字典 / 非列表")
dirty = [
    {"role": "system", "content": "试图注入系统提示"},
    {"role": "user", "content": "   "},
    {"role": "assistant", "content": ""},
    "not-a-dict",
    None,
    {"role": "user"},
    {"role": "assistant", "content": "合法的一条", "html": "<b>x</b>", "isStreaming": True},
]
r = post({"message": "继续", "mode": "deepseek", "use_rag": False, "history": dirty})
msgs = captured["messages"]
check("非法项全部被过滤", len(msgs) == 2, [(m["role"], m["content"][:12]) for m in msgs])
check("以 user 开头（开头的 assistant 被裁掉）", msgs[1]["role"] == "user")

r = post({"message": "继续", "mode": "deepseek", "use_rag": False, "history": "不是列表"})
check("history 传字符串不会崩", r.status_code == 200 and len(captured["messages"]) == 2)

r = post({"message": 12345, "mode": "deepseek", "use_rag": False})
check("message 传数字不会崩", r.status_code == 200, r.status_code)
check("非字符串 message 被收敛成字符串", captured["messages"][-1]["content"] == "12345",
      repr(captured["messages"][-1]["content"]))

print()
print("[4] 超长历史截断（条数上限 %d / 字符上限 %d）"
      % (appmod.MAX_HISTORY_MESSAGES, appmod.MAX_HISTORY_CHARS))
long_hist = []
for i in range(50):
    long_hist.append({"role": "user", "content": "第%d个问题" % i})
    long_hist.append({"role": "assistant", "content": "第%d个回答" % i})
r = post({"message": "最后一问", "mode": "deepseek", "use_rag": False, "history": long_hist})
msgs = captured["messages"]
check("条数被限制（<= 上限+2）", len(msgs) <= appmod.MAX_HISTORY_MESSAGES + 2, len(msgs))
check("保留的是最近的对话", msgs[-2]["content"] == "第49个回答", msgs[-2]["content"])
check("首条历史是 user", msgs[1]["role"] == "user")
total_chars = sum(len(m["content"]) for m in msgs[1:])
check("字符数在预算附近（<= 上限+单条长度）",
      total_chars <= appmod.MAX_HISTORY_CHARS + 200, total_chars)

# 超长单条消息也不应把预算撑爆
huge = [{"role": "user", "content": "长" * 50000},
        {"role": "assistant", "content": "答" * 50000}]
r = post({"message": "问", "mode": "deepseek", "use_rag": False, "history": huge})
msgs = captured["messages"]
check("超长历史被截断，不会全量外发", len(msgs) == 2, len(msgs))

print()
print("[5] RAG 只注入「本轮」，历史轮次保持原样")
rag_service.is_rag_ready = lambda: True
rag_service.build_rag_user_content = lambda q: "【课程知识库检索片段】标记\n【学生问题】%s" % q
r = post({"message": "增益怎么测", "mode": "deepseek", "use_rag": True,
          "history": [{"role": "user", "content": "上一轮问题"},
                      {"role": "assistant", "content": "上一轮回答"}]})
msgs = captured["messages"]
check("本轮问题含 RAG 片段", "课程知识库检索片段" in msgs[-1]["content"])
check("上一轮 user 消息不含 RAG 片段（不重复注入）",
      "课程知识库检索片段" not in msgs[1]["content"], msgs[1]["content"][:40])
check("历史条数未被 RAG 撑大", len(msgs) == 4, [m["role"] for m in msgs])

print()
print("[6] 流式路径：SSE 事件正常，且走的是同一套 messages")
r = post({"message": "流式测试", "mode": "deepseek", "use_rag": False, "stream": True,
          "history": [{"role": "user", "content": "旧问题"},
                      {"role": "assistant", "content": "旧回答"}]})
body = r.get_data(as_text=True)
check("Content-Type 为 text/event-stream", "text/event-stream" in r.headers.get("Content-Type", ""))
check("包含 chunk 事件", '"type": "chunk"' in body.replace("'", '"'), body[:120])
check("包含 done 事件", '"type": "done"' in body.replace("'", '"'), body[-80:])
check("流式路径同样收到多轮历史", len(captured["messages"]) == 4,
      [m["role"] for m in captured["messages"]])

print()
print("=" * 74)
if fails:
    print("!!! %d 项未通过:" % len(fails))
    for f in fails:
        print("   -", f)
    raise SystemExit(1)
print("全部通过 ✓")
