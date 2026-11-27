<template>
  <div class="model-train-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">训练与模型库</h1>
        <p class="page-subtitle">选择数据集 → 配置训练/验证/测试划分 → 训练逻辑回归 → 查看评估指标与模型库。</p>
      </div>
    </div>

    <div class="card p-20 mt-16">
      <div class="section-title mb-16">训练配置</div>
      <EmptyState v-if="!datasets.length" text="暂无可用数据集，请先在「数据集与清洗」页生成" icon="📁" />
      <template v-else>
        <div class="form-grid">
          <div class="form-item">
            <label>数据集版本 <span class="required">*</span></label>
            <select v-model="form.dataset_id" class="mt-8">
              <option value="" disabled>请选择数据集</option>
              <option v-for="d in datasets" :key="d.dataset_id || d.task_id" :value="d.dataset_id || d.task_id">
                {{ d.dataset_id || d.task_id.slice(0, 8) }}（{{ d.repo_name || '未知仓库' }}）
              </option>
            </select>
          </div>
          <div class="form-item">
            <label>模型类型</label>
            <select v-model="form.model_type" class="mt-8">
              <option value="logistic_regression">逻辑回归（Logistic Regression）</option>
            </select>
            <p class="form-hint mt-8">首版交付逻辑回归基线；八模型对比属课程交付范围。</p>
          </div>
        </div>

        <div class="section-subtitle mt-16 mb-8">数据集划分比例（按时间顺序，测试集整体晚于训练集）</div>
        <div class="ratio-row">
          <div class="ratio-item">
            <label>训练集</label>
            <input v-model.number="form.train_ratio" type="number" step="0.05" min="0" max="1" />
          </div>
          <div class="ratio-item">
            <label>验证集</label>
            <input v-model.number="form.val_ratio" type="number" step="0.05" min="0" max="1" />
          </div>
          <div class="ratio-item">
            <label>测试集</label>
            <input v-model.number="form.test_ratio" type="number" step="0.05" min="0" max="1" />
          </div>
          <div class="ratio-total" :class="{ invalid: !ratioValid }">
            合计：{{ ratioSum.toFixed(2) }} {{ ratioValid ? '✓' : '✗（须等于 1.0）' }}
          </div>
        </div>

        <button class="btn btn-primary mt-16" :disabled="!ratioValid || !form.dataset_id || training" @click="handleTrain">
          {{ training ? '提交中...' : '开始训练' }}
        </button>

        <div v-if="taskState" class="task-status mt-16">
          <StatusTag :status="taskStatusKind" />
          <span class="text-sm text-secondary ml-8">{{ taskState.message || taskState.status }}</span>
        </div>

        <div v-if="lastMetrics" class="metrics-card mt-16">
          <div class="section-subtitle mb-8">评估指标（验证集）</div>
          <div class="metrics-grid">
            <StatCard label="准确率" :value="fmtMetric(lastMetrics.accuracy)" />
            <StatCard label="F1" :value="fmtMetric(lastMetrics.f1_score)" />
            <StatCard label="AUC" :value="fmtMetric(lastMetrics.auc)" />
          </div>
          <InfoAlert type="info" class="mt-8">指标基于开源项目历史数据，需通过课程项目试用进一步验证。</InfoAlert>
        </div>
      </template>
    </div>

    <div class="card p-20 mt-16">
      <div class="table-header">
        <span class="section-title">模型库</span>
        <span class="text-sm text-secondary">共 {{ models.length }} 条 · 本地保存</span>
      </div>
      <EmptyState v-if="!models.length" text="暂无模型记录，训练完成后将在此展示" icon="🤖" />
      <table v-else class="data-table">
        <thead>
          <tr><th>模型ID</th><th>类型</th><th>数据集</th><th>状态</th><th>训练时间</th><th>操作</th></tr>
        </thead>
        <tbody>
          <tr v-for="m in models" :key="m.task_id">
            <td class="mono">{{ m.model_id || m.task_id.slice(0, 8) }}</td>
            <td>{{ m.model_type || 'logistic_regression' }}</td>
            <td class="mono">{{ (m.dataset_id || '').slice(0, 12) }}</td>
            <td><StatusTag :status="m.status" /></td>
            <td>{{ formatDateTime(m.updated_at) }}</td>
            <td class="action-cell">
              <button class="btn btn-link btn-view" @click="openView(m)">查看</button>
              <button class="btn btn-link" @click="removeModel(m.task_id)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="viewVisible" class="modal-mask" @click.self="closeView">
      <div class="modal-box">
        <div class="modal-header">
          <span class="modal-title">模型详情 · {{ viewModel && (viewModel.model_id || viewModel.task_id.slice(0, 8)) }}</span>
          <button class="modal-close" @click="closeView">×</button>
        </div>
        <div class="modal-body" v-if="viewModel">
          <div class="meta-grid">
            <StatCard label="模型ID" :value="viewModel.model_id || viewModel.task_id.slice(0, 8)" />
            <StatCard label="模型类型" :value="viewModel.model_type || 'logistic_regression'" />
            <StatCard label="数据集" :value="(viewModel.dataset_id || '').slice(0, 12) || '-'" />
            <StatCard label="状态" :value="viewModel.status || '-'" />
            <StatCard label="训练时间" :value="formatShortDateTime(viewModel.updated_at)" />
          </div>

          <div class="section-subtitle mt-16 mb-8">评估指标</div>
          <div v-if="viewModel.metrics" class="metrics-grid">
            <StatCard label="准确率" :value="fmtMetric(viewModel.metrics.accuracy)" />
            <StatCard label="F1" :value="fmtMetric(viewModel.metrics.f1_score)" />
            <StatCard label="AUC" :value="fmtMetric(viewModel.metrics.auc)" />
          </div>
          <EmptyState v-else text="该模型暂无评估指标（可能训练未完成）" icon="📊" />

          <div class="section-subtitle mt-16 mb-8">训练配置</div>
          <div class="config-row">
            <div class="config-item"><span class="config-label">训练集比例</span><span class="config-value">{{ fmtRatio(viewModel.train_ratio) }}</span></div>
            <div class="config-item"><span class="config-label">验证集比例</span><span class="config-value">{{ fmtRatio(viewModel.val_ratio) }}</span></div>
            <div class="config-item"><span class="config-label">测试集比例</span><span class="config-value">{{ fmtRatio(viewModel.test_ratio) }}</span></div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeView">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import EmptyState from '@/components/common/EmptyState.vue'
