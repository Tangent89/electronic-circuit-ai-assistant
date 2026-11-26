<template>
  <div class="agent-selector-container">
  <!-- 标题栏 -->
    <div class="agent-selector">
      <h1 v-if="!showSubButtons">请选择智能体模块</h1>
      <h1 v-else>资料查阅模块</h1>
      <p v-if="!showSubButtons" class="main-subtitle">当前模型：{{ modeDescription }}</p>
      <p v-if="showSubButtons" class="submodule-hint">请选择一个实验子模块进入学习。</p>
      <button
        v-if="showSubButtons"
        class="back-button"
        @click="backToMain"
      >返回</button>

      <div class="button-group">
        <template v-if="!showSubButtons">
          <!-- 三个按钮均使用 main-button 类，并且结构统一：图标 + 文本 -->
          <button
            class="main-button"
            :class="{'waterdrop-animation': clickedAgent === 'datasearch'}"
          @animationend="onAnimationEnd('datasearch')"
          @click="handleClick('datasearch')"
          >
            <img src="@/assets/datasearch.png" alt="资料查阅图标" class="button-icon" />
            <span class="button-text">资料查阅</span>
          </button>
          <button
            class="main-button"
            :class="{'waterdrop-animation': clickedAgent === 'questions'}"
          @animationend="onAnimationEnd('questions')"
          @click="handleClick('questions')"
          >
            <img src="@/assets/questionviewer.png" alt="试题练习图标" class="button-icon" />
            <span class="button-text">试题练习</span>
          </button>
          <button
            class="main-button"
            :class="{'waterdrop-animation': clickedAgent === 'chat'}"
          @animationend="onAnimationEnd('chat')"
          @click="handleClick('chat')"
          >
            <img src="@/assets/chatinterface.png" alt="自由问答图标" class="button-icon" />
            <span class="button-text">自由问答</span>
          </button>
        </template>

        <!-- 资料查阅二级模块 -->
        <template v-else>
          <div class="submodule-grid">
            <button
              v-for="item in dataSearchModules"
              :key="item.path"
              class="sub-button"
              @click="goToAgent(item.path)"
            >
              <div class="sub-button-text">
                <span class="sub-title">{{ item.title }}</span>
                <span class="sub-desc">{{ item.desc }}</span>
              </div>
              <img
                class="sub-button-thumb"
                :src="item.imageSrc"
                :alt="`${item.title}配图（占位）`"
              />
            </button>
          </div>
        </template>
      </div>

      <!-- 模型选择开关区域 -->
      <div class="mode-switch-container">
        <div class="tri-buttons">
          <button 
            :class="{'active': mode === 'deepseek'}" 
            @click="switchMode('deepseek')">
            DeepSeek
          </button>
          <button 
            :class="{'active': mode === 'local'}" 
            @click="switchMode('local')">
            DeepSeek本地
          </button>
          <button 
            :class="{'active': mode === 'tencent'}" 
            @click="switchMode('tencent')">
            腾讯混元
          </button>
          <button
            :class="{ active: mode === 'zhipu' }"
            @click="switchMode('zhipu')">
            智谱GLM
          </button>
          <button
            :class="{ active: mode === 'qwen' }"
            @click="switchMode('qwen')">
            通义千问
          </button>
        </div>
        <div class="mode-switch-hint">大语言模型切换</div>
      </div>
    </div>
  </div>
</template>

<script>
// 六个子模块配图：文件名与路由 path 语义一致，位于 src/assets/images/
import imgBasicComponents from "@/assets/images/basic-components.svg";
import imgInstrumentUsage from "@/assets/images/instrument-usage.svg";
import imgAnalogCircuit from "@/assets/images/analog-circuit-experiments.svg";
import imgDigitalCircuit from "@/assets/images/digital-circuit-experiments.svg";
import imgRfCircuit from "@/assets/images/rf-circuit-experiments.svg";
import imgTroubleshooting from "@/assets/images/troubleshooting-guide.svg";

