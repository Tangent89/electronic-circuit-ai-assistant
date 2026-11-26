<!-- src/components/BackButton.vue -->
<template>
    <button class="back-button" @click="goBack">
      后退
    </button>
  </template>
  
  <script>
  export default {
    name: 'BackButton',
    methods: {
      goBack() {
        this.$router.back();
      }
    }
  }
  </script>
  
  <style scoped>
  .back-button {
    padding: 10px 20px;
    font-size: 16px;
    background-color: var(--color-primary-dark);
    border: none;
    border-radius: 4px;
    color: var(--color-text-on-primary);
    cursor: pointer;
    transition: background-color 0.3s;
  }
  .back-button:hover {
    background-color: var(--color-primary-hover);
  }
  </style>
  