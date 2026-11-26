<template>
  <div class="basic-components-page">
    <section class="module-header">
      <h2>基础元器件知识库</h2>
      <p>每张卡片都配有图示区域，方便你查看元器件实物外观与电路示意。</p>
    </section>

    <section class="toolbar">
      <input
        v-model.trim="keyword"
        type="text"
        placeholder="搜索元器件名称（如 电阻、运放、MOSFET）"
      />
      <span class="count">共 {{ filteredComponents.length }} 项</span>
    </section>

    <div class="card-list">
      <article v-for="item in filteredComponents" :key="item.name" class="component-card">
        <div class="content">
          <h3>{{ item.name }}</h3>
          <p class="desc">{{ item.desc }}</p>
          <p class="example"><strong>典型示例：</strong>{{ item.example }}</p>
          <div class="actions">
            <button type="button" @click="askAIForComponent(item.name)">AI 讲解</button>
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
              <span class="placeholder-title">元器件实物参考图</span>
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
              <span class="placeholder-title">电路原理参考图</span>
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
  name: "BasicComponents",
  data() {
    return {
      selectedMode: "deepseek",
      keyword: "",
      components: []
    };
  },
  computed: {
    normalizedComponents() {
      return this.components.map((item, index) => {
        const code = String(index + 1).padStart(3, "0");
        const name = item["关键字"] || "未命名元器件";
        const realImageUrl =
          item["现实图像"] || item["实物图"] || item["图片"] || item["图片路径"] || "";
        const schematicImageUrl =
          item["原理图像"] || item["电路原理图"] || item["原理图路径"] || "";
        return {
          name,
          desc: item["说明"] || "暂无说明。",
          example: item["使用示例"] || "暂无示例。",
          realImageUrl,
          schematicImageUrl,
          realImageHintPath: `public/images/components/real/component-${code}.png`,
          schematicImageHintPath: `public/images/components/schematic/component-${code}.png`
        };
      });
    },
    filteredComponents() {
      const key = this.keyword.toLowerCase();
      if (!key) return this.normalizedComponents;
      return this.normalizedComponents.filter(
        (item) =>
          item.name.toLowerCase().includes(key) ||
          item.desc.toLowerCase().includes(key) ||
          item.example.toLowerCase().includes(key)
      );
    }
  },
  mounted() {
    this.selectedMode = this.$route.query.mode || "deepseek";
    fetch("/electronicComponents.json")
      .then(response => response.json())
      .then(data => {
        this.components = data;
      })
      .catch(error => console.error("读取基础元器件数据失败：", error));
  },
  methods: {
    askAIForComponent(componentName) {
      const prompt = `请用“工作原理-关键参数-实验接线注意-常见故障”四部分讲解元器件「${componentName}」，并给一个实验场景示例。`;
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
.basic-components-page {
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
  display: flex;
  gap: 10px;
  align-items: center;
}

.toolbar input {
  flex: 1;
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

.component-card {
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

.content h3 {
  margin: 0 0 8px;
}

.desc,
.example {
  margin: 0 0 8px;
  line-height: 1.65;
  color: var(--color-text-main);
}

.actions {
  margin-top: 6px;
}

button {
  border: none;
  border-radius: 6px;
  background-color: var(--color-primary-dark);
  color: var(--color-text-on-primary);
  padding: 8px 12px;
  cursor: pointer;
}

@media (max-width: 900px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .component-card {
    grid-template-columns: 1fr;
  }

  .image-row {
    grid-template-columns: 1fr;
  }
}
</style>
