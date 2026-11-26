/**
 * 前端 buildHistoryPayload 的回归测试（不需要浏览器、不需要联网）。
 *
 * 做法：从 ChatInterface.vue 中取出【真实的】<script> 块 -> 去掉 import ->
 * export default 换成 module.exports -> require 进来直接调用。
 * 这样测的是源文件里那段代码本身，而不是另抄一份的副本。
 *
 * 运行： node tests/test_history_payload.js   （在项目根目录执行）
 */
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");
const vuePath = path.join(root, "VUEworks", "my-vue-project", "src", "components", "ChatInterface.vue");
const src = fs.readFileSync(vuePath, "utf8");

const m = src.match(/<script>([\s\S]*?)<\/script>/);
if (!m) {
  console.error("FAIL  未能从 .vue 中提取 <script> 块");
  process.exit(1);
}

let js = m[1];
js = js.replace(/^\s*import[\s\S]*?from\s+['"][^'"]+['"];?[ \t]*$/gm, "");
js = js.replace(/export\s+default\s*/, "module.exports = ");

const tmp = path.join(__dirname, "_extracted_chatinterface.js");
fs.writeFileSync(tmp, js, "utf8");

let comp;
try {
  comp = require(tmp);
} catch (e) {
  console.error("FAIL  提取出的组件脚本无法加载:", e.message);
  fs.unlinkSync(tmp);
  process.exit(1);
}

const methods = comp.methods || {};
const fn = methods.buildHistoryPayload;
if (typeof fn !== "function") {
  console.error("FAIL  未在 components.methods 中找到 buildHistoryPayload");
  fs.unlinkSync(tmp);
  process.exit(1);
}
console.log("已从源文件提取到 buildHistoryPayload（" + fn.toString().split("\n").length + " 行）\n");

let fails = 0;
function check(desc, cond, extra) {
  console.log((cond ? "  PASS  " : "  FAIL  ") + desc + (cond ? "" : "   <<< " + JSON.stringify(extra)));
  if (!cond) fails++;
}
function call(messages, current) {
  return fn.call({ messages }, current);
}

const GREETING = "您好！我是您的电子实验教师，专注于实验答疑、自动出题、答案解析和智能批改工作。";

console.log("[1] 常规 sendMessage 路径（末尾是本轮 user 消息，必须排除）");
let msgs = [
  { role: "bot", content: GREETING, isStreaming: false },
  { role: "user", content: "什么是共射放大电路", isStreaming: false },
  { role: "bot", content: "共射放大电路是……", isStreaming: false },
  { role: "user", content: "那输入电阻呢", isStreaming: false },
];
let out = call(msgs, "那输入电阻呢");
check("本轮消息未被重复包含", out.filter((x) => x.content === "那输入电阻呢").length === 0, out);
check("历史条数为 3", out.length === 3, out.length);
check("bot 被映射为 assistant", out[0].role === "assistant" && out[2].role === "assistant", out.map((x) => x.role));
check("user 保持 user", out[1].role === "user", out.map((x) => x.role));
check("只保留 role/content 两个字段", out.every((x) => Object.keys(x).sort().join() === "content,role"), out[0]);

console.log("\n[2] 首轮对话（历史里只有开场白）");
out = call([{ role: "bot", content: GREETING, isStreaming: false },
            { role: "user", content: "你好", isStreaming: false }], "你好");
check("只剩开场白一条", out.length === 1 && out[0].role === "assistant", out);

console.log("\n[3] 过滤中间态与空内容");
out = call([
  { role: "user", content: "问题一", isStreaming: false },
  { role: "bot", content: "正在生成的一半", isStreaming: true },
  { role: "bot", content: "", isStreaming: false },
  { role: "bot", content: "   ", isStreaming: false },
  { role: "bot", content: "完整回答", isStreaming: false },
  { role: "user", content: "问题二", isStreaming: false },
], "问题二");
check("isStreaming 中的消息被排除", !out.some((x) => String(x.content).includes("正在生成")), out);
check("空/纯空白被排除，非空保留", out.length === 2 && out[1].content === "完整回答", out);

console.log("\n[4] localStorage 恢复的历史（loadHistory 后的结构）");
out = call([
  { role: "user", content: "旧问题", html: "<p>旧问题</p>", isStreaming: false },
  { role: "bot", content: "旧回答", html: "<p>旧回答</p>", isStreaming: false },
  { role: "user", content: "新问题", isStreaming: false },
], "新问题");
check("html 字段不会外发", out.every((x) => !("html" in x)), out);
check("历史正确映射", out.map((x) => x.role).join() === "user,assistant", out.map((x) => x.role));

console.log("\n[5] 边界：messages 为空 / 末尾不是本轮消息");
check("空消息列表返回空数组", call([], "随便").length === 0);
out = call([{ role: "user", content: "问题一", isStreaming: false }], "不匹配的内容");
check("末尾与当前消息不一致时不误删", out.length === 1, out);

console.log("\n[6] 长度：50 轮对话时前端仍然全量发送（截断交给后端，保持职责单一）");
msgs = [];
for (let i = 0; i < 50; i++) {
  msgs.push({ role: "user", content: "问题" + i, isStreaming: false });
  msgs.push({ role: "bot", content: "回答" + i, isStreaming: false });
}
msgs.push({ role: "user", content: "最后一问", isStreaming: false });
out = call(msgs, "最后一问");
check("前端发送 100 条历史（由后端截断到 20 条）", out.length === 100, out.length);

fs.unlinkSync(tmp);
console.log("\n" + "=".repeat(60));
if (fails) {
  console.log("!! " + fails + " 项未通过");
  process.exit(1);
}
console.log("前端方法全部通过 ✓");
