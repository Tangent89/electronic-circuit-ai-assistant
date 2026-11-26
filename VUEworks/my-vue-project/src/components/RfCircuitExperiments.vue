<template>
  <div class="module-page">
    <section class="module-header">
      <h2>射频电路实验学习中心</h2>
      <p>
        先在下表中选择实验，进入详情页阅读「实验目的、仪器设备、实验内容与步骤」；
        需要加深理解时，再使用右侧 AI 辅助答疑或针对某一实验发起讲解。
      </p>
    </section>

    <section class="module-layout">
      <div class="resource-panel">
        <h3>实验列表（共 5 项）</h3>
        <article v-for="doc in rfDocs" :key="doc.id" class="resource-card">
          <h4>{{ doc.title }}</h4>
          <p class="card-hint">{{ doc.intro }}</p>
          <div class="card-actions">
            <button type="button" @click="openAiLesson(doc.title, doc.intro)">AI 辅助讲解</button>
            <button type="button" @click="openDetail(doc.id)">查看实验详情</button>
          </div>
        </article>
      </div>

      <aside class="ai-panel">
        <h3>AI 辅助（射频电路）</h3>
        <p class="ai-tip">与上方实验列表配合使用：可先做通用问答，也可进入某一实验后再点「AI 辅助讲解」获得针对性说明。</p>
        <button type="button" @click="openPreset('请按「链路功能—关键频点与指标—测试连接—常见失配与排错」的顺序，概括一次典型射频实验的学习路径。')">学习路径说明</button>
        <button type="button" @click="openPreset('请出 3 道射频电路实验相关选择题（含答案与简要解析），侧重调制解调或振荡器基础。')">自测小题</button>
        <button type="button" @click="openPreset('请列出射频实验中常见的失配、频偏、谐波和噪声问题，并给出排查顺序。')">测量与排错要点</button>
        <textarea v-model="customQuestion" placeholder="补充提问（可与当前实验或通用概念相关）"></textarea>
        <button type="button" :disabled="!customQuestion.trim()" @click="askCustom">发送提问</button>
      </aside>
    </section>
  </div>
</template>

<script>
import { RF_EXPERIMENT_ORDER } from "@/data/rfExperimentDetails";
import { rfExperimentContent } from "@/data/rfExperimentContent";

const EXPERIMENT_INTROS = {
  "rf-exp-1":
    "围绕高频小信号调谐放大器，完成谐振频率、增益、带宽与品质因数等关键指标测试。",
  "rf-exp-2":
    "以西勒与晶体振荡器为主线，比较不同选频条件下的振荡频率与稳定度特性。",
  "rf-exp-3":
    "使用 MC1496 进行调幅、平衡调制与倍频实验，理解乘法器在调制解调中的作用。",
  "rf-exp-4":
    "完成变容二极管调频与正交鉴频设计，联调调频-鉴频链路并观察解调效果。",
  "rf-exp-5":
    "基于系统级发射接收链路，完成参数配置、链路调试与双机文字通信验证。"
};

export default {
  name: "RfCircuitExperiments",
  data() {
    return {
      selectedMode: "deepseek",
      rfDocs: [],
      customQuestion: ""
    };
  },
  mounted() {
    this.selectedMode = this.$route.query.mode || "deepseek";
    this.rfDocs = RF_EXPERIMENT_ORDER.map((id) => ({
      id,
      title: rfExperimentContent[id].title,
      intro: EXPERIMENT_INTROS[id] || ""
    }));
  },
  methods: {
    openDetail(id) {
      this.$router.push({
        path: `/rf-circuit-experiments/${id}`,
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
        `请针对射频电路实验「${experimentName}」做结构化讲解（先实验目的与仪器，再按实验内容与步骤分步说明原理与测试要点）。${ctx} 请补充频偏、失配、谐波与噪声的排查思路。`
      );
    },
    openPreset(prompt) {
      this.openChat(prompt);
    },
    askCustom() {
      this.openChat(`【射频电路实验模块】${this.customQuestion.trim()}`);
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
