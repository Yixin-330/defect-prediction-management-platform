<template>
  <div class="commit-list">
    <div class="page-header">
      <div>
        <h1 class="page-title">提交风险列表</h1>
        <p class="page-subtitle">按风险分数降序排列，优先查看高风险变更。</p>
      </div>
      <div class="flex gap-12 items-center">
        <select v-if="projects.length > 0" v-model="selectedProjectId" @change="loadData" class="project-select">
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
        <button class="btn btn-secondary" @click="loadData">↻ 刷新</button>
      </div>
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
              <td>
                <div class="score-bar-wrap">
                  <div class="score-bar" :style="scoreBarStyle(row.risk_score)"></div>
                  <span class="score-text">{{ row.risk_score?.toFixed(2) }}</span>
                </div>
              </td>
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
import { levelFromBackend } from '@/utils/format'
import { getRankingWithFallback } from '@/utils/dataSync'

const loading = ref(true)
const error = ref(null)
const items = ref([])
const projects = ref([])
const selectedProjectId = ref(null)

function scoreBarStyle(score) {
  const pct = Math.max(0, Math.min(1, score || 0)) * 100
  let color = '#22c55e'
  if (score >= 0.7) color = '#ef4444'
  else if (score >= 0.4) color = '#f97316'
  return { width: pct + '%', background: color }
}

async function loadData() {
  loading.value = true
  error.value = null
  try {
    const { items: rankingItems, projects: pros } = await getRankingWithFallback(selectedProjectId.value)
    items.value = rankingItems
    projects.value = pros || []
    if (pros && pros.length > 0 && !selectedProjectId.value) selectedProjectId.value = pros[0].id
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
.project-select { padding: 8px 12px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); background: var(--bg-input); color: var(--text-primary); font-size: 14px; min-width: 160px; }
.flex { display: flex; }
.gap-12 { gap: 12px; }
.items-center { align-items: center; }
.table-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--border-color); }
.data-table { width: 100%; }
.data-table th, .data-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border-color); }
.data-table th { font-size: 12px; color: var(--text-tertiary); font-weight: 500; }
.data-table td { font-size: 14px; }
.data-table tbody tr:hover { background-color: var(--bg-table-hover); }
.score-bar-wrap { display: flex; align-items: center; gap: 8px; min-width: 120px; }
.score-bar { height: 6px; border-radius: 3px; min-width: 20px; transition: width 0.3s; }
.score-text { font-size: 13px; font-weight: 500; }
</style>