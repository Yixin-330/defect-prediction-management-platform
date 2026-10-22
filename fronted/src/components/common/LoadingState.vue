<template>
  <div class="state-container">
    <div class="spinner"></div>
    <p class="state-text">{{ text }}</p>
  </div>
</template>

<script setup>
defineProps({
  text: { type: String, default: '加载中...' }
})
</script>

<style scoped>
.state-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
}
.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-color);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 16px;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.state-text {
  font-size: 14px;
  color: var(--text-secondary);
}
</style>