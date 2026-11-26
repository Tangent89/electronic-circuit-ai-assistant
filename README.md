# 电子线路实验课程 AI 助教系统

基于大语言模型的 B/S 架构教学辅助系统：Vue 3 前端 + Flask 后端，支持多厂商 API、本地 Ollama、RAG 课程知识库检索增强。

---

## 一、项目结构

```text
素材与源代码/
├── app.py                 # Flask 后端：/chat、/feedback，多模型与 RAG，含 SPA 404 回落
├── rag_service.py         # RAG 检索与上下文拼接
├── build_rag_index.py     # 从 database/*.md 离线构建向量索引
├── APIKey.env             # API 密钥与环境变量（勿提交到公开仓库）
├── APIKey.env.example     # 配置模板：复制为 APIKey.env 后填入自己的密钥
├── .gitignore             # 已忽略密钥、个人数据、node_modules、缓存
├── 打包提交.py            # 生成「可安全提交」的压缩包（剔除密钥并扫描残留）
├── tests/                 # 回归测试（多轮对话）
│   ├── test_chat_multiturn.py   # 后端：消息组装/截断/脏数据/RAG 注入范围
│   └── test_history_payload.js  # 前端：buildHistoryPayload 的过滤与映射
├── database/              # RAG 语料（*.md）与索引 rag_index/store.json
├── dist/                  # 前端打包产物（由 Flask 直接托管）
├── feedback_data.json     # 用户留言反馈（运行后自动生成/追加）
├── VUEworks/my-vue-project/   # Vue 3 源码
│   ├── public/            # 不打包、原样发布的静态资源
│   │   └── vendor/        # 本地化的 marked / MathJax（离线可用，见 4.7）
│   ├── src/
│   │   ├── components/    # 页面组件
│   │   ├── data/          # 实验详情等内容（JS 模块）
│   │   ├── router/        # 路由
│   │   ├── assets/        # 经 import 引用的图片等
│   │   └── styles/theme.css
│   └── vue.config.js      # 开发代理、publicPath
└── readme.txt             # 简要说明（可与本 README 对照）
```

| 目录 | 用途 |
|------|------|
| `src/` | 参与 webpack 打包的源码与 `import` 资源 |
| `public/` | 构建时复制到站点根目录；适合 JSON、大量按路径访问的图片 |
| `dist/` | `npm run build` 输出，需复制到项目根目录供 `app.py` 使用 |

---

## 二、快速运行

### 2.1 后端（生产/一体化部署）

```bash
# 安装依赖（示例）
pip install flask flask-cors python-dotenv openai requests

# 配置 APIKey.env 后启动
python app.py
```

浏览器访问：`http://127.0.0.1:5000`（默认端口 5000，`app.py` 末尾可改）。

### 2.2 前端开发（热更新）

```bash
cd VUEworks/my-vue-project
npm install
npm run serve
```

访问：`http://127.0.0.1:8081`。`vue.config.js` 已将 `/chat`、`/feedback` 代理到 `http://localhost:5000`，需同时启动 `app.py`。

### 2.3 前端打包并更新 dist

```bash
cd VUEworks/my-vue-project
npm run build
```

将生成的 `VUEworks/my-vue-project/dist/` **整体复制** 到项目根目录的 `dist/`，再运行 `python app.py`。

### 2.4 RAG 知识库（可选）

```bash
ollama pull nomic-embed-text
python build_rag_index.py
```

索引输出：`database/rag_index/store.json`。问答时默认启用 RAG（见下文 `RAG_ENABLED`）。

### 2.5 本地大模型（可选）

```bash
ollama pull deepseek-v2:16b   # 或与 OLLAMA_MODEL 一致的模型名
ollama serve
```

前端选择「DeepSeek本地」即 `mode=local`。

---

## 三、代码说明

### 3.1 后端 `app.py`

| 模块 | 说明 |
|------|------|
| `clients` / `DEFAULT_MODEL` | 各云厂商 OpenAI 兼容客户端与默认模型名 |
| `SYSTEM_PROMPT` | 全局助教人设与回答规范 |
| `POST /chat` | 参数：`message`、`mode`、`stream`、`use_rag`、`history` |
| `call_local_model*` | 调用 Ollama `/api/chat`（流式/非流式） |
| `prepare_user_message_for_rag` | 问答前注入检索片段 |
| `normalize_history` / `trim_history` / `build_messages` | 多轮对话上下文：清洗、截断、组装 messages |
| `POST /feedback` | 留言写入 `feedback_data.json` |
| `spa_fallback` | 404 回落：前端 history 路由深链接刷新不 404（见 4.7） |

