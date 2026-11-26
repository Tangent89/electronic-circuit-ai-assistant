<template>
  <header class="global-header">
    <!-- ←—— 左侧按钮区 ——→ -->
    <div class="left-buttons">
      <!-- 主页 -->
      <button class="nav-button home-button" type="button" @click="goHome">
        主页
      </button>
      <!-- 后退：仅非首页时显示 -->
      <button
        v-if="showBack"
        class="nav-button back-button"
        @click="$router.back()"
      >
        返回
      </button>
    </div>

    <!-- 中间标题 -->
    <h1>{{ computedTitle }}</h1>

    <!-- 右侧悬浮按钮区 -->
    <div class="floating-buttons">
      <router-link to="/feedback" class="nav-button feedback-button">
        留言反馈
      </router-link>
    </div>
  </header>
</template>

  
  <script>
  
  export default {
  name: "HeaderBar",
  props: {
    pageTitle: {
      type: String,
      default: "基于大语言模型的电子实验课程AI问答助手"
    }
  },
  computed: {
    computedTitle() { // 根据当前路由 meta.title显示标题；否则使用默认标题
      return this.$route.meta.title || this.pageTitle;
    },
    showBack() { // 根路径不显示“返回”按钮
      return this.$route.path !== "/";
    }
  },
  methods: {
    goHome() {
      const query = {};
      const mode = this.$route.query.mode;
      if (mode) query.mode = mode;

      if (this.$route.path === "/") {
        // 已在主页时，注入 homeReset 触发主页模块回到初始状态。
        query.homeReset = String(Date.now());
        this.$router.replace({ path: "/", query });
        return;
      }

      this.$router.push({ path: "/", query });
    }
  }
};
</script>
  
<style scoped>
.global-header {
/* 占据页面顶部 */
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 60px;
  z-index: 999;
  /* 半透明毛玻璃背景 */
  background-color: var(--color-header-bg);
  backdrop-filter: blur(10px);  /* 关键：实现毛玻璃效果 */
  /* 布局 */
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  column-gap: 12px;
  padding: 0 16px;
  box-sizing: border-box;
}

  /* 左侧按钮分组：与标题、右侧按钮三栏布局 */
.left-buttons {
  display: flex;
  gap: 10px;
  justify-self: start;
  align-items: center;
  min-width: 0;
}

/* 公共按钮基类 */
.nav-button {
  font-size: 16px;
  padding: 6px 12px;
  color: var(--color-text-on-primary);
  background: var(--color-nav-gray);
  border-radius: 6px;
  border: none;
  cursor: pointer;
  text-decoration: none;   /* 兼容 router-link 渲染出的 <a> 标签 */
  transition: background 0.3s;
}
.nav-button:hover {
  background: var(--color-nav-gray-hover);
}

/* 中间标题 */
.global-header h1 {
  margin: 0;
  text-align: center;
  font-size: clamp(16px, 2.2vw, 22px);
  font-weight: bold;
  color: var(--color-header-title);
  font-family: "Microsoft YaHei", sans-serif;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}

/* 右侧按钮区 */
.floating-buttons {
  display: flex;
  gap: 8px;
  justify-self: end;
  align-items: center;
  min-width: 0;
}

.nav-button {
  font-size: 14px;
  padding: 6px 10px;
}

@media (max-width: 760px) {
  .global-header {
    padding: 0 10px;
    column-gap: 8px;
  }
  .left-buttons {
    gap: 6px;
  }
  .nav-button {
    font-size: 13px;
    padding: 5px 8px;
  }
}
  </style>
  