<template>
  <div ref="chartRef" class="chart-container"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  features: { type: Array, default: () => [] }
})

const chartRef = ref(null)
let chart = null

function renderChart() {
  if (!chart) return
  const sorted = [...props.features].sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
  const names = sorted.map(f => f.name)
  const values = sorted.map(f => f.value)
  const colors = values.map(v => v >= 0 ? '#ef4444' : '#22c55e')

  chart.setOption({
    tooltip: { trigger: 'axis', formatter: (p) => `${p[0].name}: ${p[0].value > 0 ? '+' : ''}${p[0].value.toFixed(2)}` },
    grid: { left: '3%', right: '10%', bottom: '3%', top: 10, containLabel: true },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#94a3b8', formatter: (v) => v.toFixed(2) },
      splitLine: { lineStyle: { color: '#334155' } }
    },
    yAxis: {
      type: 'category',
      data: names,
      axisLabel: { color: '#f1f5f9' },
      axisLine: { lineStyle: { color: '#334155' } }
    },
    series: [{
      type: 'bar',
      data: values.map((v, i) => ({ value: v, itemStyle: { color: colors[i] } })),
      barWidth: 16,
      label: {
        show: true,
        position: 'right',
        formatter: (p) => p.value >= 0 ? `+${p.value.toFixed(2)}` : p.value.toFixed(2),
        color: '#94a3b8'
      }
    }]
  })
}

onMounted(() => {
  chart = echarts.init(chartRef.value)
  renderChart()
  window.addEventListener('resize', () => chart?.resize())
})

onUnmounted(() => {
  chart?.dispose()
  chart = null
})

watch(() => props.features, renderChart, { deep: true })
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 240px;
}
</style>