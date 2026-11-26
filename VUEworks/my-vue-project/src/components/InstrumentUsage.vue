<template>
  <div class="instrument-usage-page">
    <section class="module-header">
      <h2>仪器设备使用指南</h2>
      <p>支持按分类筛选；每个仪器卡片都提供图示区域，帮助你快速理解仪器外观与连接方式。</p>
    </section>

    <section class="toolbar">
      <select v-model="selectedCategory">
        <option value="全部">全部分类</option>
        <option v-for="c in categories" :key="c" :value="c">{{ c }}</option>
      </select>
      <input
        v-model.trim="keyword"
        type="text"
        placeholder="搜索仪器名称（如 示波器、频谱分析仪）"
      />
      <span class="count">共 {{ filteredInstruments.length }} 项</span>
    </section>

    <div class="card-list">
      <article v-for="item in filteredInstruments" :key="item.name" class="instrument-card">
        <div class="content">
          <div class="title-row">
            <h3>{{ item.name }}</h3>
            <span class="tag">{{ item.category }}</span>
          </div>
          <p class="scene"><strong>典型实验：</strong>{{ item.scene }}</p>
          <div class="actions">
            <button type="button" @click="askAIForInstrument(item.name, item.category)">AI 讲解</button>
          </div>
        </div>

        <div class="image-row">
          <div class="image-slot">
            <img
              v-if="item.realImageUrl"
              :src="item.realImageUrl"
              :alt="`${item.name} 实物图`"
              @error="item.realImageUrl = ''"
            />
            <div v-else class="image-placeholder">
              <span class="placeholder-title">仪器实物参考图</span>
              <span class="placeholder-path">{{ item.realImageHintPath }}</span>
            </div>
          </div>

          <div class="image-slot">
            <img
              v-if="item.schematicImageUrl"
              :src="item.schematicImageUrl"
              :alt="`${item.name} 原理图`"
              @error="item.schematicImageUrl = ''"
            />
            <div v-else class="image-placeholder">
              <span class="placeholder-title">连接示意参考图</span>
              <span class="placeholder-path">{{ item.schematicImageHintPath }}</span>
            </div>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<script>
export default {
  name: "InstrumentUsage",
  data() {
    return {
      selectedMode: "deepseek",
      selectedCategory: "全部",
      keyword: "",
      instruments: []
    };
  },
  computed: {
    normalizedInstruments() {
      return this.instruments.map((item, index) => {
        const code = String(index + 1).padStart(3, "0");
        return {
          name: item["名称"] || "未命名仪器",
          category: item["分类"] || "未分类",
          scene: item["典型实验"] || "暂无描述",
          realImageUrl:
            item["现实图像"] || item["实物图"] || item["图片"] || item["图片路径"] || "",
          schematicImageUrl:
            item["原理图像"] || item["电路原理图"] || item["原理图路径"] || "",
          realImageHintPath: `public/images/instruments/real/instrument-${code}.png`,
          schematicImageHintPath: `public/images/instruments/schematic/instrument-${code}.png`
        };
      });
    },
    categories() {
      return Array.from(new Set(this.normalizedInstruments.map((item) => item.category)));
    },
    filteredInstruments() {
      const key = this.keyword.toLowerCase();
      return this.normalizedInstruments.filter((item) => {
        const byCategory =
          this.selectedCategory === "全部" || item.category === this.selectedCategory;
        const byKeyword =
          !key ||
          item.name.toLowerCase().includes(key) ||
          item.category.toLowerCase().includes(key) ||
          item.scene.toLowerCase().includes(key);
        return byCategory && byKeyword;
      });
    }
  },
  mounted() {
    this.selectedMode = this.$route.query.mode || "deepseek";
    fetch("/labInstruments.json")
      .then(response => response.json())
      .then(data => {
        this.instruments = data;
      })
      .catch(error => console.error("读取仪器设备数据失败：", error));
  },
  methods: {
    askAIForInstrument(instrumentName, category) {
      const prompt = `请围绕实验仪器「${instrumentName}」（分类：${category}）进行讲解，包含：核心功能、接线与参数设置、易错点、常见故障排查步骤。`;
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
.instrument-usage-page {
  width: 90%;
  margin: 60px auto 0;
  max-height: calc(100vh - 130px);
  overflow-y: auto;
  padding-bottom: 24px;
}

.module-header,
.toolbar,
.card-list {
  background: var(--color-overlay-panel);
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 14px;
}

.module-header h2 {
  margin: 0 0 8px;
}

.module-header p {
  margin: 0;
  color: var(--color-text-secondary);
}

.toolbar {
  display: grid;
  grid-template-columns: 170px 1fr auto;
  gap: 10px;
  align-items: center;
}

.toolbar select,
.toolbar input {
  border: 1px solid var(--color-border-muted);
  border-radius: 6px;
  padding: 8px 10px;
}

.count {
  color: var(--color-text-secondary);
  font-size: 14px;
}

.card-list {
  display: grid;
  gap: 12px;
}

.instrument-card {
  display: grid;
  grid-template-columns: 1fr 420px;
  gap: 12px;
  border: 1px solid var(--color-border-light);
  border-radius: 8px;
  padding: 12px;
  background: var(--color-surface);
}

.image-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  align-content: start;
}

.image-slot {
  border: 1px dashed var(--color-border-dashed);
  border-radius: 8px;
  min-height: 135px;
  overflow: hidden;
  background: var(--color-primary-bg-soft);
}

.image-slot img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-placeholder {
  width: 100%;
  height: 100%;
  min-height: 135px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 8px;
  color: var(--color-primary-ink);
  text-align: center;
  padding: 8px;
}

.placeholder-title {
  font-weight: 600;
}

.placeholder-path {
  font-size: 12px;
  color: var(--color-text-secondary);
  word-break: break-all;
}

.title-row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}

.title-row h3 {
  margin: 0;
}

.tag {
  font-size: 12px;
  color: var(--color-primary-ink);
  background: var(--color-primary-bg-strong);
  border-radius: var(--radius-pill);
  padding: 3px 8px;
}

.scene {
  margin: 0;
  line-height: 1.65;
  color: var(--color-text-main);
}

.actions {
  margin-top: 10px;
}

button {
  border: none;
  border-radius: 6px;
  background-color: var(--color-primary-dark);
  color: var(--color-text-on-primary);
  padding: 8px 12px;
  cursor: pointer;
}

@media (max-width: 980px) {
  .toolbar {
    grid-template-columns: 1fr;
  }

  .instrument-card {
    grid-template-columns: 1fr;
  }

  .image-row {
    grid-template-columns: 1fr;
  }
}
</style>
