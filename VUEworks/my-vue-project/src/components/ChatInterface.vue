<template>
  <div id="chatInterface">
    <div class="main">
      <section class="chat-header">
        <div>
          <h2>AI 自由问答</h2>
          <p>可提问实验原理、接线步骤、数据分析与故障排查。</p>
        </div>
        <span class="mode-badge">当前模型：{{ modeLabel }}</span>
      </section>

      <div ref="chatWindow" class="chat-window">
        <div v-if="streamingActive" class="streaming-banner-row">
          <div class="streaming-banner-inner">
            <div class="streaming-banner">
              <span class="streaming-spinner" aria-hidden="true"></span>
              <span>AI正在思考中</span>
            </div>
            <button
              type="button"
              class="stop-stream-btn"
              :disabled="!canAbortStream"
              @click="stopStreamOutput"
            >
              终止输出
            </button>
          </div>
        </div>
        <div
          v-for="(msg, index) in messages"
          :key="`${msg.role}-${index}`"
          class="message"
          :class="msg.role"
        >
          <div class="role-tag">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
          <div class="bubble-wrap">
            <div
              class="bubble"
              v-html="msg.html || (msg.isStreaming ? '正在思考中...' : '')"
            ></div>
            <span
              v-if="msg.role === 'bot' && msg.isStreaming"
              class="stream-cursor"
            ></span>
          </div>
        </div>
      </div>
      
      <div class="input-area">
        <textarea
                  v-model="userInput"
                  placeholder="请输入内容（Enter 发送，Shift+Enter 换行）" 
                  @input="autoResize" 
                  @keydown.enter.exact.prevent="sendMessage"
                  rows="1"></textarea>
        <button class="primary-btn" :disabled="loading" @click="sendMessage">
          {{ loading ? "生成中..." : "发送" }}
        </button>
        <button class="ghost-btn" id="clearHistoryBtn" :disabled="loading" @click="clearHistory">清除记录</button>
      </div>
      
    </div>
  </div>
</template>

<script>
import {
  renderMarkdownWithMath,
  renderPlainText,
  typesetMathInElement
} from "@/utils/contentRenderer";

