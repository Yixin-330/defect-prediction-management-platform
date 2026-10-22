<template>
  <div class="state-container">
    <div class="state-icon">⚠</div>
    <p class="state-text">{{ message }}</p>
    <button class="btn btn-primary mt-16" @click="$emit('retry')">重试</button>
  </div>
</template>

<script setup>
defineProps({
  message: { type: String, default: '请求失败，请稍后重试' }
})
defineEmits(['retry'])
</script>

<style scoped>
.state-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
}
.state-icon {
  font-size: 40px;
  color: var(--color-error);
  margin-bottom: 16px;
}
.state-text {
  font-size: 14px;
  color: var(--text-secondary);
  text-align: center;
  max-width: 400px;
}
</style>