<template>
  <div class="info-alert" :class="`alert-${type}`">
    <span class="alert-icon">{{ iconMap[type] }}</span>
    <div class="alert-content">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  type: { type: String, default: 'info' }
})

const iconMap = { info: 'ℹ', warning: '⚠', error: '✕', success: '✓' }
</script>

<style scoped>
.info-alert {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 12px 16px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  line-height: 1.6;
}
.alert-info {
  background-color: var(--color-info-bg);
  color: var(--color-primary-light);
}
.alert-warning {
  background-color: var(--color-warning-bg);
  color: var(--color-warning);
}
.alert-error {
  background-color: var(--color-error-bg);
  color: var(--color-error);
}
.alert-success {
  background-color: var(--color-success-bg);
  color: var(--color-success);
}
.alert-icon {
  font-size: 16px;
  flex-shrink: 0;
}
.alert-content {
  flex: 1;
}
</style>