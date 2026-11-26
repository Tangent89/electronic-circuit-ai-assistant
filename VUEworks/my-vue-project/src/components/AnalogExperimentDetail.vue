<template>
  <div class="detail-page">
    <div v-if="doc" class="detail-card">
      <h2>{{ doc.title }}</h2>

      <section class="block">
        <h3>实验目的</h3>
        <p v-for="(line, idx) in doc.purpose" :key="'p' + idx" class="verbatim">{{ line }}</p>
      </section>

      <section class="block">
        <h3>实验所用仪器设备</h3>
        <p v-for="(line, idx) in doc.equipment" :key="'e' + idx" class="verbatim">{{ line }}</p>
      </section>

      <section class="block">
        <h3>实验内容及要求</h3>
        <p v-for="(line, idx) in doc.content_requirements" :key="'c' + idx" class="verbatim">{{ line }}</p>
      </section>

      <div class="actions">
        <button type="button" @click="askAi">AI 辅助讲解本实验</button>
      </div>
    </div>
    <div v-else class="detail-card">
      <p>未找到该实验内容。</p>
    </div>
  </div>
</template>

<script>
import { analogExperimentContent } from "@/data/analogExperimentContent";

export default {
  name: "AnalogExperimentDetail",
  computed: {
    doc() {
      const id = this.$route.params.id;
      return analogExperimentContent[id] || null;
    },
    selectedMode() {
      return this.$route.query.mode || "deepseek";
    }
  },
  methods: {
    askAi() {
      if (!this.doc) return;
      const prompt = `请针对模拟电路实验「${this.doc.title}」讲解：先概括实验目的，再说明所列仪器各自用途，最后按「实验内容及要求」逐条解释原理、接线与测量要点；并说明示波器/电源共地与常见操作误区。`;
      this.$router.push({
        path: "/chat",
        query: {
          topic: encodeURIComponent(prompt),
          mode: this.selectedMode
        }
      });
    }
  }
};
</script>

<style scoped>
.detail-page {
  width: 90%;
  margin: 60px auto 0;
  max-height: calc(100vh - 130px);
  overflow-y: auto;
  padding-bottom: 24px;
}

.detail-card {
  background: var(--color-overlay-card);
  border-radius: 10px;
  padding: 18px;
}

.detail-card h2 {
  margin-top: 0;
}

.block {
  margin-bottom: 22px;
}

.block h3 {
  margin: 0 0 10px;
  font-size: 18px;
  color: var(--color-text-main);
}

.verbatim {
  margin: 0 0 8px;
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--color-text-main);
  font-size: 15px;
}

.actions {
  margin-top: 16px;
}

button {
  border: none;
  border-radius: 6px;
  background-color: var(--color-primary-dark);
  color: var(--color-text-on-primary);
  padding: 8px 12px;
  cursor: pointer;
}
</style>
