<template>
  <div class="question-viewer-container">
    <header class="practice-header">
      <div class="header-title">
        <h2>试题练习</h2>
        <p>按题号顺序练习，支持单选题与填空题</p>
      </div>
      <div class="header-progress">
        <div class="progress-text">进度 {{ currentIndex + 1 }} / {{ questions.length || 0 }}</div>
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
        </div>
      </div>
    </header>

    <div class="content-area">
      <div v-if="question">
        <article class="question-card">
          <div class="question-meta">
            <span class="meta-pill">第 {{ currentIndex + 1 }} 题</span>
            <span class="type-badge">{{ question.type }}</span>
            <span v-if="question.point" class="point-badge">考点：{{ question.point }}</span>
          </div>

          <h3 class="question-title">
            {{ question.stem }}
          </h3>

          <div v-if="question.type === '单选题'" class="options">
            <label
              class="option"
              :class="{ active: userAnswer === key }"
              v-for="(optionText, key) in question.options"
              :key="key"
            >
              <input
                type="radio"
                :value="key"
                v-model="userAnswer"
                class="option-input"
              />
              <span class="option-text">{{ key }}. {{ optionText }}</span>
            </label>
          </div>

          <div v-else class="blank-answer-box">
            <label class="blank-label">请输入你的答案（可多空用分号分隔）：</label>
            <textarea
              v-model.trim="userAnswer"
              class="blank-input"
              placeholder="例如：0；最大"
            />
          </div>

          <div class="action-row">
            <button class="submit-btn" @click="submitAnswer" :disabled="!canSubmit">
              提交答案
            </button>
          </div>

          <div v-if="showResult" class="result">
            <p
              v-if="question.type === '单选题' && userAnswer === question.answer"
              class="correct"
            >
              ✅ 正确
            </p>
            <p
              v-else-if="question.type === '单选题'"
              class="incorrect"
            >
              ❌ 错误，正确答案是：{{ question.answer }}
            </p>
            <p v-else class="blank-result">
              标准答案：{{ question.answer }}
            </p>
            <button @click="askAI" class="explain-btn">AI讲解</button>
          </div>

          <div v-if="loading" class="ai-loading">
            <p>正在加载中，请稍候...</p>
          </div>
          <div v-if="aiResponse" class="ai-response">
            <h4>AI解析</h4>
            <div ref="aiResponseContainer" v-html="aiResponse"></div>
          </div>
        </article>
      </div>
      <div v-else>
        <p>加载题目中...</p>
      </div>
    </div>

    <footer class="navigation">
      <button @click="prevQuestion" :disabled="currentIndex === 0">上一题</button>
      <button @click="nextQuestion" :disabled="currentIndex === questions.length - 1">下一题</button>
      <input
        type="number"
        v-model.number="jumpIndex"
        placeholder="题号"
        class="jump-input"
      />
      <button @click="jumpToQuestion" :disabled="!isValidJump">跳转题目</button>
    </footer>
  </div>
</template>
  
<script>
import {
  renderMarkdownWithMath,
  typesetMathInElement
} from "@/utils/contentRenderer";

