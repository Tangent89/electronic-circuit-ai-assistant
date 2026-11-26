//通过python.ee.xidian.edu.cn使用本项目

本地开发环境以Python运行app.py文件即可启动程序，通过http://127.0.0.1:5000访问
（8081 是 npm run serve 的前端开发服务器端口，需另外启动 app.py 才能真正问答）

VUEworks文件夹为vue源码
APIKey.env文件用于保存APIKey等密钥（APIKey.env.example 为配置模板）
app.py为后端程序
dist文件夹为VUE项目打包后的静态文件
feedback_data.json用于存储用户留言反馈信息
打包提交.py用于生成剔除密钥与个人数据的提交压缩包

【提交前清理（重要）】
- 直接压缩整个文件夹会把 APIKey.env（真实密钥）和 feedback_data.json（真实姓名/邮箱/学号）一起交出去
- 正确做法：运行 python 打包提交.py，生成 源代码_提交版.zip
- 若密钥曾外发过，请到各厂商控制台重置密钥
- 正式部署请把 app.py 末尾的 debug=True 改为 debug=False

【API 修改】
- 密钥：编辑根目录 APIKey.env（DEEPSEEK_API_KEY / TENCENT_API_KEY / ZHIPU_API_KEY / QWEN_API_KEY）
- 云端模型名：app.py → DEFAULT_MODEL
- 本地模型：APIKey.env 或环境变量 OLLAMA_MODEL（需 ollama pull 对应模型）
- 助教人设：app.py → SYSTEM_PROMPT

【图片 修改】
- 首页三按钮：VUEworks/my-vue-project/src/assets/（datasearch / questionviewer / chatinterface，扩展名与 AgentSelector.vue 中一致）
- 资料查阅六按钮：src/assets/images/（basic-components、instrument-usage、analog-circuit-experiments、digital-circuit-experiments、rf-circuit-experiments、troubleshooting-guide）
- 元器件/仪器卡片图：public/images/components/ 与 public/images/instruments/（按 001、002 编号命名 PNG）
- 改前端后需 npm run build，并将 dist 复制到项目根目录 dist/
  （注意：整体替换而非合并，否则 dist/js、dist/css 会累积多份历史版本）

【离线依赖（重要）】
- marked 与 MathJax 已本地化到 VUEworks/my-vue-project/public/vendor/，不再依赖外网 CDN
- 因此答辩现场断网也能正常渲染 Markdown 与数学公式
- MathJax 使用 SVG 输出（tex-mml-svg.js），不会额外联网加载字体文件
- public/index.html 中的 51.la 访问统计已注释，如需访问量统计可取消注释

【前端路由与 404 回落】
- 前端是 history 模式路由，/questions、/analog-circuit-experiments/1 等路径后端并不存在
- app.py 中的 spa_fallback 会把页面导航请求回落到 index.html，保证深链接刷新不 404
- vue.config.js 的 publicPath 必须为 '/'；若为 './'，子页面刷新会因资源路径错误而白屏

【RAG 修改】
- 语料：database/*.md 增删改
- 建库：ollama pull nomic-embed-text → python build_rag_index.py → 生成 database/rag_index/store.json
- 关闭：APIKey.env 设 RAG_ENABLED=0，或 POST /chat 传 use_rag:false
- 嵌入模型：环境变量 OLLAMA_EMBED_MODEL（与建库、检索须一致）

RAG知识库：将实验相关 Markdown 放在 database 目录下，安装 Ollama 后执行 ollama pull nomic-embed-text，再运行 python build_rag_index.py 生成 database/rag_index/store.json。后端启动后会自动在问答中注入检索片段；可设置环境变量 RAG_ENABLED=0 关闭，或在 POST /chat 中传 use_rag:false。