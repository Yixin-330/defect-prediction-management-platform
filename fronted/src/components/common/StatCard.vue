<template>
  <div class="stat-card card">
    <div class="stat-value" :class="{ 'stat-danger': danger, 'stat-primary': primary }">{{ value }}</div>
    <div class="stat-label">{{ label }}</div>
    <div v-if="sub" class="stat-sub">{{ sub }}</div>
  </div>
</template>

<script setup>
defineProps({
  value: { type: [String, Number], required: true },
  label: { type: String, required: true },
  sub: { type: String, default: '' },
  danger: { type: Boolean, default: false },
  primary: { type: Boolean, default: false }
})
</script>

<style scoped>
.stat-card {
  padding: 20px;
}
.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}
.stat-danger { color: var(--color-high-risk); }
.stat-primary { color: var(--color-primary); }
.stat-label {
  font-size: 14px;
  color: var(--text-primary);
  margin-top: 8px;
  font-weight: 500;
}
.stat-sub {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}
</style>