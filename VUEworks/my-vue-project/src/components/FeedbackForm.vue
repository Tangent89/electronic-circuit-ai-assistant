<template>
    <div class="feedback-form">
      <div class="close-icon" @click="goBack">✖</div>
      <h2>意见反馈</h2>
      <form @submit.prevent="submitFeedback">
        <div class="form-group">
          <label for="name">姓名（可选）：</label>
          <input type="text" v-model="name" id="name" placeholder="请输入您的姓名" />
        </div>
        <div class="form-group">
          <label for="email">电子邮件（可选）：</label>
          <input type="email" v-model="email" id="email" placeholder="请输入您的邮箱" />
        </div>
        <div class="form-group">
          <label for="message">留言内容：</label>
          <textarea
            id="message"
            class="feedback-textarea"
            v-model="message"
            placeholder="请留下您的意见和建议"
            required
          ></textarea>
          </div>
        <button type="submit">提交反馈</button>
      </form>
      <div v-if="feedbackSubmitted" class="feedback-success">
        感谢您的反馈！
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: "FeedbackForm",
    data() {
      return {
        name: "",
        email: "",
        message: "",
        feedbackSubmitted: false
      }
    },
    methods: {
      async submitFeedback() {
        // 构造反馈数据
        const feedbackData = {
          name: this.name,
          email: this.email,
          message: this.message,
          timestamp: new Date()
        };
  
        try {
          // 调用后端 API 存储反馈数据
          // 后端服务中 /feedback 接口来处理POST请求
          const response = await fetch(`${window.location.origin}/feedback`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(feedbackData)
          });
  
          if (!response.ok) {
            throw new Error(`提交反馈失败：${response.status}`);
          }
          // 显示提交成功信息
          this.feedbackSubmitted = true;
          // 需要时可以重置表单
          this.name = "";
          this.email = "";
          this.message = "";
        } catch (error) {
          console.error("反馈提交错误：", error);
          // 可在这里添加错误提示
        }
      },
      goBack() {
        // 返回上一页
        this.$router.go(-1);
      }
    }
  }
  </script>
  
  <style scoped>
  .feedback-form {
    max-width: 700px;
    margin: 60px auto;
    padding: 30px;
    background: var(--color-surface);
    border-radius: 8px;
    box-shadow: var(--shadow-soft);
    position: relative;
  }
  .feedback-form h2 {
    text-align: center;
    margin-bottom: 20px;
    color: var(--color-text-main);
  }
  .form-group {
    margin-bottom: 15px;
  }
  .form-group label {
    display: block;
    margin-bottom: 5px;
    font-weight: bold;
  }
  .form-group input{            /* 小输入框样式 */
    width: 100%;
    padding: 12px;              
    font-size: 15px;            
    box-sizing: border-box;
    border: 1px solid var(--color-border-strong);
    border-radius: 4px;
    resize: vertical;   
  }
  .feedback-textarea {          /* 留言板输入框样式 */
    width: 100%;
    padding: 12px;              /* 内边距略大，便于输入 */
    font-size: 15px;            /* 提高字体大小 */
    box-sizing: border-box;
    border: 1px solid var(--color-border-strong);
    border-radius: 4px;
    resize: vertical;           /* 允许垂直缩放 */
    min-height: 150px;
  }
  .feedback-form button {
    width: 100%;
    padding: 10px;
    background-color: var(--color-primary-dark);
    border: none;
    border-radius: 4px;
    color: var(--color-text-on-primary);
    font-size: 16px;
    cursor: pointer;
    transition: background-color 0.3s;
  }
  .feedback-form button:hover {
    background-color: var(--color-primary-hover);
  }
  .feedback-success {
    margin-top: 20px;
    text-align: center;
    color: var(--color-success);
    font-size: 18px;
  }
  /* 右上角叉号按钮 */
  .close-icon {
    position: absolute;
    top: 10px;
    right: 10px;
    font-size: 24px;
    line-height: 1;
    color: var(--color-text-main);
    cursor: pointer;
    transition: color 0.3s;
  }
  .close-icon:hover {
    color: var(--color-text-secondary); /* 悬停时略微变深 */
  }
  </style>
  