<template>
  <div class="module-page">
    <section class="module-header">
      <h2>数字电路实验学习中心</h2>
      <p>
        先在下表中选择实验，进入详情页阅读「实验目的、仪器设备、实验任务及要求」；
        需要加深理解时，再使用右侧 AI 辅助答疑或针对某一实验发起讲解。
      </p>
    </section>

    <section class="module-layout">
      <div class="resource-panel">
        <h3>实验列表（共 6 项）</h3>
        <article v-for="doc in digitalDocs" :key="doc.id" class="resource-card">
          <h4>{{ doc.title }}</h4>
          <p class="card-hint">{{ doc.intro }}</p>
          <div class="card-actions">
            <button type="button" @click="openAiLesson(doc.title, doc.intro)">AI 辅助讲解</button>
            <button type="button" @click="openDetail(doc.id)">查看实验详情</button>
          </div>
        </article>
      </div>

      <aside class="ai-panel">
        <h3>AI 辅助（数字电路）</h3>
        <p class="ai-tip">与上方实验列表配合使用：可先做通用问答，也可进入某一实验后再点「AI 辅助讲解」获得针对性说明。</p>
        <button type="button" @click="openPreset('请按「逻辑功能—真值表/时序—接线与测量—常见现象与排错」的顺序，概括一次典型数字电路实验的学习路径。')">学习路径说明</button>
        <button type="button" @click="openPreset('请出 3 道数字电路实验相关的选择题（含答案与简要解析），侧重组合逻辑或时序电路基础。')">自测小题</button>
        <button type="button" @click="openPreset('请列出数字电路实验中常见的电源、逻辑电平与测量类问题，并给出排查顺序。')">测量与排错要点</button>
        <textarea v-model="customQuestion" placeholder="补充提问（可与当前实验或通用概念相关）"></textarea>
        <button type="button" :disabled="!customQuestion.trim()" @click="askCustom">发送提问</button>
      </aside>
    </section>
  </div>
</template>

<script>
import { DIGITAL_EXPERIMENT_ORDER } from "@/data/digitalExperimentDetails";
import { digitalExperimentContent } from "@/data/digitalExperimentContent";

const EXPERIMENT_INTROS = {
  "digital-exp-1":
    "用 SSI/MSI 搭建组合逻辑：多数表决、1 位与 4 位全加器，并配合编码、译码与显示电路理解信号路径。",
  "digital-exp-2":
    "围绕译码器与数据选择器：用 74LS138、74LS151 等实现组合函数及简易数字显示报警等命题。",
  "digital-exp-3":
    "熟悉 D/JK 触发器逻辑功能，搭建异步/同步计数与广告灯等时序电路，并用示波器观察波形。",
  "digital-exp-4":
    "掌握 MSI 计数器级联与任意进制设计：74LS161、74LS90、74LS192 等应用与显示、波形验证。",
  "digital-exp-5":
    "移位寄存器 74LS194 与门电路构成环形、扭环形及移位型计数器，理解自启动与波形测量要点。",
  "digital-exp-6":
    "用计数器、数据选择器与移位寄存器设计计数型与移位型序列码发生器，完成定长序列输出。"
};

export default {
  name: "DigitalCircuitExperiments",
  data() {
    return {
      selectedMode: "deepseek",
      digitalDocs: [],
      customQuestion: ""
    };
  },
  mounted() {
    this.selectedMode = this.$route.query.mode || "deepseek";
    this.digitalDocs = DIGITAL_EXPERIMENT_ORDER.map((id) => ({
      id,
      title: digitalExperimentContent[id].title,
      intro: EXPERIMENT_INTROS[id] || ""
    }));
  },
  methods: {
    openDetail(id) {
      this.$router.push({
        path: `/digital-circuit-experiments/${id}`,
        query: { mode: this.selectedMode }
      });
    },
    openChat(prompt) {
      this.$router.push({
        path: "/chat",
        query: {
          topic: encodeURIComponent(prompt),
          mode: this.selectedMode
        }
      });
    },
    openAiLesson(experimentName, intro) {
      const ctx = intro ? `背景说明：${intro}` : "";
      this.openChat(
        `请针对数字电路实验「${experimentName}」做结构化讲解（先实验目的与仪器，再按实验任务及要求分步说明原理与操作要点）。${ctx} 请补充逻辑电平、共地与常见测量误区。`
      );
    },
    openPreset(prompt) {
      this.openChat(prompt);
    },
    askCustom() {
      this.openChat(`【数字电路实验模块】${this.customQuestion.trim()}`);
    }
  }
};
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

.resource-panel,
.ai-panel {
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

.card-actions {
  display: flex;
  gap: 10px;
  align-items: center;
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

@media (max-width: 1000px) {
  .module-layout {
    grid-template-columns: 1fr;
  }
}
</style>
