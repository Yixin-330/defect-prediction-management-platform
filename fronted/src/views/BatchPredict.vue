<template>
  <div class="batch-predict-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">批量预测与评估</h1>
        <p class="page-subtitle">选择仓库 → 对全部提交批量预测 → 按风险降序查看结果 → 进入提交详情查看 diff 与解释。</p>
      </div>
      <button class="btn btn-secondary" @click="loadRepos">↻ 刷新仓库</button>
    </div>

    <LoadingState v-if="repoLoading" text="正在加载仓库列表..." />
    <ErrorState v-else-if="repoError" :message="repoError" @retry="loadRepos" />

    <template v-else>
      <div class="card p-20 mt-16">
        <div class="section-title mb-16">选择仓库并执行批量预测</div>
        <EmptyState v-if="!repos.length" text="暂无已连接仓库，请先在「仓库接入」页克隆仓库" icon="⬚" />
        <template v-else>
          <select v-model="selectedRepoId" class="repo-select">
            <option :value="null" disabled>请选择仓库</option>
            <option v-for="r in repos" :key="r.id" :value="r.id">{{ r.name || r.url }}（ID: {{ r.id }}）</option>
          </select>
          <div class="form-actions mt-16">
            <button class="btn btn-primary" :disabled="!selectedRepoId || predicting" @click="handleBatchPredict">
              {{ predicting ? '批量预测中...' : '执行批量预测' }}
            </button>
          </div>
          <div v-if="batchMessage" class="mt-16">
            <InfoAlert :type="batchError ? 'error' : 'success'">{{ batchMessage }}</InfoAlert>
          </div>
        </template>
      </div>

      <div class="card p-20 mt-16">
        <div class="table-header">
          <span class="section-title">预测结果</span>
          <span class="text-sm text-secondary">共 {{ results.length }} 条 · 按风险降序</span>
        </div>
        <EmptyState v-if="!results.length" text="暂无预测结果，执行批量预测后将在此展示" icon="📋" />
        <table v-else class="data-table">
          <thead>
            <tr><th>提交ID</th><th>风险分数</th><th>风险等级</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="row in results" :key="row.commit_id">
              <td class="mono">{{ row.commit_id }}</td>
              <td>
                <div class="score-bar-wrap">
                  <div class="score-bar" :style="scoreBarStyle(row.risk_score)"></div>
                  <span class="score-text">{{ fmtScore(row.risk_score) }}</span>
                </div>
              </td>
              <td><RiskTag :level="levelFromBackend(row.level)" :score="row.risk_score" show-score /></td>
              <td><router-link :to="`/commits/${row.commit_id}`" class="text-sm">查看详情与 diff</router-link></td>
            </tr>
          </tbody>
        </table>
      </div>

      <InfoAlert type="info" class="mt-16">
        正式评估使用冻结阈值；界面临时调整阈值属探索性结果，不覆盖正式记录。无标签提交可预测但不可评估。
      </InfoAlert>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import InfoAlert from '@/components/common/InfoAlert.vue'
import RiskTag from '@/components/common/RiskTag.vue'
import { getProjects } from '@/api/project'
import { batchPredict } from '@/api/batch'
import { levelFromBackend } from '@/utils/format'

const repos = ref([])
const repoLoading = ref(true)
const repoError = ref(null)
const selectedRepoId = ref(null)
const predicting = ref(false)
const results = ref([])
const batchMessage = ref('')
const batchError = ref(false)

function scoreBarStyle(score) {
  const pct = Math.max(0, Math.min(1, score || 0)) * 100
  let color = '#22c55e'
  if (score >= 0.7) color = '#ef4444'
  else if (score >= 0.4) color = '#f97316'
  return { width: pct + '%', background: color }
}
function fmtScore(v) { return v == null ? '-' : Number(v).toFixed(2) }

async function loadRepos() {
  repoLoading.value = true
  repoError.value = null
  try {
    const list = await getProjects()
    repos.value = list || []
  } catch (e) {
    repoError.value = e.message || '加载仓库失败'
  } finally {
    repoLoading.value = false
  }
}

async function handleBatchPredict() {
  if (!selectedRepoId.value) return
  predicting.value = true
  batchMessage.value = ''
  batchError.value = false
  results.value = []
  try {
    const res = await batchPredict(selectedRepoId.value)
    batchMessage.value = res.message || '批量预测完成'
    const data = res.data || []
    data.sort((a, b) => (b.risk_score || 0) - (a.risk_score || 0))
    results.value = data
  } catch (e) {
    batchMessage.value = e.message || '批量预测失败'
    batchError.value = true
  } finally {
    predicting.value = false
  }
}

onMounted(loadRepos)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.p-20 { padding: 20px; }
.repo-select { width: 100%; padding: 8px 12px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); background: var(--bg-input); color: var(--text-primary); font-size: 14px; }
.form-actions { display: flex; gap: 12px; }
.table-header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 12px; }
.data-table { width: 100%; }
.data-table th, .data-table td { padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border-color); }
.data-table th { font-size: 12px; color: var(--text-tertiary); font-weight: 500; }
.data-table td { font-size: 13px; }
.mono { font-family: ui-monospace, monospace; }
.score-bar-wrap { display: flex; align-items: center; gap: 8px; min-width: 120px; }
.score-bar { height: 6px; border-radius: 3px; min-width: 20px; transition: width 0.3s; }
.score-text { font-size: 13px; font-weight: 500; }
.mt-16 { margin-top: 16px; }
.mb-16 { margin-bottom: 16px; }
</style>