export default {
  name: 'AgentSelector',
  data() {
    return {
      mode: "deepseek",         // false 表示本地部署；true 表示 API 模型
      clickedAgent: '',        // 记录哪个按钮被点击
      showSubButtons: false,
      // 配图目录：src/assets/images/（*.svg；若为 PNG/JPG 请改扩展名并同步上方 import）
      dataSearchModules: [
        { path: "basic-components", title: "基础元器件", desc: "器件识别、参数理解与应用场景速查。", imageSrc: imgBasicComponents },
        { path: "instrument-usage", title: "仪器设备使用", desc: "示波器、电源、信号源等常用仪器操作要点。", imageSrc: imgInstrumentUsage },
        { path: "analog-circuit-experiments", title: "模拟电路实验", desc: "按实验单元查看目的、仪器与步骤要求。", imageSrc: imgAnalogCircuit },
        { path: "digital-circuit-experiments", title: "数字电路实验", desc: "覆盖组合逻辑、时序逻辑等核心实验内容。", imageSrc: imgDigitalCircuit },
        { path: "rf-circuit-experiments", title: "射频电路实验", desc: "聚焦调制解调、振荡与链路调试实验。", imageSrc: imgRfCircuit },
        { path: "troubleshooting-guide", title: "实验技能与故障排查", desc: "提供常见错误定位思路与处理流程。", imageSrc: imgTroubleshooting }
      ]
    }
  },
  watch: {
    "$route.query.mode": {
      immediate: true,
      handler(newMode) {
        const allowedModes = ["deepseek", "local", "tencent", "zhipu", "qwen"];
        if (typeof newMode === "string" && allowedModes.includes(newMode)) {
          this.mode = newMode;
        }
      }
    },
    "$route.query.homeReset"() {
      this.resetHomeView();
    }
  },
  computed: {
    // 根据当前模式返回不同文案
    modeDescription() {
      switch (this.mode) {
        case 'deepseek': return 'DeepSeek API';
        case 'local':    return 'Local 模型';
        case 'tencent':  return 'Tencent API';
        case 'zhipu':    return '智谱 API';
        case 'qwen':     return '通义千问 API';
        default: return ''; 
      }
    }
  },
  methods: {
    resetHomeView() {
      this.showSubButtons = false;
      this.clickedAgent = "";
    },
    switchMode(newMode) {
      this.mode = newMode;
    },
    backToMain() {
      this.showSubButtons = false;
    },
    handleClick(agent) {
      this.clickedAgent = agent;
    },
    onAnimationEnd(agent) {
      if (this.clickedAgent === agent) {
        if (agent === 'datasearch') {
          // 点击资料查阅后，显示六个子模块（即切换显示逻辑）
          this.showSubButtons = true;
        } else {
          // 对于其他按钮，直接跳转并传递mode参数
          this.$router.push({ path: '/' + agent, query: { mode: this.mode } });
        }
        this.clickedAgent = '';
      }
    },
    goToAgent(agent) {
      this.$router.push({ 
        path: '/' + agent, 
        query: { mode: this.mode }
      });
    },
  }
}
</script>

<style scoped>

.agent-selector-container {
  width: 100%;
  margin: 0 auto;
  padding: 76px 20px 34px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 10px);
  background-size: cover;
  position: relative;
}
.agent-selector-container::before {
  content: "";
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(180deg, var(--color-overlay-mask-50), var(--color-overlay-mask-25));
  z-index: 1;
}

.agent-selector {
  position: relative;
  z-index: 2;
  max-width: 940px;
  width: 100%;
  margin: 0 auto;
  padding: 56px 42px 34px;
  border-radius: 20px;
  background: linear-gradient(170deg, var(--color-overlay-lighter), var(--color-overlay-panel));
  border: 1px solid var(--color-overlay-light);
  box-shadow: var(--shadow-hero);
  backdrop-filter: blur(6px);
  text-align: center;
}
.agent-selector h1 {
  margin: 0;
  font-size: 34px;
  letter-spacing: 0.4px;
  color: var(--color-text-main);
}

.main-subtitle {
  margin: 12px 0 24px;
  color: var(--color-text-muted);
  font-size: 15px;
  letter-spacing: 0.2px;
}

.submodule-hint {
  margin: 10px 0 22px;
  color: var(--color-text-muted);
  font-size: 15px;
}

.button-group {
  width: 100%;
  display: flex;
  flex-direction: row;
  justify-content: center;
  gap: 18px;
}

/* 统一的主按钮样式 */
.main-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 168px;
  height: 154px;
  padding: 16px 12px 12px;
  border: none;
  border-radius: 14px;
  background: linear-gradient(160deg, var(--color-primary), var(--color-primary-dark));
  box-shadow: var(--shadow-primary);
  cursor: pointer;
  transition: transform 0.22s ease, box-shadow 0.22s ease, filter 0.22s ease;
}
.main-button:hover {
  transform: translateY(-4px) scale(1.01);
  box-shadow: var(--shadow-primary-strong);
  filter: brightness(1.03);
}

/* 图标大小 */
.button-icon {
  width: 86px;
  height: 86px;
  margin-bottom: 10px;
}
/* 文字样式 */
.button-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-on-primary);
  white-space: nowrap;
}

/* 水滴动画按钮 */
.main-button.waterdrop-animation {
  animation: waterdrop 0.4s ease forwards;
}
@keyframes waterdrop {
  0%   { transform: scale(1); }
  50%  { transform: scale(0.8); }
  100% { transform: scale(1); }
}

