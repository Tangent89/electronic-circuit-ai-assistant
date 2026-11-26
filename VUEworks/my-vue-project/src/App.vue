<template>
  <div id="app">
    <HeaderBar :pageTitle="globalTitle" />
    <!-- 背景层 -->
    <div class="background">
      <div class="square">
        <ul>
          <li></li>
          <li></li>
          <li></li>
          <li></li>
          <li></li>
        </ul>
      </div>
      <div class="circle">
        <ul>
          <li></li>
          <li></li>
          <li></li>
          <li></li>
          <li></li>
        </ul>
      </div>
    </div>
    <!-- 应用主体（路由视图） -->
    <router-view></router-view>
  </div>
</template>

<script>
import HeaderBar from "@/components/HeaderBar.vue";

export default {
  name: "App",
  components: {
    HeaderBar
},

data() {
    return {
      globalTitle: "基于大语言模型的电子线路实验课程AI问答助手"
    }
  }
}
</script>

<!-- 注意这里不要添加 scoped 属性，以便全局背景样式起作用 -->
<style>
#app {
  padding-top: 6px; /* 与标题栏的高度相同 */
}
/* 背景容器覆盖整个页面 */
.background {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100vh;
  z-index: -1; /* 确保背景在所有内容后面 */
  overflow: hidden;
  /* 如果你需要渐变背景，可以使用下面这一行，或者换成其他背景 */
  background: linear-gradient(200deg, var(--color-primary), var(--color-primary-light));
}

/* 动画背景结构 */
.square,
.circle {
  display:none; /*直接用 display:none 隐藏*/
  position: absolute;
  width: 100%;
  height: 100%;
}

.square ul,
.circle ul {
  list-style: none;
  margin: 0;
  padding: 0;
}

.square li,
.circle li {
  position: absolute;
  border: 1px solid var(--color-surface);
  background-color: var(--color-surface);
  width: 30px;
  height: 30px;
  opacity: 0;
}

/* square 动画效果 */
.square li {
  top: 40vh;
  left: 60vw;
  animation: square 10s linear infinite;
}
.square li:nth-child(2) {
  top: 80vh;
  left: 10vw;
  animation-delay: 2s;
}
.square li:nth-child(3) {
  top: 80vh;
  left: 85vw;
  animation-delay: 4s;
}
.square li:nth-child(4) {
  top: 10vh;
  left: 70vw;
  animation-delay: 6s;
}
.square li:nth-child(5) {
  top: 10vh;
  left: 10vw;
  animation-delay: 8s;
}

/* circle 动画效果 */
.circle li {
  bottom: 0;
  left: 15vw;
  animation: circle 10s linear infinite;
}
.circle li:nth-child(2) {
  left: 35vw;
  animation-delay: 2s;
}
.circle li:nth-child(3) {
  left: 55vw;
  animation-delay: 6s;
}
.circle li:nth-child(4) {
  left: 75vw;
  animation-delay: 4s;
}
.circle li:nth-child(5) {
  left: 90vw;
  animation-delay: 8s;
}

/* 动画关键帧 */
@keyframes square {
  0% {
    transform: scale(0) rotateY(0deg);
    opacity: 1;
  }
  100% {
    transform: scale(5) rotateY(1000deg);
    opacity: 0;
  }
}

@keyframes circle {
  0% {
    transform: scale(0) rotateY(0deg);
    opacity: 1;
    bottom: 0;
    border-radius: 0;
  }
  100% {
    transform: scale(5) rotateY(1000deg);
    opacity: 0;
    bottom: 90vh;
    border-radius: 50%;
  }
}
</style>
