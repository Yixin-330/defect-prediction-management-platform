<template>
  <div class="quality-trend">
    <div class="page-header">
      <div>
        <h1 class="page-title">项目质量趋势</h1>
      </div>
      <div class="flex gap-12 items-center">
        <select v-if="projects.length > 0" v-model="selectedProjectId" @change="loadData" class="project-select">
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
        <select v-model="timeRange" @change="loadData" class="project-select">
          <option value="all">全部时间</option>
          <option value="7">近7天</option>
          <option value="30">近30天</option>
          <option value="90">近90天</option>
        </select>
        <router-link to="/" class="btn btn-secondary">返回工作台</router-link>
      </div>
    </div>

    <LoadingState v-if="loading" text="正在加载趋势数据..." />

    <ErrorState v-else-if="error" :message="error" @retry="loadData" />

    <template v-else>
      <div class="grid-4 mt-16">
        <StatCard :value="summary.total_commits || 0" label="总提交数" />
        <StatCard :value="summary.high_risk_commits || 0" label="高风险提交" danger />
        <StatCard :value="summary.total_repos || 0" label="仓库数" primary />
        <StatCard :value="summary.abnormal_comits || 0" label="异常提交" />
      </div>

      <div class="card p-20 mt-24">
        <div class="section-title mb-8">风险趋势</div>
        <p class="text-sm text-secondary mb-16">基于历史预测数据</p>
        <EmptyState v-if="!trendData.length" text="暂无趋势数据" icon="📈" />
        <RiskTrendChart v-else :data="trendData" />
      </div>

      <div class="card p-20 mt-24" v-if="recentCommits.length">
        <div class="section-title mb-16">最近提交</div>
        <table class="data-table">
          <thead>
            <tr><th>提交哈希</th><th>作者</th><th>提交信息</th><th>时间</th></tr>
          </thead>
          <tbody>
            <tr v-for="c in recentCommits" :key="c.id">
              <td>{{ c.hash }}</td>
              <td>{{ c.author }}</td>
              <td>{{ c.message }}</td>
              <td>{{ formatDateTime(c.date) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import StatCard from '@/components/common/StatCard.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import RiskTrendChart from '@/components/charts/RiskTrendChart.vue'
import { getDashboardSummary, getProjects, getProjectPredictions } from '@/api/project'
import { formatDateTime, buildTrendFromCommits, buildTrendFromPredictions } from '@/utils/format'

const loading = ref(true)
const error = ref(null)
const summary = ref({})
const trendData = ref([])
const recentCommits = ref([])
const projects = ref([])
const selectedProjectId = ref(null)
const timeRange = ref('all')

async function loadData() {
  loading.value = true
  error.value = null
  try {
    const res = await getDashboardSummary()
    summary.value = res
    recentCommits.value = res.recent_commits || []

    const allProjects = await getProjects()
    projects.value = allProjects || []
    const proj = selectedProjectId.value
      ? allProjects?.find(p => p.id === selectedProjectId.value)
      : (allProjects || [])[0]
    if (proj && !selectedProjectId.value) selectedProjectId.value = proj.id

    if (proj) {
      try {
        const predData = await getProjectPredictions(proj.id)
        let preds = predData.predictions || []
        if (timeRange.value !== 'all') {
          const days = parseInt(timeRange.value)
          const cutoff = new Date(Date.now() - days * 86400000).toISOString()
          preds = preds.filter(p => p.predicted_at >= cutoff)
        }
        trendData.value = buildTrendFromPredictions(preds)
      } catch (e) {
        trendData.value = buildTrendFromCommits(res.recent_commits)
      }
    } else {
      trendData.value = buildTrendFromCommits(res.recent_commits)
    }

  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.project-select { padding: 8px 12px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); background: var(--bg-input); color: var(--text-primary); font-size: 14px; min-width: 120px; }
.flex { display: flex; }
.gap-12 { gap: 12px; }
.items-center { align-items: center; }
.p-20 { padding: 20px; }
.data-table { width: 100%; }
.data-table th, .data-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border-color); }
.data-table th { font-size: 12px; color: var(--text-tertiary); font-weight: 500; }
.data-table td { font-size: 14px; }
.data-table tbody tr:hover { background-color: var(--bg-table-hover); }
</style>