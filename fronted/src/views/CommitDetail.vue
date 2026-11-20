<template>
  <div class="commit-detail">
    <div class="page-header">
      <div>
        <h1 class="page-title">提交详情与风险解释</h1>
        <p class="page-subtitle">提交ID: {{ id }}</p>
      </div>
      <div class="flex gap-12">
        <router-link to="/commits" class="btn btn-secondary">返回列表</router-link>
        <router-link :to="`/commits/${id}/arrange`" class="btn btn-primary">安排代码审查</router-link>
      </div>
    </div>

    <LoadingState v-if="loading" text="正在加载预测数据..." />

    <ErrorState v-else-if="error && !notFound" :message="error" @retry="loadData" />

    <div v-else-if="notFound" class="card p-20 mt-24 not-found-state">
      <div class="section-title mb-16">尚无预测结果</div>
      <InfoAlert type="warning">
        该提交尚未生成预测结果。请先在「批量预测」页面或「提交风险列表」中触发预测，再返回此页面查看风险解释。
      </InfoAlert>
      <div class="flex gap-12 mt-16">
        <router-link to="/batch-predict" class="btn btn-primary">前往批量预测</router-link>
        <router-link to="/commits" class="btn btn-secondary">返回风险列表</router-link>
      </div>
    </div>

    <template v-else>
      <div class="two-col mt-24">
        <div class="card p-20">
          <div class="section-title mb-16">提交信息</div>
          <div class="commit-meta">
            <div class="meta-row"><span class="meta-label">提交ID</span><span>{{ prediction.commit_id }}</span></div>
            <div class="meta-row"><span class="meta-label">预测时间</span><span>{{ formatDateTime(prediction.predicted_at) }}</span></div>
          </div>
        </div>

        <div class="card p-20 risk-score-card">
          <div class="section-title mb-16">预测风险信号</div>
          <div class="risk-score">{{ prediction.risk_score?.toFixed(2) }}</div>
          <RiskTag :level="levelFromBackend(prediction.level)" :score="prediction.risk_score" show-score />
          <p class="text-sm text-secondary mt-16">分数范围 0–1 · 仅供参考</p>
        </div>
      </div>

      <div class="card p-20 mt-24">
        <div class="section-title mb-16">算法模型信息</div>
        <div class="model-info-grid">
          <div class="model-info-item">
            <span class="meta-label">模型来源</span>
            <span class="model-source" :class="isRealModel ? 'real' : 'mock'">
              {{ isRealModel ? '🤖 机器学习模型' : '📋 规则兜底' }}
            </span>
          </div>
          <div class="model-info-item">
            <span class="meta-label">模型ID</span>
            <span>{{ prediction.model_id || '-' }}</span>
          </div>
          <div class="model-info-item">
            <span class="meta-label">风险等级</span>
            <span>{{ prediction.level || '-' }}</span>
          </div>
          <div class="model-info-item">
            <span class="meta-label">特征解释</span>
            <span>{{ prediction.explanation_available ? '可用' : '暂不支持' }}</span>
          </div>
        </div>
        <InfoAlert :type="isRealModel ? 'success' : 'warning'" class="mt-16">
          {{ modelDescription }}
        </InfoAlert>
      </div>

      <InfoAlert type="info" class="mt-24">风险分数用于安排审查优先级，不是缺陷认定。</InfoAlert>

      <div class="card p-20 mt-24">
        <div class="section-title mb-16">代码变更 (diff)</div>
        <LoadingState v-if="diffLoading" text="正在加载代码变更..." />
        <ErrorState v-else-if="diffError" :message="diffError" @retry="loadDiff" />
        <EmptyState v-else-if="!diffText" text="该提交无 diff 内容或暂无可定位的变更证据，仅提供审查范围建议" icon="📝" />
        <pre v-else class="diff-block"><code>{{ diffText }}</code></pre>
        <InfoAlert type="info" class="mt-16">diff 绑定固定提交及父版本；无独立位置证据时仅展示变更范围，修复建议需人工确认。</InfoAlert>
      </div>

      <div class="card p-20 mt-24" v-if="!prediction.explanation_available">
        <div class="section-title mb-8">风险解释</div>
        <InfoAlert type="warning">当前模型暂不支持特征级解释。请结合代码变更内容进行人工审查。</InfoAlert>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import RiskTag from '@/components/common/RiskTag.vue'
import InfoAlert from '@/components/common/InfoAlert.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import { getPrediction } from '@/api/prediction'
import { getCommitDiff } from '@/api/batch'
import { levelFromBackend, formatDateTime } from '@/utils/format'

const route = useRoute()
const id = route.params.id
const loading = ref(true)
const error = ref(null)
const notFound = ref(false)
const prediction = ref({})
const diffLoading = ref(false)
const diffError = ref(null)
const diffText = ref('')

async function loadDiff() {
  diffLoading.value = true
  diffError.value = null
  try {
    const res = await getCommitDiff(id)
    diffText.value = (res && res.diff) || ''
  } catch (e) {
    diffError.value = e.message || '加载 diff 失败'
    diffText.value = ''
  } finally {
    diffLoading.value = false
  }
}

const isRealModel = computed(() => {
  const mid = prediction.value.model_id || ''
  return mid.includes('synthetic') || mid.includes('logistic') || mid.includes('lr')
})

const modelDescription = computed(() => {
  if (isRealModel.value) {
    return '该预测由逻辑回归模型生成，基于提交的变更特征（修改规模、熵、开发者经验等14维特征）计算风险概率。'
  }
  return '模型未加载或加载失败，当前使用规则兜底：包含 fix/bug 关键词的提交判为高风险，提交信息过短判为中风险，其余为低风险。'
})

async function loadData() {
  loading.value = true
  error.value = null
  notFound.value = false
  try {
    prediction.value = await getPrediction(id)
    loadDiff()
  } catch (e) {
    if (e.code === 404 || (e.message || '').includes('404') || (e.message || '').includes('Not Found')) {
      notFound.value = true
    } else {
      error.value = e.message || '加载失败'
    }
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.two-col { display: grid; grid-template-columns: 1.5fr 1fr; gap: 16px; }
.p-20 { padding: 20px; }
.commit-meta { display: flex; flex-direction: column; gap: 8px; }
.meta-row { display: flex; gap: 12px; font-size: 14px; }
.meta-label { color: var(--text-tertiary); min-width: 80px; }
.risk-score-card { text-align: center; }
.risk-score { font-size: 48px; font-weight: 700; color: var(--color-high-risk); line-height: 1; margin: 8px 0 12px; }
.model-info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.model-info-item { display: flex; flex-direction: column; gap: 4px; }
.model-source { font-size: 14px; font-weight: 500; }
.model-source.real { color: var(--color-success); }
.model-source.mock { color: var(--color-warning); }
.mt-24 { margin-top: 24px; }
.mt-16 { margin-top: 16px; }
.diff-block { background: var(--bg-code, #0d1117); color: var(--text-primary); padding: 16px; border-radius: var(--radius-sm); overflow: auto; max-height: 480px; font-size: 12px; line-height: 1.6; font-family: ui-monospace, monospace; border: 1px solid var(--border-color); }
.diff-block code { white-space: pre; }
</style>