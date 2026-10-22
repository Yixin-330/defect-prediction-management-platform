<template>
  <div class="quality-trend">
    <div class="page-header">
      <div>
        <h1 class="page-title">项目质量趋势</h1>
      </div>
      <router-link to="/" class="btn btn-secondary">返回工作台</router-link>
    </div>

    <LoadingState v-if="loading" text="正在加载趋势数据..." />

    <ErrorState v-else-if="error" :message="error" @retry="loadData" />

    <template v-else>
      <div class="grid-4 mt-16">
        <StatCard :value="summary.total_commits || 0" label="总提交数" />
        <StatCard :value="summary.high_risk_commits || 0" label="高风险提交" danger />
        <StatCard :value="summary.total_repos || 0" label="仓库数" primary />
        <StatCard :value="summary.abnormal_commits || 0" label="异常提交" />
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
import { getDashboardSummary } from '@/api/project'
import { formatDateTime, buildTrendFromCommits } from '@/utils/format'

const loading = ref(true)
const error = ref(null)
const summary = ref({})
const trendData = ref([])
const recentCommits = ref([])

async function loadData() {
  loading.value = true
  error.value = null
  try {
    const res = await getDashboardSummary()
    summary.value = res
    trendData.value = buildTrendFromCommits(res.recent_commits)
    recentCommits.value = res.recent_commits || []
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
.p-20 { padding: 20px; }
.data-table { width: 100%; }
.data-table th, .data-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border-color); }
.data-table th { font-size: 12px; color: var(--text-tertiary); font-weight: 500; }
.data-table td { font-size: 14px; }
.data-table tbody tr:hover { background-color: var(--bg-table-hover); }
</style>