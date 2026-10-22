<template>
  <div class="state-container">
    <div class="state-icon">{{ icon }}</div>
    <p class="state-text">{{ text }}</p>
    <button v-if="retry" class="btn btn-primary mt-16" @click="$emit('retry')">重试</button>
  </div>
</template>

<script setup>
defineProps({
  text: { type: String, default: '暂无数据' },
  icon: { type: String, default: '📭' },
  retry: { type: Boolean, default: false }
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
  font-size: 48px;
  margin-bottom: 16px;
}
.state-text {
  font-size: 14px;
  color: var(--text-secondary);
}
</style>