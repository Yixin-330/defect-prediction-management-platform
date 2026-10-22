<template>
  <span class="tag" :style="tagStyle">{{ labelText }}</span>
</template>

<script setup>
import { computed } from 'vue'
import { riskLabel } from '@/utils/format'

const props = defineProps({
  level: { type: String, default: 'none' },
  score: { type: Number, default: null },
  showScore: { type: Boolean, default: false }
})

const labelText = computed(() => {
  const base = riskLabel(props.level)
  if (props.showScore && props.score != null) {
    return `${base} ${props.score.toFixed(2)}`
  }
  return base
})

const styleMap = {
  high: { bg: 'var(--color-high-risk-bg)', color: 'var(--color-high-risk)' },
  mid: { bg: 'var(--color-mid-risk-bg)', color: 'var(--color-mid-risk)' },
  low: { bg: 'var(--color-low-risk-bg)', color: 'var(--color-low-risk)' },
  none: { bg: 'var(--bg-tag)', color: 'var(--text-tertiary)' }
}

const tagStyle = computed(() => {
  const s = styleMap[props.level] || styleMap.none
  return { backgroundColor: s.bg, color: s.color }
})
</script>