export default {
  name: 'ChatInterface',
  data() {
    return {
      selectedMode: '',  // 从 AgentSelector 路由参数中传入的调用模式
      userInput: '',
      loading: false,
      streamingActive: false,
      streamAbortController: null,
      messages: [],
      scrollRafId: null,
      typesetTimer: null
    }
  },
  beforeUnmount() {
    if (this.scrollRafId) {
      window.cancelAnimationFrame(this.scrollRafId);
      this.scrollRafId = null;
    }
    if (this.typesetTimer) {
      clearTimeout(this.typesetTimer);
      this.typesetTimer = null;
    }
    this.messages.forEach((msg) => {
      if (msg && msg.flushTimer) {
        clearTimeout(msg.flushTimer);
      }
    });
  },
  computed: {
    modeLabel() {
      const map = {
        deepseek: "DeepSeek API",
        local: "DeepSeek 本地",
        tencent: "腾讯混元",
        zhipu: "智谱 GLM",
        qwen: "通义千问"
      };
      return map[this.selectedMode] || this.selectedMode || "未设置";
    },
    canAbortStream() {
      return !!this.streamAbortController;
    }
  },
  mounted() {
    // 从路由参数中获取调用模型模式，例如 /chat?mode=local 或 ?mode=api
    this.selectedMode = this.$route.query.mode || 'deepseek';
    this.loadHistory();

    // 检查是否有传入的 topic 和 response 参数
    const topic = this.$route.query.topic;
    if (topic) {
      const prompt = decodeURIComponent(topic);
      this.addMessage('user', prompt, false);
      this.autoSendMessage(prompt);
    } else if (this.messages.length === 0) {
      this.displayPresetGreeting();
    }
    if (this.$route.query.topic) {
      // 替换路由地址，清除 topic 保留 mode 参数
      const { mode } = this.$route.query
      this.$router.replace({ path: this.$route.path, query: {mode} });
    }
  },

  methods: {
    scrollToBottom() {
      this.$nextTick(() => {
        const chatWindow = this.$refs.chatWindow;
        if (chatWindow) {
          chatWindow.scrollTop = chatWindow.scrollHeight;
        }
      });
    },
    typesetMath() {
      this.$nextTick(() => {
        const target = this.$refs.chatWindow || undefined;
        typesetMathInElement(target).catch(() => {
          // 忽略排版失败，避免影响主流程
        });
      });
    },
    scheduleTypesetMath(delay = 180) {
      if (this.typesetTimer) return;
      this.typesetTimer = setTimeout(() => {
        this.typesetTimer = null;
        this.typesetMath();
      }, delay);
    },
    containsMathSyntax(text) {
      return /(\$\$|\\\(|\\\[|\$(?:\\.|[^$\n])+\$)/.test(String(text || ""));
    },
    scheduleScrollToBottom() {
      if (this.scrollRafId) return;
      this.scrollRafId = window.requestAnimationFrame(() => {
        this.scrollRafId = null;
        this.scrollToBottom();
      });
    },
    renderContent(content, asMarkdown = true) {
      if (!asMarkdown) {
        return renderPlainText(content);
      }
      return renderMarkdownWithMath(content);
    },
    addMessage(role, content, asMarkdown = true) {
      this.messages.push({
        role,
        content,
        html: this.renderContent(content, asMarkdown),
        isStreaming: false,
        pendingChunk: "",
        flushTimer: null
      });
      this.saveHistory();
      this.scrollToBottom();
      if (role === 'bot') this.typesetMath();
    },
    addStreamingBotPlaceholder() {
      this.messages.push({
        role: "bot",
        content: "",
        html: "",
        isStreaming: true,
        pendingChunk: "",
        flushTimer: null
      });
      this.scrollToBottom();
      return this.messages.length - 1;
    },
    flushStreamingContent(index, asMarkdown = true) {
      const target = this.messages[index];
      if (!target) return;
      const pendingChunk = target.pendingChunk || "";
      if (!pendingChunk) return;
      target.pendingChunk = "";
      target.content += pendingChunk;
      target.html = this.renderContent(target.content, asMarkdown);
      target.isStreaming = true;
      this.scheduleScrollToBottom();
      if (this.containsMathSyntax(pendingChunk)) {
        this.scheduleTypesetMath();
      }
    },
    appendStreamingContent(index, chunk, asMarkdown = true) {
      const target = this.messages[index];
      if (!target) return;
      target.pendingChunk = (target.pendingChunk || "") + chunk;
      if (target.flushTimer) return;
      target.flushTimer = setTimeout(() => {
        target.flushTimer = null;
        this.flushStreamingContent(index, asMarkdown);
      }, 40);
    },
    stopStreamOutput() {
      if (this.streamAbortController) {
        this.streamAbortController.abort();
      }
    },
    finalizeStreamingBotMessage(botIndex, aborted) {
      if (botIndex === null || botIndex === undefined) return;
      const botMsg = this.messages[botIndex];
      if (!botMsg || botMsg.role !== "bot") return;
      if (botMsg.flushTimer) {
        clearTimeout(botMsg.flushTimer);
        botMsg.flushTimer = null;
      }
      this.flushStreamingContent(botIndex, true);
      botMsg.isStreaming = false;
      if (aborted) {
        if (botMsg.content.trim()) {
          botMsg.content = `${botMsg.content.trimEnd()}\n\n*（输出已终止）*`;
        } else {
          botMsg.content = "输出已终止。";
        }
        botMsg.html = this.renderContent(botMsg.content, true);
      } else if (!botMsg.content.trim()) {
        botMsg.content = "已完成响应，但未收到可显示内容。";
        botMsg.html = this.renderContent(botMsg.content, true);
      }
      this.saveHistory();
      this.scheduleTypesetMath(0);
    },
    saveHistory() {
      localStorage.setItem('chatHistory', JSON.stringify(this.messages));
    },
    loadHistory() {
      const raw = localStorage.getItem('chatHistory');
      if (!raw) return;
      try {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          this.messages = parsed
            .filter((item) => item && (item.role === 'user' || item.role === 'bot'))
            .map((item) => ({
              role: item.role,
              content: String(item.content || ''),
              html: this.renderContent(String(item.content || ''), item.role === 'bot'),
              isStreaming: false
            }));
          this.scrollToBottom();
          this.typesetMath();
        }
      } catch (error) {
        console.error('读取聊天历史失败:', error);
      }
    },
    autoResize(event) {
      const textarea = event.target;
      textarea.style.height = 'auto';
      textarea.style.height = textarea.scrollHeight + 'px';
    },

    async autoSendMessage(topic) {
      this.loading = true;
      this.streamingActive = true;
      try {
        await this.sendMessageWithStream(topic);
        this.typesetMath();
      } catch (error) {
        if (error && error.name === "AbortError") {
          return;
        }
        console.error("AutoSendMessage 错误：", error);
        this.addMessage("bot", "调用模型时发生错误，请稍后重试。", true);
      } finally {
        this.loading = false;
        this.streamingActive = false;
      }
    },

    async sendMessage() {
      const message = this.userInput.trim();
      if (!message) return;
      this.addMessage('user', message, false);
      // 清空输入框
      this.userInput = '';
      
      // 显示加载状态
      this.loading = true;
      this.streamingActive = true;
      
      try {
        await this.sendMessageWithStream(message);
        this.typesetMath();
      } catch (error) {
        if (error && error.name === "AbortError") {
          return;
        }
        console.error("请求错误:", error);
        this.addMessage("bot", "调用模型时发生错误，请稍后重试。", true);
      } finally {
        this.loading = false;
        this.streamingActive = false;
      }
    },
    buildHistoryPayload(currentMessage) {
      // 把已有对话整理成后端要的多轮上下文 [{role:'user'|'assistant', content}]。
      // 注意：this.messages 里已经包含「本轮」这条 user 消息（sendMessage 与
      // mounted 中的 topic 流程都会先 addMessage），必须排除，否则本轮问题会重复发送。
      const prior = this.messages.slice();
      const last = prior[prior.length - 1];
      if (last && last.role === 'user' && last.content === currentMessage) {
        prior.pop();
      }
      return prior
        .filter((m) => (m.role === 'user' || m.role === 'bot'))
        .filter((m) => !m.isStreaming && typeof m.content === 'string' && m.content.trim())
        .map((m) => ({
          role: m.role === 'user' ? 'user' : 'assistant',
          content: m.content
        }));
    },
    async sendMessageWithStream(message) {
      const ac = new AbortController();
      this.streamAbortController = ac;
      const signal = ac.signal;
      let botIndex = null;

      try {
        const baseUrl = window.location.origin;
        const response = await fetch(`${baseUrl}/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          signal,
          body: JSON.stringify({
            message,
            mode: this.selectedMode,
            stream: true,
            // 多轮对话上下文：让模型能记住之前的问答（后端会做条数与字符数截断）
            history: this.buildHistoryPayload(message)
          })
        });

        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const contentType = response.headers.get("content-type") || "";
        // 兼容后端未启用流式时的 JSON 返回。
        if (!response.body || !contentType.includes("text/event-stream")) {
          const data = await response.json();
          this.addMessage("bot", data.response || "", true);
          return;
        }

        botIndex = this.addStreamingBotPlaceholder();
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        let done = false;

        while (!done) {
          const { value, done: streamDone } = await reader.read();
          if (streamDone) break;
          buffer += decoder.decode(value, { stream: true });

          const events = buffer.split("\n\n");
          buffer = events.pop() || "";

          for (const eventBlock of events) {
            const line = eventBlock
              .split("\n")
              .find((l) => l.startsWith("data: "));
            if (!line) continue;

            const payloadText = line.slice(6);
            let payload = null;
            try {
              payload = JSON.parse(payloadText);
            } catch (e) {
              continue;
            }

            if (payload.type === "chunk" && payload.content) {
              this.appendStreamingContent(botIndex, payload.content, true);
            } else if (payload.type === "error") {
              this.appendStreamingContent(
                botIndex,
                payload.message || "调用模型时发生错误，请稍后重试。",
                true
              );
            } else if (payload.type === "done") {
              done = true;
            }
          }
        }

        this.finalizeStreamingBotMessage(botIndex, false);
      } catch (error) {
        if (error && (error.name === "AbortError" || signal.aborted)) {
          this.finalizeStreamingBotMessage(botIndex, true);
          return;
        }
        throw error;
      } finally {
        this.streamAbortController = null;
      }
    },
    clearHistory() {
      localStorage.removeItem("chatHistory");
      this.messages = [];
      this.displayPresetGreeting();
    },
    displayPresetGreeting() {
      const greeting = "您好！我是您的电子实验教师，专注于实验答疑、自动出题、答案解析和智能批改工作。请告诉我您需要的帮助或提出您的问题。";
      this.addMessage('bot', greeting, true);
      this.typesetMath();
    }
  }
}
</script>

<style scoped>
#chatInterface {
  width: 100%;
}

.main {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 70px);
  width: min(92%, 1420px);
  margin: 0 auto;
  margin-top: 60px;
  background: var(--color-surface);
  border-radius: 14px;
  border: 1px solid var(--color-border-soft);
  box-shadow: var(--shadow-elevated);
  overflow: hidden;
}

.chat-header {
  margin: 14px 14px 0;
  padding: 12px 14px;
  border-radius: 12px;
  background: var(--color-overlay-light);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.chat-header h2 {
  margin: 0 0 4px;
  font-size: 20px;
}

.chat-header p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 14px;
}

.mode-badge {
  display: inline-block;
  background: var(--color-primary-bg-soft);
  color: var(--color-primary-ink);
  border: 1px solid var(--color-primary-light);
  padding: 4px 10px;
  border-radius: var(--radius-pill);
  font-size: 13px;
  white-space: nowrap;
}

.chat-window {
  flex: 1;
  margin: 12px 14px 0;
  border-radius: 12px;
  padding: 14px;
  padding-bottom: 76px;
  overflow-y: auto;
  background: var(--color-surface);
  border: 1px solid var(--color-border-soft);
}

.streaming-banner-row {
  position: sticky;
  top: 0;
  z-index: 2;
  display: flex;
  justify-content: center;
  width: 100%;
  margin-bottom: 10px;
}

.streaming-banner-inner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.streaming-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  width: fit-content;
  background: var(--color-primary-alpha-12);
  color: var(--color-primary-ink);
  border: 1px solid var(--color-primary-dark-alpha-35);
  border-radius: var(--radius-pill);
  padding: 4px 12px 4px 10px;
  font-size: 12px;
}

.stop-stream-btn {
  padding: 4px 12px;
  border-radius: var(--radius-pill);
  font-size: 12px;
  cursor: pointer;
  border: 1px solid var(--color-border-strong);
  background: var(--color-surface);
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.stop-stream-btn:hover:not(:disabled) {
  background: var(--color-surface-strong);
  border-color: var(--color-text-muted);
  color: var(--color-text-main);
}

.stop-stream-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.streaming-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid var(--color-primary-dark-alpha-35);
  border-top-color: var(--color-primary-ink);
  border-radius: 50%;
  flex-shrink: 0;
  animation: streaming-spin 0.75s linear infinite;
}

@keyframes streaming-spin {
  to {
    transform: rotate(360deg);
  }
}

.input-area {
  margin: 10px 14px 14px;
  padding: 10px;
  background-color: var(--color-surface);
  border: 1px solid var(--color-border-soft);
  border-radius: 12px;
  box-shadow: var(--shadow-soft);
  display: flex;
  align-items: flex-end;
  gap: 10px;
}

.input-area textarea {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid var(--color-border-strong);
  border-radius: 8px;
  font-size: 15px;
  outline: none;
  resize: none;
  overflow-y: auto;
  line-height: 1.5;
  white-space: pre-wrap;
  min-height: 22px;
  max-height: 160px;
}

.input-area textarea:focus {
  border-color: var(--color-primary-light);
  box-shadow: 0 0 0 2px var(--color-primary-alpha-30);
}

.input-area button {
  padding: 9px 14px;
  border: none;
  border-radius: 8px;
  color: var(--color-text-on-primary);
  font-size: 14px;
  cursor: pointer;
  white-space: nowrap;
}

.input-area button:disabled {
  opacity: 0.68;
  cursor: not-allowed;
}

.primary-btn {
  background-color: var(--color-primary-dark);
}

.primary-btn:hover {
  background-color: var(--color-primary-hover);
}

.ghost-btn {
  background: var(--color-surface-strong);
  color: var(--color-text-secondary) !important;
}

.ghost-btn:hover {
  background: var(--color-border-soft);
}

.message {
  display: flex;
  align-items: flex-start;
  margin-bottom: 15px;
  gap: 8px;
  width: 100%;
  box-sizing: border-box;
}

.message.user {
  flex-direction: row;
  justify-content: flex-end;
  align-items: flex-end;
}

.message.bot {
  justify-content: flex-start;
}

.role-tag {
  min-width: 32px;
  height: 24px;
  border-radius: var(--radius-pill);
  background: var(--color-primary-bg-strong);
  color: var(--color-primary-ink);
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-top: 4px;
}

.message .bubble {
  max-width: 74%;
  padding: 10px 14px;
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.5;
  word-wrap: break-word;
  white-space: normal;
}

.bubble-wrap {
  display: inline-flex;
  align-items: flex-end;
}

.message.user .bubble {
  order: 1;
  background: var(--color-primary-dark);
  color: var(--color-text-on-primary);
  border-bottom-right-radius: 0;
}

.message.bot .bubble {
  background-color: var(--color-surface-strong);
  color: var(--color-text-main);
  border-bottom-left-radius: 0;
}

.message.user .role-tag {
  order: 1;
  margin-right: 8px;
  margin-left: 0;
}

.message.user .bubble-wrap {
  order: 2;
}

.stream-cursor {
  width: 7px;
  height: 18px;
  margin-left: 4px;
  background: var(--color-primary-dark);
  border-radius: 2px;
  animation: cursorBlink 0.9s steps(1) infinite;
}

.bubble :deep(p) {
  margin: 0 0 8px;
}

.bubble :deep(p:last-child) {
  margin-bottom: 0;
}

.bubble :deep(pre) {
  background: var(--color-overlay-subtle);
  border-radius: 6px;
  padding: 8px;
  overflow-x: auto;
}

.bubble :deep(.math-block) {
  overflow-x: auto;
  margin: 8px 0;
}

.bubble :deep(.math-inline) {
  display: inline;
}

@keyframes cursorBlink {
  0%, 49% { opacity: 1; }
  50%, 100% { opacity: 0.08; }
}

@media (max-width: 1000px) {
  .main {
    width: 100%;
  }

  .chat-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .message .bubble {
    max-width: 86%;
  }
}
</style>
