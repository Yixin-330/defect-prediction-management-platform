<template>
  <div class="arrange-review">
    <div class="page-header">
      <div>
        <h1 class="page-title">安排代码审查</h1>
        <p class="page-subtitle">为提交选择审查人并创建审查任务</p>
      </div>
      <router-link :to="`/commits/${commitId}`" class="btn btn-secondary">返回提交详情</router-link>
    </div>

    <LoadingState v-if="loading" text="正在加载预测数据..." />

    <ErrorState v-else-if="error" :message="error" @retry="loadData" />

    <template v-else>
      <div class="card p-20 mt-24 form-card">
        <div class="section-title mb-24">审查任务分配</div>

        <div class="two-col mb-24">
          <div class="card p-20">
            <div class="section-title mb-16">提交预测信息</div>
            <div class="commit-meta">
              <div class="meta-row"><span class="meta-label">提交ID</span><span>{{ prediction.commit_id }}</span></div>
              <div class="meta-row"><span class="meta-label">风险分数</span><span>{{ prediction.risk_score?.toFixed(2) }}</span></div>
              <div class="meta-row"><span class="meta-label">风险等级</span><span>{{ prediction.level }}</span></div>
              <div class="meta-row"><span class="meta-label">预测模型</span><span>{{ prediction.model_id }}</span></div>
            </div>
          </div>

          <div class="form-body">
            <div class="form-item mb-24">
              <label>审查人 <span class="required">*</span></label>
              <input v-model="form.handler" type="text" placeholder="输入审查人姓名" class="mt-8" />
            </div>

            <div class="form-item mb-24">
              <label>审查备注</label>
              <textarea v-model="form.note" rows="4" placeholder="补充审查重点说明" class="mt-8"></textarea>
            </div>
          </div>
        </div>

        <InfoAlert type="info">提交后将创建审查记录，状态为"待审查"。</InfoAlert>

        <div class="form-actions mt-24">
          <button class="btn btn-secondary" @click="$router.back()">取消</button>
          <button class="btn btn-primary" :disabled="submitting" @click="handleSubmit">
            {{ submitting ? '提交中...' : '✓ 保存并安排审查' }}
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import InfoAlert from '@/components/common/InfoAlert.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import { getPrediction } from '@/api/prediction'
import { createReview } from '@/api/review'

const route = useRoute()
const router = useRouter()
const commitId = route.params.id
const loading = ref(true)
const error = ref(null)
const submitting = ref(false)
const prediction = ref({})
const form = ref({ handler: '', note: '' })

async function loadData() {
  loading.value = true
  error.value = null
  try {
    prediction.value = await getPrediction(commitId)
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function handleSubmit() {
  if (!form.value.handler) return
  submitting.value = true
  try {
    await createReview({
      commit_id: parseInt(commitId),
      handler: form.value.handler,
      note: form.value.note || null
    })
    router.push('/reviews')
  } catch (e) {
    error.value = e.message || '创建失败'
  } finally {
    submitting.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.p-20 { padding: 20px; }
.form-card { max-width: 900px; }
.form-item { display: flex; flex-direction: column; }
.form-item label { font-size: 13px; color: var(--text-secondary); }
.required { color: var(--color-error); }
.form-actions { display: flex; gap: 12px; justify-content: flex-end; }
.commit-meta { display: flex; flex-direction: column; gap: 8px; }
.meta-row { display: flex; gap: 12px; font-size: 14px; }
.meta-label { color: var(--text-tertiary); min-width: 80px; }
.mb-24 { margin-bottom: 24px; }
</style>