`mode` 取值：`deepseek`、`local`、`tencent`、`zhipu`、`qwen`（与前端首页模型切换一致）。

### 3.2 前端路由 `src/router/index.js`

| 路径 | 页面 |
|------|------|
| `/` | 智能体入口（资料查阅 / 试题 / 问答） |
| `/chat` | AI 自由问答 |
| `/questions` | 试题练习 |
| `/basic-components` | 基础元器件 |
| `/instrument-usage` | 仪器设备 |
| `/analog-circuit-experiments` | 模拟电路实验列表 |
| `/analog-circuit-experiments/:id` | 模拟实验详情 |
| `/digital-circuit-experiments` | 数字电路实验 |
| `/rf-circuit-experiments` | 射频电路实验 |
| `/troubleshooting-guide` | 故障排查 |
| `/feedback` | 留言反馈 |

实验详情正文来自 `src/data/*ExperimentContent.js`、`*ExperimentDetails.js`。

### 3.3 RAG 流程

1. `database/*.md` → `build_rag_index.py` 切分、向量化 → `store.json`
2. 用户提问 → `rag_service.retrieve_chunks` → 拼入 user 消息 → 再调用大模型

---

## 四、常见修改指南（改哪里）

### 4.1 API 密钥与后端环境变量 — `APIKey.env`

在项目根目录新建或编辑 **`APIKey.env`**（与 `app.py` 同级）：

```env
DEEPSEEK_API_KEY=你的密钥
TENCENT_API_KEY=你的密钥
ZHIPU_API_KEY=你的密钥
QWEN_API_KEY=你的密钥

# 可选
RAG_ENABLED=1
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MODEL=deepseek-v2:16b
```

> **安全提示**：不要将真实密钥提交到 Git；答辩演示可用环境变量或本地文件。

**改云端模型名称**：编辑 `app.py` 中 `DEFAULT_MODEL` 字典（如 `deepseek-v4-flash`）。

**改助教人设**：编辑 `app.py` 中 `SYSTEM_PROMPT` 字符串。

**关闭 RAG**：`APIKey.env` 设 `RAG_ENABLED=0`，或请求体传 `"use_rag": false`。

**RAG 参数**（`rag_service.py` / `build_rag_index.py` 会读取）：

- `OLLAMA_EMBED_MODEL`（默认 `nomic-embed-text`）
- `RAG_TOP_K`、`RAG_MIN_SCORE`
- `RAG_CHUNK_SIZE`、`RAG_CHUNK_OVERLAP`（仅建库脚本）

> ⚠️ **注意**：这些参数请用 **系统环境变量** 设置，**不要写在 `APIKey.env` 里**。
> 原因是 `app.py` 中 `import rag_service` 早于 `load_dotenv()`，而 `rag_service.py`
> 在模块导入时就把这些值读走了，因此写在 `.env` 中不会生效。
> 只有 `RAG_ENABLED`、`OLLAMA_MODEL`（对话用）写在 `APIKey.env` 中是有效的。
> 彻底修复方式：把 `app.py` 里的 `load_dotenv(...)` 移到 `import rag_service` 之前。

---

### 4.2 图片资源

#### （1）首页三个大按钮图标

| 文件 | 说明 |
|------|------|
| `src/assets/datasearch.svg`（或 `.png`） | 资料查阅 |
| `src/assets/questionviewer.svg` | 试题练习 |
| `src/assets/chatinterface.svg` | 自由问答 |

修改位置：`src/components/AgentSelector.vue` 模板里 `src="@/assets/xxx.png"` — **扩展名需与文件一致**（当前仓库多为 `.svg`，若引用 `.png` 请改模板或补 PNG 文件）。

#### （2）资料查阅六个子模块右侧配图

目录：**`src/assets/images/`**

| 文件名 | 对应模块 |
|--------|----------|
| `basic-components.svg` | 基础元器件 |
| `instrument-usage.svg` | 仪器设备 |
| `analog-circuit-experiments.svg` | 模拟电路 |
| `digital-circuit-experiments.svg` | 数字电路 |
| `rf-circuit-experiments.svg` | 射频电路 |
| `troubleshooting-guide.svg` | 故障排查 |

替换图片：覆盖同名文件，或改 `AgentSelector.vue` 顶部 `import ... from "@/assets/images/xxx"` 的路径与后缀。

#### （3）元器件 / 仪器卡片实物图与原理图

放在 **`public/images/`**（构建后访问路径为 `/images/...`）：

```text
public/images/components/real/component-001.png
public/images/components/schematic/component-001.png
public/images/instruments/real/instrument-001.png
public/images/instruments/schematic/instrument-001.png
```

