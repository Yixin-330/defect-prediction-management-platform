<template>
  <div class="commit-list">
    <div class="page-header">
      <div>
        <h1 class="page-title">提交风险列表</h1>
        <p class="page-subtitle">按风险分数降序排列，优先查看高风险变更。</p>
      </div>
      <button class="btn btn-secondary" @click="loadData">↻ 刷新</button>
    </div>

    <LoadingState v-if="loading" text="正在加载风险列表..." />

    <ErrorState v-else-if="error" :message="error" @retry="loadData" />

    <template v-else>
      <div class="card mt-16">
        <div class="table-header">
          <span class="section-title">提交队列</span>
          <span class="text-sm text-secondary">共 {{ items.length }} 条 · 排序：风险分数 ↓</span>
        </div>
        <EmptyState v-if="!items.length" text="暂无预测数据，请先克隆仓库并生成预测" icon="📭" />
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>提交ID</th>
              <th>风险分数</th>
              <th>风险等级</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in items" :key="row.commit_id">
              <td>{{ row.commit_hash }}</td>
              <td>{{ row.risk_score?.toFixed(2) }}</td>
              <td><RiskTag :level="levelFromBackend(row.level)" :score="row.risk_score" show-score /></td>
              <td><router-link :to="`/commits/${row.commit_id}`" class="text-sm">查看详情</router-link></td>
            </tr>
          </tbody>
        </table>
      </div>

      <InfoAlert type="info" class="mt-16">风险分数用于安排审查优先级，不是缺陷认定。</InfoAlert>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import RiskTag from '@/components/common/RiskTag.vue'
import InfoAlert from '@/components/common/InfoAlert.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { getProjects, getRiskRanking } from '@/api/project'
import { levelFromBackend } from '@/utils/format'

const loading = ref(true)
const error = ref(null)
const items = ref([])

async function loadData() {
  loading.value = true
  error.value = null
  try {
    const projects = await getProjects()
    const project = (projects || [])[0]
    if (!project) {
      items.value = []
      loading.value = false
      return
    }
    const res = await getRiskRanking(project.id)
    items.value = res.items || []
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
.table-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--border-color); }
.data-table { width: 100%; }
.data-table th, .data-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border-color); }
.data-table th { font-size: 12px; color: var(--text-tertiary); font-weight: 500; }
.data-table td { font-size: 14px; }
.data-table tbody tr:hover { background-color: var(--bg-table-hover); }
</style>