import InfoAlert from '@/components/common/InfoAlert.vue'
import StatCard from '@/components/common/StatCard.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { trainModel } from '@/api/model'
import { useTaskPolling } from '@/composables/useTaskPolling'
import { listDatasets, listModels, saveModel, removeModel } from '@/utils/localStore'
import { formatDateTime, formatShortDateTime } from '@/utils/format'

const datasets = ref([])
const models = ref([])
const training = ref(false)
const lastMetrics = ref(null)
const viewVisible = ref(false)
const viewModel = ref(null)
const form = ref({
  dataset_id: '',
  model_type: 'logistic_regression',
  train_ratio: 0.7,
  val_ratio: 0.15,
  test_ratio: 0.15
})

const { taskState, poll } = useTaskPolling()

const ratioSum = computed(() => (form.value.train_ratio || 0) + (form.value.val_ratio || 0) + (form.value.test_ratio || 0))
const ratioValid = computed(() => Math.abs(ratioSum.value - 1.0) < 0.001)
const taskStatusKind = computed(() => {
  const s = (taskState.value && taskState.value.status) || ''
  if (s === 'success') return 'done'
  if (s === 'failed' || s === 'error') return 'failed'
  if (s === 'processing' || s === 'pending') return 'reviewing'
  return 'waiting'
})

function fmtMetric(v) {
  if (v == null || isNaN(v)) return '-'
  return Number(v).toFixed(4)
}

function fmtRatio(v) {
  if (v == null || isNaN(v)) return '-'
  return Number(v).toFixed(2)
}

function openView(m) {
  viewModel.value = m
  viewVisible.value = true
}

function closeView() {
  viewVisible.value = false
  viewModel.value = null
}