编号 `001` 与 JSON 列表顺序对应（见 `BasicComponents.vue`、`InstrumentUsage.vue` 中 `padStart(3, "0")`）。也可在 JSON 字段里直接写完整 URL（如 `现实图像`、`原理图像`）。

#### （4）站点图标、校徽等

- `public/XDUlogo.svg`
- `public/index.html` 中 `<link rel="icon" ...>` 的 `favicon`

---

### 4.3 业务数据（非 RAG）

| 内容 | 文件 | 使用页面 |
|------|------|----------|
| 元器件库 | `public/electronicComponents.json` | `BasicComponents.vue` |
| 仪器设备 | `public/labInstruments.json` | `InstrumentUsage.vue` |
| 试题题库 | `public/questionPracticeBank.json` | `QuestionViewer.vue` |
| 模拟实验 | `src/data/analogExperimentContent.js` 等 | 对应列表/详情组件 |
| 数字实验 | `src/data/digitalExperimentContent.js` | 同上 |
| 射频实验 | `src/data/rfExperimentContent.js` | 同上 |

增删实验：改 `*Content.js` 中的条目与路由 `id`，并在列表组件中保持链接一致。

---

### 4.4 RAG 课程文档

| 操作 | 位置 |
|------|------|
| 新增/修改实验讲义 | `database/*.md` |
| 重建索引 | 运行 `python build_rag_index.py` |
| 索引文件 | `database/rag_index/store.json`（可删后重建） |

---

### 4.5 界面文案与样式

| 修改项 | 文件 |
|--------|------|
| 浏览器标题、外链脚本 | `public/index.html` |
| 全站主色、圆角、阴影 | `src/styles/theme.css` |
| 顶栏标题、主页/返回逻辑 | `src/components/HeaderBar.vue` |
| 首页主标题、子模块文案 | `src/components/AgentSelector.vue` |
| 全局背景渐变 | `src/App.vue` |

---

### 4.6 开发代理与部署路径

| 修改项 | 文件 |
|--------|------|
| 开发时后端地址 | `vue.config.js` → `devServer.proxy` 的 `target` |
| 打包后资源路径 | `vue.config.js` → `publicPath: '/'`（**必须为绝对根路径**，原因见 4.7） |
| 后端端口 | `app.py` 末尾 `app.run(..., port=5000)` |

线上部署可参考 `readme.txt`：`python.ee.xidian.edu.cn` 等环境需按平台要求配置 WSGI 与静态目录。

---

### 4.7 离线依赖与前端路由（重要）

**（1）第三方前端库已本地化，不再依赖外网 CDN**

| 库 | 位置 | 说明 |
|----|------|------|
| marked v15.0.7 | `public/vendor/marked.min.js` | Markdown 渲染，与 `package.json` 中依赖版本一致 |
| MathJax v3.2.2 | `public/vendor/mathjax/tex-mml-svg.js` | 数学公式渲染，采用 **SVG 输出**，不额外下载字体文件 |

原先二者从 `cdn.jsdelivr.net` 加载，一旦答辩现场断网或 CDN 不可达，
AI 回答会退化成未渲染的纯文本、公式完全失效。现已改为本地引用，**完全离线可用**。

> 升级方式：替换 `public/vendor/` 下同名文件即可。若换成 CHTML 输出
> （`tex-mml-chtml.js`），还需一并复制 `output/chtml/fonts/woff-v2/` 字体目录，
> 否则公式会缺字。建议保持 SVG 输出。

**（2）51.la 访问统计已注释**

`public/index.html` 中的第三方统计脚本会向外部域名上报访客数据，且为外域同步脚本，
网络不通时会拖慢首页加载。目前**已注释**（取消注释即可恢复）。
若论文需要访问量统计数据，请自行决定是否启用。

**（3）前端为 history 模式路由，依赖后端 404 回落**

前端使用 `createWebHistory()`，因此 `/questions`、`/analog-circuit-experiments/1`
等路径并不存在于后端。`app.py` 中的 `spa_fallback`（404 处理器）会把
「浏览器页面导航」请求回落到 `index.html`，保证**深链接直接访问或按 F5 刷新不会 404**。
缺失的静态资源与接口请求仍正常返回 404。

同时注意两点：

- `vue.config.js` 的 `publicPath` 必须是 `'/'`。若改成 `'./'`，在
  `/analog-circuit-experiments/1` 这类子页面刷新时，资源会被解析成
  `/analog-circuit-experiments/js/app.js` 而加载失败（白屏）。
- `public/index.html` 中引用本地库也必须用绝对路径 `/vendor/...`，同理。

**（4）更新 `dist/` 时请整体替换，不要合并**

