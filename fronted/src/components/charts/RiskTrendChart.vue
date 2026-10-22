<template>
  <div ref="chartRef" class="chart-container"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] }
})

const chartRef = ref(null)
let chart = null

function renderChart() {
  if (!chart) return
  const days = props.data.map(d => d.date)
  const high = props.data.map(d => d.high || 0)
  const mid = props.data.map(d => d.mid || 0)
  const low = props.data.map(d => d.low || 0)

  chart.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: {
      data: ['高风险', '中风险', '低风险'],
      top: 0,
      textStyle: { color: '#94a3b8' }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', top: 40, containLabel: true },
    xAxis: {
      type: 'category',
      data: days,
      axisLabel: { color: '#94a3b8' },
      axisLine: { lineStyle: { color: '#334155' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#94a3b8' },
      splitLine: { lineStyle: { color: '#334155' } }
    },
    series: [
      { name: '高风险', type: 'bar', stack: 'risk', data: high, itemStyle: { color: '#ef4444' } },
      { name: '中风险', type: 'bar', stack: 'risk', data: mid, itemStyle: { color: '#f97316' } },
      { name: '低风险', type: 'bar', stack: 'risk', data: low, itemStyle: { color: '#22c55e' } }
    ]
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

watch(() => props.data, renderChart, { deep: true })
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 220px;
}
</style>