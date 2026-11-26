<template>
  <div class="guide-page">
    <section class="hero-card">
      <h2>实验技能与故障排查实战手册</h2>
      <p>
        把实验台当成一个“会说话的现场”：每一次不亮、不稳、不通，都是电路在给你线索。
        按照“先外后内、先静后动、先电源后信号、先简单后复杂”去排查，问题会越来越清晰。
      </p>
      <div class="hero-actions">
        <button type="button" @click="askAI(generalPrompt)">AI 帮我梳理排查思路</button>
      </div>
    </section>

    <section class="panel">
      <h3>标准实验流程（六步走）</h3>
      <div class="flow-grid">
        <article v-for="step in flowSteps" :key="step.id" class="flow-card">
          <div class="step-badge">步骤 {{ step.id }}</div>
          <h4>{{ step.title }}</h4>
          <p>{{ step.desc }}</p>
        </article>
      </div>
    </section>

    <section class="panel">
      <h3>四类实验技能地图</h3>
      <div class="domain-grid">
        <article v-for="domain in domainCards" :key="domain.title" class="domain-card">
          <h4>{{ domain.title }}</h4>
          <p class="domain-scene">{{ domain.scene }}</p>
          <ul>
            <li v-for="point in domain.points" :key="point">{{ point }}</li>
          </ul>
          <button type="button" class="ghost-btn" @click="askAI(domain.prompt)">让 AI 讲这一块</button>
        </article>
      </div>
    </section>

    <section class="panel">
      <h3>故障排查四板斧</h3>
      <div class="method-grid">
        <article v-for="method in troubleshootingMethods" :key="method.name" class="method-card">
          <h4>{{ method.name }}</h4>
          <p>{{ method.desc }}</p>
          <p class="method-tip">现场口诀：{{ method.tip }}</p>
        </article>
      </div>
    </section>

    <section class="panel">
      <h3>典型案例（像侦探一样定位问题）</h3>
      <div class="case-list">
        <article v-for="item in cases" :key="item.title" class="case-card">
          <h4>{{ item.title }}</h4>
          <p><strong>现象：</strong>{{ item.symptom }}</p>
          <p><strong>排查：</strong>{{ item.trace }}</p>
          <p><strong>结论：</strong>{{ item.result }}</p>
        </article>
      </div>
    </section>

    <section class="panel safety-panel">
      <h3>安全红线（先保人，再保设备）</h3>
      <ul>
        <li>接线、拆线、更换芯片前必须断电，禁止带电插拔。</li>
        <li>先确认电源极性与电压等级，特别是运放和数字芯片。</li>
        <li>示波器、频谱仪等仪器先看输入上限，必要时加衰减器。</li>
        <li>射频与 CMOS 器件注意静电防护，操作前先放电。</li>
      </ul>
    </section>
  </div>
</template>