async function handleTrain() {
  training.value = true
  lastMetrics.value = null
  try {
    const res = await trainModel({
      dataset_id: form.value.dataset_id,
      model_type: form.value.model_type,
      train_ratio: form.value.train_ratio,
      val_ratio: form.value.val_ratio,
      test_ratio: form.value.test_ratio
    })
    const taskId = res.task_id
    saveModel({
      task_id: taskId,
      dataset_id: form.value.dataset_id,
      model_type: form.value.model_type,
      train_ratio: form.value.train_ratio,
      val_ratio: form.value.val_ratio,
      test_ratio: form.value.test_ratio,
      status: 'pending'
    })
    models.value = listModels()
    poll(taskId, (finalState) => {
      const status = (finalState && finalState.status) || 'failed'
      saveModel({
        task_id: taskId,
        dataset_id: form.value.dataset_id,
        model_type: form.value.model_type,
        train_ratio: form.value.train_ratio,
        val_ratio: form.value.val_ratio,
        test_ratio: form.value.test_ratio,
        status,
        model_id: finalState && finalState.model_id,
        metrics: finalState && finalState.metrics
      })
      models.value = listModels()
      if (finalState && finalState.metrics) lastMetrics.value = finalState.metrics
    })
  } catch (e) {
    lastMetrics.value = null
    taskState.value = { status: 'failed', message: (e && e.message) || '训练提交失败' }
  } finally {
    training.value = false
  }
}

onMounted(() => {
  datasets.value = listDatasets().filter(d => d.status === 'success')
  models.value = listModels()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.p-20 { padding: 20px; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-item { display: flex; flex-direction: column; }
.form-item label { font-size: 13px; color: var(--text-secondary); }
.required { color: var(--color-error); }
.form-hint { font-size: 12px; color: var(--text-tertiary); }
select, input { padding: 8px 12px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); background: var(--bg-input); color: var(--text-primary); font-size: 14px; }
.section-subtitle { font-size: 13px; color: var(--text-secondary); font-weight: 500; }
.ratio-row { display: flex; gap: 16px; align-items: flex-end; flex-wrap: wrap; }
.ratio-item { display: flex; flex-direction: column; gap: 4px; }
.ratio-item label { font-size: 12px; color: var(--text-tertiary); }
.ratio-item input { width: 100px; }
.ratio-total { font-size: 13px; color: var(--text-secondary); padding-bottom: 8px; }
.ratio-total.invalid { color: var(--color-error); }
.task-status { display: flex; align-items: center; }
.ml-8 { margin-left: 8px; }
.metrics-card { padding: 16px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); background: var(--bg-card-hover); }
.metrics-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.table-header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 12px; }
.data-table { width: 100%; }
.data-table th, .data-table td { padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border-color); }
.data-table th { font-size: 12px; color: var(--text-tertiary); font-weight: 500; }
.data-table td { font-size: 13px; }
.mono { font-family: ui-monospace, monospace; }
.btn-link { background: none; border: none; color: var(--color-error); cursor: pointer; font-size: 13px; }
.action-cell { display: flex; gap: 12px; align-items: center; }
.btn-view { color: var(--color-primary, #4c8dff); }
.mt-16 { margin-top: 16px; }
.mt-8 { margin-top: 8px; }
.mb-16 { margin-bottom: 16px; }
.mb-8 { margin-bottom: 8px; }

.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.55); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-box { width: 640px; max-width: 92vw; max-height: 86vh; display: flex; flex-direction: column; background: var(--bg-card, #1e2330); border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; border-bottom: 1px solid var(--border-color); }
.modal-title { font-size: 15px; color: var(--text-primary); font-weight: 600; }
.modal-close { background: none; border: none; color: var(--text-secondary); font-size: 22px; cursor: pointer; line-height: 1; }
.modal-body { padding: 16px 20px; overflow: auto; flex: 1; }
.meta-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.config-row { display: flex; gap: 24px; flex-wrap: wrap; }
.config-item { display: flex; flex-direction: column; gap: 4px; }
.config-label { font-size: 12px; color: var(--text-tertiary); }
.config-value { font-size: 14px; color: var(--text-primary); font-family: ui-monospace, monospace; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 12px 20px; border-top: 1px solid var(--border-color); }
</style>