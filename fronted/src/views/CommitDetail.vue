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

    <ErrorState v-else-if="error" :message="error" @retry="loadData" />

    <template v-else>
      <div class="two-col mt-24">
        <div class="card p-20">
          <div class="section-title mb-16">提交信息</div>
          <div class="commit-meta">
            <div class="meta-row"><span class="meta-label">提交ID</span><span>{{ prediction.commit_id }}</span></div>
            <div class="meta-row"><span class="meta-label">预测模型</span><span>{{ prediction.model_id }}</span></div>
            <div class="meta-row"><span class="meta-label">预测时间</span><span>{{ formatDateTime(prediction.predicted_at) }}</span></div>
            <div class="meta-row"><span class="meta-label">解释可用</span><span>{{ prediction.explanation_available ? '是' : '否' }}</span></div>
          </div>
        </div>

        <div class="card p-20 risk-score-card">
          <div class="section-title mb-16">预测风险信号</div>
          <div class="risk-score">{{ prediction.risk_score?.toFixed(2) }}</div>
          <RiskTag :level="levelFromBackend(prediction.level)" :score="prediction.risk_score" show-score />
          <p class="text-sm text-secondary mt-16">分数范围 0–1 · 仅供参考</p>
        </div>
      </div>

      <InfoAlert type="info" class="mt-24">风险分数用于安排审查优先级，不是缺陷认定。</InfoAlert>

      <div class="card p-20 mt-24" v-if="!prediction.explanation_available">
        <div class="section-title mb-8">风险解释</div>
        <InfoAlert type="warning">当前模型暂不支持特征级解释。请结合代码变更内容进行人工审查。</InfoAlert>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import RiskTag from '@/components/common/RiskTag.vue'
import InfoAlert from '@/components/common/InfoAlert.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import { getPrediction } from '@/api/prediction'
import { levelFromBackend, formatDateTime } from '@/utils/format'

const route = useRoute()
const id = route.params.id
const loading = ref(true)
const error = ref(null)
const prediction = ref({})

async function loadData() {
  loading.value = true
  error.value = null
  try {
    prediction.value = await getPrediction(id)
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
.two-col { display: grid; grid-template-columns: 1.5fr 1fr; gap: 16px; }
.p-20 { padding: 20px; }
.commit-meta { display: flex; flex-direction: column; gap: 8px; }
.meta-row { display: flex; gap: 12px; font-size: 14px; }
.meta-label { color: var(--text-tertiary); min-width: 80px; }
.risk-score-card { text-align: center; }
.risk-score { font-size: 48px; font-weight: 700; color: var(--color-high-risk); line-height: 1; margin: 8px 0 12px; }
</style>