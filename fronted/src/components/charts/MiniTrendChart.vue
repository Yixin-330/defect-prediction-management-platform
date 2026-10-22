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
  chart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '5%', right: '5%', bottom: '10%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: props.data.map(d => d.date),
      axisLabel: { color: '#94a3b8', fontSize: 10 },
      axisLine: { lineStyle: { color: '#334155' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#94a3b8', fontSize: 10 },
      splitLine: { lineStyle: { color: '#334155' } }
    },
    series: [{
      type: 'line',
      data: props.data.map(d => d.value),
      smooth: true,
      symbol: 'circle',
      symbolSize: 4,
      lineStyle: { color: '#3b82f6', width: 2 },
      itemStyle: { color: '#3b82f6' },
      areaStyle: { color: 'rgba(59,130,246,0.1)' }
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

watch(() => props.data, renderChart, { deep: true })
</script>

<style scoped>
.chart-container {
  width: 100%;
  height: 80px;
}
</style>