`npm run build` 会生成带哈希的新文件名。若只是把新产物「复制进去」而不删除旧文件，
`dist/js`、`dist/css` 会不断累积历史版本（体积膨胀数倍）。正确做法：
先删除项目根目录的 `dist/`，再把 `VUEworks/my-vue-project/dist/` 整个复制过来。

---

## 五、接口速查

### POST `/chat`

```json
{
  "message": "用户问题",
  "mode": "deepseek",
  "stream": true,
  "use_rag": true,
  "history": [
    { "role": "user", "content": "上一轮问题" },
    { "role": "assistant", "content": "上一轮回答" }
  ]
}
```

- `stream: true` → SSE，`data: {"type":"chunk","content":"..."}`，结束 `type: done`
- `stream: false` → `{"response": "完整回答"}`
- `history`（可选）→ **多轮对话上下文**。不传则退化为单轮问答，与旧版本行为一致。
  - 只接受 `role ∈ {user, assistant}` 且 `content` 为非空字符串的项，其余自动过滤
  - 后端会做截断保护：最多 `CHAT_HISTORY_MAX_MESSAGES`（默认 20）条、
    合计不超过 `CHAT_HISTORY_MAX_CHARS`（默认 16000）字符，从最近的消息往前保留
  - 截断后若首条是 assistant 会被去掉，保证上下文以 user 开头
  - RAG 检索片段**只注入本轮问题**，历史轮次原样发送，既不重复注入也省 token

> 前端 `ChatInterface.vue` 的 `buildHistoryPayload()` 负责组装该字段，
> 会自动排除本轮问题本身、正在流式输出中的消息以及空消息。
> 回归测试：`python tests/test_chat_multiturn.py`、`node tests/test_history_payload.js`

### POST `/feedback`

```json
{
  "name": "姓名",
  "email": "邮箱",
  "message": "留言内容"
}
```

---

## 六、依赖一览

**Python**：`flask`、`flask-cors`、`python-dotenv`、`openai`、`requests`

**Node（前端）**：见 `VUEworks/my-vue-project/package.json`

**外部服务**：各厂商 API；可选 Ollama（对话 + RAG 嵌入）

---

## 七、常见问题

1. **改了前端页面但线上没变** → 是否重新 `npm run build` 并更新了根目录 `dist/`。  
2. **本地模型无响应** → Ollama 是否运行、`OLLAMA_MODEL` 是否已 `ollama pull`。  
3. **RAG 不生效** → 是否存在 `database/rag_index/store.json`，`RAG_ENABLED` 是否为 1。  
4. **8081 能访问但问答失败** → 开发模式下需同时启动 `app.py`（5000 端口）。  
5. **图片不显示** → 区分 `src/assets`（import）与 `public/images`（URL 路径），扩展名与代码一致。  
6. **子页面刷新后 404 或白屏** → 确认 `publicPath` 为 `'/'`、`app.py` 中有 `spa_fallback`，详见 4.7。  
7. **Markdown / 公式不渲染** → 确认 `dist/vendor/marked.min.js` 与 `dist/vendor/mathjax/tex-mml-svg.js` 存在（离线依赖未随 `dist` 一起部署时会失效）。  
8. **RAG 参数改了没反应** → 这些参数不能用 `APIKey.env` 配置，见 4.1 末尾的说明。

---

## 八、交付 / 提交前的安全清理（重要）

项目根目录的 `APIKey.env` 保存着**真实可用的 API 密钥**，`feedback_data.json`
保存着**真实姓名 / 邮箱 / 学号**。直接压缩整个文件夹提交会造成密钥泄露。

推荐流程：

```bash
# 1) 生成一份剔除了密钥、个人数据、node_modules 的提交压缩包
python 打包提交.py            # 输出 源代码_提交版.zip
```

该脚本会：

- 排除 `APIKey.env`、`feedback_data.json`、`VUEworks/my-vue-project/node_modules/`、
  `__pycache__/`、`.idea/` 等；
- 用**脱敏后**的示例留言写入压缩包内；
- 对包内所有文本文件做一次密钥扫描（`sk-` 开头的 Key、学号邮箱），
  有残留会明确告警。

其他注意事项：

- 压缩包中不含 `APIKey.env`，接收方需复制 `APIKey.env.example` 为 `APIKey.env` 并填写自己的密钥。
- 若 `APIKey.env` 曾被提交到公开仓库或外发过，**请到各厂商控制台把密钥全部重置**，
  因为密钥一旦外泄即视为永久泄露。
- 生产部署请把 `app.py` 末尾的 `debug=True` 改为 `debug=False`
  （Werkzeug 调试器可执行任意代码，仅适合本地开发）。

---

## 九、相关文档
  
- `readme.txt` — 极简部署说明  

