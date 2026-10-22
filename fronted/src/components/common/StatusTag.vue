<template>
  <span class="tag" :style="tagStyle">{{ labelText }}</span>
</template>

<script setup>
import { computed } from 'vue'
import { predictStatusLabel, reviewStatusLabel } from '@/utils/format'

const props = defineProps({
  type: { type: String, default: 'review' },
  status: { type: String, required: true }
})

const labelText = computed(() =>
  props.type === 'predict' ? predictStatusLabel(props.status) : reviewStatusLabel(props.status)
)

const statusStyles = {
  completed: { bg: 'var(--color-success-bg)', color: 'var(--color-success)' },
  done: { bg: 'var(--color-success-bg)', color: 'var(--color-success)' },
  analyzing: { bg: 'var(--bg-tag)', color: 'var(--text-secondary)' },
  pending: { bg: 'var(--bg-tag)', color: 'var(--text-secondary)' },
  waiting: { bg: 'var(--color-info-bg)', color: 'var(--color-info)' },
  reviewing: { bg: 'var(--color-info-bg)', color: 'var(--color-info)' },
  rechecking: { bg: 'var(--color-warning-bg)', color: 'var(--color-warning)' },
  failed: { bg: 'var(--color-error-bg)', color: 'var(--color-error)' },
  ignored: { bg: 'var(--bg-tag)', color: 'var(--text-tertiary)' }
}

const tagStyle = computed(() => {
  const s = statusStyles[props.status] || statusStyles.pending
  return { backgroundColor: s.bg, color: s.color }
})
</script>