export default {
  name: "QuestionViewer",
  data() {
    return {
      selectedMode: "deepseek",
      questions: [],
      currentIndex: 0,
      question: null,
      userAnswer: "",
      showResult: false,
      aiResponse: "",
      jumpIndex: null,
      loading: false,
      aiStreaming: false,
      aiTypesetTimer: null
    };
  },
  beforeUnmount() {
    if (this.aiTypesetTimer) {
      clearTimeout(this.aiTypesetTimer);
      this.aiTypesetTimer = null;
    }
  },
  computed: {
    progressPercent() {
      if (!this.questions.length) return 0;
      return Math.round(((this.currentIndex + 1) / this.questions.length) * 100);
    },
    canSubmit() {
      if (!this.question) return false;
      if (this.question.type === "单选题") {
        return !!this.userAnswer;
      }
      return true;
    },
    isValidJump() {
      return this.jumpIndex > 0 && this.jumpIndex <= this.questions.length;
    }
  },
  mounted() {
    this.selectedMode = this.$route.query.mode || "deepseek";
    fetch("/questionPracticeBank.json")
      .then((response) => response.json())
      .then((data) => {
        this.questions = data;
        this.loadQuestion();
      })
      .catch((error) => console.error("加载题库失败：", error));
  },
  methods: {
    loadQuestion() {
      this.question = this.questions[this.currentIndex] || null;
      this.userAnswer = "";
      this.showResult = false;
      this.aiResponse = "";
      this.aiStreaming = false;
    },
    submitAnswer() {
      this.showResult = true;
    },
    async askAI() {
      if (!this.question) return;
      const baseUrl = window.location.origin;
      this.loading = true;
      this.aiStreaming = true;
      this.aiResponse = "";

      const prompt =
        this.question.type === "单选题"
          ? `请解释以下选择题：题目：${this.question.stem}；选项：A. ${this.question.options.A || ""}，B. ${this.question.options.B || ""}，C. ${this.question.options.C || ""}，D. ${this.question.options.D || ""}；学生选择了：${this.userAnswer}；正确答案是：${this.question.answer}。请给出详细解析。`
          : `请解释以下填空题：题目：${this.question.stem}；学生填写：${this.userAnswer || "（未填写）"}；标准答案：${this.question.answer}。请给出知识点讲解和解题思路。`;

      try {
        await this.askAIWithStream(baseUrl, prompt);
      } catch (error) {
        console.error("AI讲解请求错误：", error);
        this.aiResponse = this.renderAiContent("AI讲解请求失败，请稍后重试。");
        this.typesetMath();
      } finally {
        this.loading = false;
        this.aiStreaming = false;
      }
    },
    typesetMath() {
      this.$nextTick(() => {
        const container = this.$refs.aiResponseContainer;
        typesetMathInElement(container).catch(() => {
          // 忽略排版失败
        });
      });
    },
    scheduleTypesetMath(delay = 200) {
      if (this.aiTypesetTimer) return;
      this.aiTypesetTimer = setTimeout(() => {
        this.aiTypesetTimer = null;
        this.typesetMath();
      }, delay);
    },
    renderAiContent(content) {
      return renderMarkdownWithMath(content);
    },
    async askAIWithStream(baseUrl, prompt) {
      const response = await fetch(`${baseUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: prompt, mode: this.selectedMode, stream: true })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const contentType = response.headers.get("content-type") || "";
      if (!response.body || !contentType.includes("text/event-stream")) {
        const data = await response.json();
        this.aiResponse = this.renderAiContent(data.response || "");
        this.typesetMath();
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";
      let done = false;
      let fullText = "";
      let pendingText = "";
      let flushTimer = null;

      const flushPendingText = (force = false) => {
        if (!pendingText && !force) return;
        if (pendingText) {
          fullText += pendingText;
          pendingText = "";
        }
        this.aiResponse = this.renderAiContent(fullText);
        if (force) {
          this.typesetMath();
        } else {
          this.scheduleTypesetMath();
        }
      };

      const scheduleFlush = () => {
        if (flushTimer) return;
        flushTimer = setTimeout(() => {
          flushTimer = null;
          flushPendingText(false);
        }, 40);
      };

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

          let payload = null;
          try {
            payload = JSON.parse(line.slice(6));
          } catch (e) {
            continue;
          }

          if (payload.type === "chunk" && payload.content) {
            pendingText += payload.content;
            scheduleFlush();
          } else if (payload.type === "error") {
            pendingText += payload.message || "生成讲解时发生错误。";
            if (flushTimer) {
              clearTimeout(flushTimer);
              flushTimer = null;
            }
            flushPendingText(true);
            done = true;
          } else if (payload.type === "done") {
            done = true;
          }
        }
      }

      if (flushTimer) {
        clearTimeout(flushTimer);
      }
      flushPendingText(true);

      if (!fullText.trim()) {
        this.aiResponse = this.renderAiContent("已完成生成，但未收到可显示的讲解内容。");
        this.typesetMath();
      }
    },
    prevQuestion() {
      if (this.currentIndex > 0) {
        this.currentIndex--;
        this.loadQuestion();
      }
    },
    nextQuestion() {
      if (this.currentIndex < this.questions.length - 1) {
        this.currentIndex++;
        this.loadQuestion();
      }
    },
    jumpToQuestion() {
      if (this.isValidJump) {
        this.currentIndex = this.jumpIndex - 1;
        this.loadQuestion();
      }
    }
  }
};
</script>

<style scoped>

.question-viewer-container {
  max-width: 1100px;
  max-height: calc(100vh - 160px); 
  margin: 56px auto 0;
  overflow-y: auto; 
  min-height: 90vh;
  display: flex;
  flex-direction: column;
  padding: 20px 20px 14px;
  background: linear-gradient(200deg, var(--color-primary-light), var(--color-primary-bg-strong));
}

.practice-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
  padding: 14px 16px;
  border-radius: 12px;
  background: var(--color-overlay-light);
  margin-bottom: 14px;
}
.header-title h2 {
  margin: 0;
  font-size: 24px;
  color: var(--color-text-main);
}
.header-title p {
  margin: 6px 0 0;
  color: var(--color-text-muted);
  font-size: 14px;
}
.header-progress {
  min-width: 240px;
}
.progress-text {
  font-size: 14px;
  color: var(--color-text-main);
  margin-bottom: 6px;
  text-align: right;
}
.progress-track {
  width: 100%;
  height: 8px;
  background: var(--color-border);
  border-radius: var(--radius-pill);
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary-dark), var(--color-primary));
  transition: width 0.25s ease;
}

/* 主内容区域 */
.content-area {
  flex: 1;
  background-color: var(--color-overlay-subtle);
  border-radius: 12px;
  padding: 16px;
  overflow-y: auto;
}

.question-card {
  background: var(--color-overlay-lighter);
  border-radius: 12px;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  padding: 16px 18px;
}

.question-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.meta-pill,
.point-badge {
  display: inline-block;
  font-size: 13px;
  font-weight: 600;
  border-radius: var(--radius-pill);
  padding: 4px 10px;
}
.meta-pill {
  color: var(--color-primary-ink);
  background: var(--color-primary-bg-soft);
}
.point-badge {
  color: var(--color-success);
  background: var(--color-success-bg);
}

/* 题目标题 */
.question-title {
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 24px;
  margin: 0 0 24px;
  color: var(--color-text-main);
}
.type-badge {
  display: inline-block;
  font-size: 13px;
  font-weight: 600;
  color: var(--color-primary-ink);
  background: var(--color-primary-bg-soft);
  padding: 4px 10px;
  border-radius: var(--radius-pill);
}

/* 选项样式 */
.options {
  margin-bottom: 24px;
}
.option {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  margin-bottom: 12px;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background-color: var(--color-surface-soft);
  transition: all 0.2s ease;
  cursor: pointer;
}
.option:hover {
  border-color: var(--color-primary);
  background-color: var(--color-primary-bg-soft);
}
.option.active {
  border-color: var(--color-primary-dark);
  background-color: var(--color-primary-bg-strong);
}
.option-input {
  cursor: pointer;
}
.option-text {
  font-size: 18px;
  color: var(--color-text-secondary);
}
.blank-answer-box {
  margin-bottom: 18px;
}
.blank-label {
  display: block;
  margin-bottom: 8px;
  color: var(--color-text-main);
  font-size: 16px;
  font-weight: 600;
}
.blank-input {
  width: 100%;
  min-height: 96px;
  border: 1px solid var(--color-border-strong);
  border-radius: 8px;
  padding: 10px;
  font-size: 16px;
  box-sizing: border-box;
  resize: vertical;
}

/* 按钮 */
.action-row {
  margin-bottom: 4px;
}
.submit-btn, .explain-btn, button {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  background-color: var(--color-primary-dark);
  color: var(--color-text-on-primary);
  cursor: pointer;
  transition: background-color 0.2s ease;
}
.submit-btn[disabled] {
  background-color: var(--color-text-subtle);
  cursor: not-allowed;
}

.result {
  margin-top: 15px;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: 8px;
  background: var(--color-surface-soft);
}
.correct {
  color: var(--color-success);
  font-weight: bold;
}
.incorrect {
  color: var(--color-danger);
  font-weight: bold;
}
.blank-result {
  color: var(--color-success);
  font-weight: bold;
}
.explain-btn {
  margin-top: 8px;
}
.ai-loading {
  margin-top: 14px;
  color: var(--color-text-secondary);
}
.ai-response {
  margin-top: 14px;
  padding: 12px;
  background: var(--color-surface);
  border-radius: 8px;
  border: 1px solid var(--color-border);
}

.navigation {
  margin-top: 14px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  justify-content: center;
  padding: 12px;
  border-radius: 10px;
  background: var(--color-overlay-soft);
}
.jump-input {
  width: 96px;
  padding: 6px;
  font-size: 16px;
  text-align: center;
  border-radius: 6px;
  border: 1px solid var(--color-border-strong);
}

button:disabled {
  background-color: var(--color-text-subtle);
}
button:hover:enabled {
  background-color: var(--color-primary-hover);
}

@media (max-width: 900px) {
  .practice-header {
    flex-direction: column;
    align-items: stretch;
  }
  .header-progress {
    min-width: 0;
  }
  .progress-text {
    text-align: left;
  }
  .question-title {
    font-size: 20px;
  }
  .option-text {
    font-size: 16px;
  }
}
</style>