/* 子按钮动画 */
.sub-button {
  animation: appear 0.5s ease forwards;
  opacity: 0;
  transform: scale(0);
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  text-align: left;
  width: 100%;
  min-height: 112px;
  padding: 14px 14px 14px 16px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(145deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  box-shadow: var(--shadow-primary-md);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  color: var(--color-text-on-primary);
  font-size: 15px;
  white-space: normal;
}

.sub-button-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
}

.sub-button-thumb {
  width: 72px;
  height: 72px;
  flex-shrink: 0;
  object-fit: cover;
  border-radius: 10px;
  background: var(--color-surface-soft);
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* 悬停时的缩放和阴影效果 */
.sub-button:hover {
  transform: translateY(-3px) scale(1.01);
  box-shadow: var(--shadow-primary-lg);
}
@keyframes appear {
  0%   { transform: scale(0);   opacity: 0; }
  60%  { transform: scale(1.1); opacity: 1; }
  100% { transform: scale(1);   opacity: 1; }
}

.submodule-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.sub-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 9px;
}

.sub-desc {
  font-size: 14px;
  opacity: 0.94;
  line-height: 1.55;
}
/* 左上角返回按钮 */
.back-button {
  display: inline-block;
  text-decoration: none;
  font-size: 14px;
  color: var(--color-text-on-primary);
  padding: 6px 12px;
  background-color: var(--color-nav-gray-hover);
  border-radius: 6px;
  transition: background-color 0.3s;
  cursor: pointer;
  position: absolute;
  right: 22px;
  top: 18px;
}
.back-button:hover {
  background-color: var(--color-nav-gray);
}




/* -----------------------------
   模型选择开关部分
------------------------------ */
.mode-switch-container {
  margin-top: 32px;
  display: flex;
  flex-direction: column;  /* 垂直排列 */
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding-top: 18px;
  border-top: 1px dashed var(--color-border-strong);
}

/* 下方提示文本 */
.mode-switch-hint {
  margin-top: 8px;
  font-size: 14px;
  color: var(--color-text-secondary);
  text-align: center;
}

/* 四档开关整体容器，继承原来 .switch 样式 */
.tri-switch {
  position: relative;
  display: inline-block;
  width: 210px; 
  height: 60px; 
  border-radius: 60px;
  cursor: pointer;
  transition: background-color 0.4s;
}

/* 你可以根据选中的模式设置背景色，如果需要也可以用 .deepseek-mode、.local-mode、.tencent-mode 类来动态设置背景 */
.tri-switch.deepseek {
  background-color: var(--color-primary-dark); /* 例如 DeepSeek */
}
.tri-switch.local {
  background-color: var(--color-success);
}
.tri-switch.tencent {
  background-color: var(--color-warning);  /* 或其他颜色 */
}

/* 滑块轨道，保持原样 */
.slider {
  position: absolute;
  top: 0; 
  left: 0; 
  bottom: 0; 
  right: 0;
  border-radius: 60px;
  pointer-events: none;
}

/* mode-icon 样式 */
.mode-icon {
  position: absolute;
  width: 50px;
  height: 50px;
  top: 5px;
  left: 5px; /* 这个初始位置会被 inline style 覆盖 */
  border-radius: 50%;
  background-color: var(--color-text-main);
  transition: transform 0.4s;
  /* 保持原来背景图等可以根据需要设置 */
}

/* mode-text 样式 */
.mode-text {
  position: absolute;
  top: 50%;
  left: 65px;
  transform: translateY(-50%);
  color: var(--color-text-on-primary);
  font-size: 18px;
  font-weight: 600;
  white-space: nowrap;
}

/* 四档按钮组 */
.tri-buttons {
  margin-top: 4px;
  display: inline-flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
}

.tri-buttons button {
  padding: 8px 14px;
  font-size: 15px;
  border: 1px solid var(--color-border-soft);
  border-radius: var(--radius-pill);
  background-color: var(--color-surface-soft);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.25s ease;
}

.tri-buttons button.active,
.tri-buttons button:hover {
  background-color: var(--color-primary-dark);
  color: var(--color-text-on-primary);
  border-color: var(--color-primary-dark);
  box-shadow: var(--shadow-primary-soft);
}

@media (max-width: 980px) {
  .agent-selector-container {
    padding-top: 70px;
  }

  .agent-selector {
    padding: 46px 20px 28px;
    border-radius: 16px;
  }

  .agent-selector h1 {
    font-size: 28px;
  }

  .main-subtitle {
    margin-bottom: 18px;
  }

  .button-group {
    gap: 10px;
    flex-wrap: wrap;
  }

  .main-button {
    width: 140px;
    height: 130px;
  }

  .button-icon {
    width: 70px;
    height: 70px;
  }

  .button-text {
    font-size: 15px;
  }

  .submodule-grid {
    grid-template-columns: 1fr;
  }
}

</style>