<script>
export default {
  name: "TroubleshootingGuide",
  data() {
    return {
      selectedMode: "deepseek",
      generalPrompt:
        "请用“现象-原因-定位-修复”的结构，给我一个电子实验通用故障排查流程，适用于电路、模电、数电和射频实验。",
      flowSteps: [
        { id: 1, title: "预习与预判", desc: "看懂目的、原理和步骤，先估算结果，心里有“正常值范围”。" },
        { id: 2, title: "器件与仪器准备", desc: "清点元件、连线与仪器状态，避免一上电就被低级错误绊住。" },
        { id: 3, title: "断电接线与复核", desc: "先主后辅、先地后信号、先低后高，接完逐点核对极性与走线。" },
        { id: 4, title: "分级通电测试", desc: "先开仪器后开主电源，盯住发热、异味、波形异常等第一现场。" },
        { id: 5, title: "系统化排障", desc: "按流程收窄范围，不猜、不赌，定位到“哪一级、哪个点、哪只件”。" },
        { id: 6, title: "记录与复盘", desc: "把故障现象、原因、修复动作和结论写进报告，形成个人故障库。" }
      ],
      domainCards: [
        {
          title: "电路实验（基础）",
          scene: "像量体温：先看电源，再看电压电流是否在“正常区间”。",
          points: [
            "掌握电阻/电容/电感/二极管识别与测量",
            "会测 KVL/KCL、戴维南等效与最大功率传输",
            "谐振与相位测量关注频率、Q 值、带宽"
          ],
          prompt:
            "请用大一学生能懂的方式讲解基础电路实验中最常见的 5 类故障及排查顺序。"
        },
        {
          title: "模拟电路实验",
          scene: "像调相机焦距：先把静态工作点调清楚，再谈放大和失真。",
          points: [
            "先测静态工作点，再测增益、带宽、失真",
            "重点关注饱和失真、截止失真、自激振荡",
            "做好去耦、接地和反馈极性核查"
          ],
          prompt:
            "请按“静态工作点→动态波形→反馈稳定性”给出模拟电路排障清单。"
        },
        {
          title: "数字电路实验",
          scene: "像红绿灯系统：电平、时钟、复位三件事，错一件全乱。",
          points: [
            "确认芯片供电、方向与逻辑电平兼容",
            "输入不悬空，输出不冲突，时钟边沿要干净",
            "计数乱跳先查毛刺、复位和时钟源"
          ],
          prompt:
            "请给出数字电路实验中“能上电但逻辑不对”的高效排查路径。"
        },
        {
          title: "射频电路实验",
          scene: "像调音台：不只看有没有声，还要看功率、匹配和杂散。",
          points: [
            "围绕 50Ω 系统做连接、匹配与校准",
            "会看 S11/S21、驻波比和频谱纯净度",
            "先做最小系统，再逐级注入定位损耗点"
          ],
          prompt:
            "请结合 VNA 与频谱仪，讲一套射频实验“无信号/低增益”的排查流程。"
        }
      ],
      troubleshootingMethods: [
        {
          name: "直观检查法",
          desc: "先看、闻、摸：松线、错线、虚焊、烧焦、过热，常常一眼就能抓住。",
          tip: "先找明显异常，再做精细测量。"
        },
        {
          name: "静态+动态测量法",
          desc: "断电查通断和阻值，通电查电压、电流、波形，双线并行最稳。",
          tip: "静态定位结构错，动态定位工作错。"
        },
        {
          name: "信号寻迹法",
          desc: "标准信号从输入灌进去，逐级看哪里开始变形、衰减或消失。",
          tip: "坏在哪一级，就停在哪一级。"
        },
        {
          name: "分割与替换法",
          desc: "把系统切段、逐段验证；可疑器件用良品替换，快速验证假设。",
          tip: "小范围试错，少走弯路。"
        }
      ],
      cases: [
        {
          title: "案例 1：函数发生器有输出，计数器却不计数",
          symptom: "示波器看着有方波，数码管就是不动。",
          trace: "先查时钟幅度与边沿，再查负载设置和逻辑电平，最后换信号源交叉验证。",
          result: "定位到信号源输出异常（幅度不足/上升沿过慢），更换后恢复。"
        },
        {
          title: "案例 2：共射放大器增益低且波形削顶",
          symptom: "有输出但放大不明显，输入稍大就失真。",
          trace: "先测静态工作点，再查偏置网络与旁路电容，最后按目标 UCE 重新调点。",
          result: "静态点偏移叠加旁路问题，修正后增益与失真同时改善。"
        },
        {
          title: "案例 3：射频链路“有连接”但功率掉很多",
          symptom: "频谱仪看得到信号，但功率比预期低十几 dB。",
          trace: "最小系统直连标定，再逐级插入模块，结合 S 参数看反射和插损。",
          result: "发现匹配偏移和连接器问题，修复后链路恢复。"
        }
      ]
    };
  },
  mounted() {
    this.selectedMode = this.$route.query.mode || "deepseek";
  },
  methods: {
    askAI(prompt) {
      this.$router.push({
        path: "/chat",
        query: {
          topic: encodeURIComponent(`【实验技能与故障排查】${prompt}`),
          mode: this.selectedMode
        }
      });
    }
  }
};
</script>

<style scoped>
.guide-page {
  width: 90%;
  margin: 60px auto 0;
  max-height: calc(100vh - 130px);
  overflow-y: auto;
  padding-bottom: 22px;
}

.hero-card,
.panel {
  background: var(--color-overlay-card);
  border-radius: 10px;
  padding: 16px 18px;
  margin-bottom: 14px;
}

.hero-card h2 {
  margin: 0 0 10px;
}

.hero-card p {
  margin: 0;
  line-height: 1.75;
  color: var(--color-text-main);
}

.hero-actions {
  margin-top: 12px;
}

.panel h3 {
  margin: 0 0 12px;
}

.flow-grid,
.domain-grid,
.method-grid {
  display: grid;
  gap: 10px;
}

.flow-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.domain-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.method-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.flow-card,
.domain-card,
.method-card,
.case-card {
  border: 1px solid var(--color-border-soft);
  border-radius: 8px;
  padding: 12px;
  background: var(--color-surface);
}

.step-badge {
  display: inline-block;
  font-size: 12px;
  color: var(--color-primary-dark);
  background: var(--color-primary-bg-strong);
  padding: 2px 8px;
  border-radius: var(--radius-pill);
  margin-bottom: 6px;
}

.flow-card h4,
.domain-card h4,
.method-card h4,
.case-card h4 {
  margin: 0 0 6px;
}

.flow-card p,
.domain-card p,
.method-card p,
.case-card p {
  margin: 0;
  color: var(--color-text-main);
  line-height: 1.65;
}

.domain-scene {
  margin-bottom: 8px !important;
  color: var(--color-primary-ink) !important;
}

.domain-card ul {
  margin: 0 0 10px;
  padding-left: 18px;
  color: var(--color-text-main);
}

.domain-card li {
  margin: 4px 0;
  line-height: 1.55;
}

.method-tip {
  margin-top: 8px !important;
  color: var(--color-primary-ink) !important;
}

.case-list {
  display: grid;
  gap: 10px;
}

.case-card p {
  margin-top: 6px;
}

.safety-panel ul {
  margin: 0;
  padding-left: 18px;
}

.safety-panel li {
  margin: 6px 0;
  line-height: 1.6;
}

button {
  border: none;
  border-radius: 6px;
  background-color: var(--color-primary-dark);
  color: var(--color-text-on-primary);
  padding: 8px 12px;
  cursor: pointer;
}

.ghost-btn {
  background: var(--color-primary-bg-soft);
  color: var(--color-primary-ink);
  border: 1px solid var(--color-border-accent-soft);
}

.ghost-btn:hover {
  background: var(--color-primary-bg-strong);
}

@media (max-width: 1000px) {
  .flow-grid,
  .domain-grid,
  .method-grid {
    grid-template-columns: 1fr;
  }
}
</style>
