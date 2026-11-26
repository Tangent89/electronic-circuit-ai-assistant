<template>
  <div class="module-page">
    <section class="module-header">
      <h2>模拟电路实验学习中心</h2>
      <p>
        先在下表中选择实验，进入详情页阅读「实验目的、仪器设备、实验内容与要求」；
        需要加深理解时，再使用右侧 AI 辅助答疑或针对某一实验发起讲解。
      </p>
    </section>

    <section class="module-layout">
      <div class="resource-panel">
        <h3>实验列表（共 5 项）</h3>
        <article v-for="doc in analogDocs" :key="doc.id" class="resource-card">
          <h4>{{ doc.title }}</h4>
          <p class="card-hint">{{ doc.intro }}</p>
          <div class="card-actions">
            <button type="button" @click="openAiLesson(doc.title, doc.intro)">AI 辅助讲解</button>
            <button type="button" @click="openDetail(doc.id)">查看实验详情</button>
          </div>
        </article>

      </div>

      <aside class="ai-panel">
        <h3>AI 辅助（模拟电路）</h3>
        <p class="ai-tip">与上方实验列表配合使用：可先做通用问答，也可进入某一实验后再点「AI 辅助讲解」获得针对性说明。</p>
        <button type="button" @click="openPreset('请按「原理要点—操作步骤—示波器/仪表读数—常见现象与误差来源」的顺序，概括一次典型模拟电路实验的学习路径。')">学习路径说明</button>
        <button type="button" @click="openPreset('请出 3 道模拟电路实验相关的选择题（含答案与简要解析），侧重运放或分立放大电路基础。')">自测小题</button>
        <button type="button" @click="openPreset('请列出模拟电路实验中常见的接线、供电与测量类问题，并给出排查顺序。')">测量与排错要点</button>
        <textarea v-model="customQuestion" placeholder="补充提问（可与当前实验或通用概念相关）"></textarea>
        <button type="button" :disabled="!customQuestion.trim()" @click="askCustom">发送提问</button>
      </aside>
    </section>
  </div>
</template>

<script>
import { ANALOG_EXPERIMENT_ORDER } from "@/data/analogExperimentDetails";
import { analogExperimentContent } from "@/data/analogExperimentContent";

/** 与各实验标题对应的简短导读，便于列表页上下文连贯 */
const EXPERIMENT_INTROS = {
  "opamp-application":
    "侧重集成运放的线性与比例运算：传输特性、动态范围、幅频特性与负载能力等概念的建立与测量。",
  "ce-cc-amplifier":
    "从单级共射放大电路入手，理解静态工作点、增益与输入输出阻抗，并衔接共集与相关扩展思路。",
  "differential-amplifier":
    "围绕差分放大器的差模/共模特性与共模抑制比，理解对称电路与恒流源改善性能的作用。",
  "active-filter-opamp":
    "利用运放构成有源滤波器，掌握低通、高通与级联带通的设计思路与频率响应测量要点。",
  "opamp-nonlinear-waveform":
    "进入运放非线性应用与振荡电路，理解正弦、方波与占空比可调波形的实现与调试思路。"
};

export default {
  name: "AnalogCircuitExperiments",
  data() {
    return {
      selectedMode: 'deepseek',
      analogDocs: [],
      customQuestion: ''
    }
  },
  mounted() {
    this.selectedMode = this.$route.query.mode || 'deepseek';
    this.analogDocs = ANALOG_EXPERIMENT_ORDER.map((id) => ({
      id,
      title: analogExperimentContent[id].title,
      intro: EXPERIMENT_INTROS[id] || ""
    }));
  },
  methods: {
    openDetail(id) {
      this.$router.push({
        path: `/analog-circuit-experiments/${id}`,
        query: { mode: this.selectedMode }
      });
    },
    openChat(prompt) {
      this.$router.push({
        path: '/chat',
        query: {
          topic: encodeURIComponent(prompt),
          mode: this.selectedMode
        }
      });
    },
    openAiLesson(experimentName, intro) {
      const ctx = intro ? `背景说明：${intro}` : "";
      this.openChat(
        `请针对模拟电路实验「${experimentName}」做结构化讲解（先实验目的与仪器，再按内容要求分步说明原理与操作要点）。${ctx} 请补充安全用电、示波器共地与常见测量误区。`
      );
    },
    openPreset(prompt) {
      this.openChat(prompt);
    },
    askCustom() {
      this.openChat(`【模拟电路实验模块】${this.customQuestion.trim()}`);
    }
  }
}
</script>

<style scoped>
.module-page {
  width: 90%;
  margin: 60px auto 0;
  max-height: calc(100vh - 130px);
  overflow-y: auto;
}

.module-header {
  background: var(--color-overlay-panel);
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 16px;
}

.module-header h2 {
  margin: 0 0 8px;
}

.module-header p {
  margin: 0;
  color: var(--color-text-secondary);
}

.module-layout {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
}

.resource-panel, .ai-panel {
  background: var(--color-overlay-panel);
  border-radius: 10px;
  padding: 16px;
}

.resource-card {
  border: 1px solid var(--color-border-faint);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.resource-card h4 {
  margin: 0 0 8px;
}

.card-hint {
  margin: 0 0 10px;
  color: var(--color-text-secondary);
  font-size: 14px;
}

.resource-card p {
  margin: 0 0 8px;
  color: var(--color-text-main);
}

.resource-card pre {
  margin: 0 0 10px;
  white-space: pre-wrap;
  background: var(--color-surface-soft);
  border-radius: 6px;
  padding: 8px;
}

.card-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.doc-link {
  color: var(--color-primary-dark);
  text-decoration: none;
}

.ai-tip {
  color: var(--color-text-secondary);
  font-size: 14px;
}

button {
  border: none;
  border-radius: 6px;
  background-color: var(--color-primary-dark);
  color: var(--color-text-on-primary);
  padding: 8px 12px;
  margin: 6px 0;
  cursor: pointer;
}

button:disabled {
  background: var(--color-disabled-bg);
  cursor: not-allowed;
}

textarea {
  width: 100%;
  min-height: 90px;
  border: 1px solid var(--color-border-strong);
  border-radius: 6px;
  padding: 8px;
  box-sizing: border-box;
  margin-top: 8px;
}

.empty-text {
  color: var(--color-text-subtle);
}

@media (max-width: 1000px) {
  .module-layout {
    grid-template-columns: 1fr;
  }
}
</style>
