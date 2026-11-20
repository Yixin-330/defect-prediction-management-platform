<template>
  <div class="dataset-page">
    <div class="page-header">
      <div>
        <h1 class="page-title">数据集与清洗</h1>
        <p class="page-subtitle">选定仓库 → 采集预览 → 生成数据集（含清洗与特征提取）→ 保存数据版本。</p>
      </div>
      <button class="btn btn-secondary" @click="loadRepos">↻ 刷新仓库</button>
    </div>

    <LoadingState v-if="repoLoading" text="正在加载仓库列表..." />

    <ErrorState v-else-if="repoError" :message="repoError" @retry="loadRepos" />

    <template v-else>
      <div class="card p-20 mt-16">
        <div class="section-title mb-16">选择仓库</div>
        <EmptyState v-if="!repos.length" text="暂无已连接仓库，请先在「仓库接入」页克隆仓库" icon="⬚" />
        <template v-else>
          <select v-model="selectedRepoId" class="repo-select" @change="onRepoChange">
            <option :value="null" disabled>请选择仓库</option>
            <option v-for="r in repos" :key="r.id" :value="r.id">{{ r.name || r.url }}（ID: {{ r.id }}）</option>
          </select>

          <div v-if="previewLoading" class="mt-16">
            <LoadingState text="正在采集提交预览..." />
          </div>
          <div v-else-if="previewError" class="mt-16">
            <ErrorState :message="previewError" @retry="loadPreview" />
          </div>
          <div v-else-if="previewCommits.length" class="mt-16">
            <div class="preview-summary">
              <StatCard label="提交总数" :value="previewCommits.length" />
              <StatCard label="作者数" :value="authorCount" />
              <StatCard label="时间范围" :value="commitTimeRange" />
            </div>
            <div class="section-subtitle mt-16 mb-8">提交预览（前 10 条）</div>
            <table class="data-table">
              <thead>
                <tr><th>提交哈希</th><th>作者</th><th>时间</th><th>信息</th></tr>
              </thead>
              <tbody>
                <tr v-for="c in previewCommits.slice(0, 10)" :key="c.id || c.hash">
                  <td class="mono">{{ (c.hash || '').slice(0, 8) }}</td>
                  <td>{{ c.author || '-' }}</td>
                  <td>{{ formatShortDateTime(c.date || c.committed_at) }}</td>
                  <td class="msg-cell">{{ c.message || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
      </div>

      <div v-if="selectedRepoId" class="card p-20 mt-16">
        <div class="section-title mb-16">生成数据集</div>
        <div class="form-item mb-16">
          <label>数据集名称</label>
          <input v-model="datasetName" type="text" placeholder="default_dataset" class="mt-8" />
          <p class="form-hint mt-8">将执行解析 → SZZ 标注 → 14 维特征提取 → 清洗 → 时间顺序划分，并保存为可追溯的数据版本。</p>
        </div>
        <button class="btn btn-primary" :disabled="generating" @click="handleGenerate">
          {{ generating ? '提交中...' : '生成数据集' }}
        </button>

        <div v-if="taskState" class="task-status mt-16">
          <StatusTag :status="taskStatusKind" />
          <span class="text-sm text-secondary ml-8">{{ taskState.message || taskState.status }}</span>
        </div>
      </div>

      <div class="card p-20 mt-16">
        <div class="table-header">
          <span class="section-title">数据集版本记录</span>
          <span class="text-sm text-secondary">共 {{ datasets.length }} 条 · 本地保存</span>
        </div>
        <EmptyState v-if="!datasets.length" text="暂无数据集记录，生成后将在此展示" icon="📁" />
        <table v-else class="data-table">
          <thead>
            <tr><th>数据集ID</th><th>来源仓库</th><th>状态</th><th>创建时间</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="d in datasets" :key="d.task_id">
              <td class="mono">{{ d.dataset_id || d.task_id.slice(0, 8) }}</td>
              <td>{{ d.repo_name || ('repo#' + d.repo_id) }}</td>
              <td><StatusTag :status="d.status" /></td>
              <td>{{ formatDateTime(d.updated_at) }}</td>
              <td>
                <button class="btn btn-link" @click="removeDataset(d.task_id)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <InfoAlert type="info" class="mt-16">
        清洗前后摘要可在生成完成后查看任务消息；原始数据不变，处理版本按配置可重建。
      </InfoAlert>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import InfoAlert from '@/components/common/InfoAlert.vue'
import StatCard from '@/components/common/StatCard.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { getProjects, getRepoCommits } from '@/api/project'
import { generateDataset } from '@/api/dataset'
import { useTaskPolling } from '@/composables/useTaskPolling'
import { listDatasets, saveDataset, removeDataset } from '@/utils/localStore'
import { formatDateTime, formatShortDateTime } from '@/utils/format'

const repos = ref([])
const repoLoading = ref(true)
const repoError = ref(null)
const selectedRepoId = ref(null)
const previewCommits = ref([])
const previewLoading = ref(false)
const previewError = ref(null)
const datasetName = ref('default_dataset')
const generating = ref(false)
const datasets = ref([])

const { taskState, poll } = useTaskPolling()

const authorCount = computed(() => {
  const set = new Set(previewCommits.value.map(c => c.author).filter(Boolean))
  return set.size
})
const commitTimeRange = computed(() => {
  if (!previewCommits.value.length) return '-'
  const times = previewCommits.value.map(c => c.date || c.committed_at || '').filter(Boolean).sort()
  if (!times.length) return '-'
  return `${formatShortDateTime(times[0])} ~ ${formatShortDateTime(times[times.length - 1])}`
})
const taskStatusKind = computed(() => {
  const s = (taskState.value && taskState.value.status) || ''
  if (s === 'success') return 'done'
  if (s === 'failed' || s === 'error') return 'failed'
  if (s === 'processing' || s === 'pending') return 'reviewing'
  return 'waiting'
})

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

async function loadPreview() {
  if (!selectedRepoId.value) return
  previewLoading.value = true
  previewError.value = null
  try {
    const data = await getRepoCommits(selectedRepoId.value)
    previewCommits.value = data.commits || []
  } catch (e) {
    previewError.value = e.message || '采集预览失败'
  } finally {
    previewLoading.value = false
  }
}

function onRepoChange() {
  previewCommits.value = []
  if (selectedRepoId.value) loadPreview()
}

async function handleGenerate() {
  if (!selectedRepoId.value) return
  generating.value = true
  try {
    const res = await generateDataset({
      repo_id: selectedRepoId.value,
      dataset_name: datasetName.value || 'default_dataset'
    })
    const taskId = res.task_id
    const repo = repos.value.find(r => r.id === selectedRepoId.value)
    saveDataset({
      task_id: taskId,
      repo_id: selectedRepoId.value,
      repo_name: repo ? (repo.name || repo.url) : ('repo#' + selectedRepoId.value),
      dataset_name: datasetName.value,
      status: 'pending'
    })
    datasets.value = listDatasets()
    poll(taskId, (finalState) => {
      const status = (finalState && finalState.status) || 'failed'
      saveDataset({
        task_id: taskId,
        repo_id: selectedRepoId.value,
        repo_name: repo ? (repo.name || repo.url) : ('repo#' + selectedRepoId.value),
        dataset_name: datasetName.value,
        status,
        dataset_id: finalState && finalState.dataset_id
      })
      datasets.value = listDatasets()
    })
  } catch (e) {
    previewError.value = e.message || '生成数据集失败'
  } finally {
    generating.value = false
  }
}

onMounted(() => {
  loadRepos()
  datasets.value = listDatasets()
})
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.p-20 { padding: 20px; }
.repo-select { width: 100%; padding: 8px 12px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); background: var(--bg-input); color: var(--text-primary); font-size: 14px; }
.preview-summary { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
.section-subtitle { font-size: 13px; color: var(--text-secondary); font-weight: 500; }
.data-table { width: 100%; }
.data-table th, .data-table td { padding: 10px 14px; text-align: left; border-bottom: 1px solid var(--border-color); }
.data-table th { font-size: 12px; color: var(--text-tertiary); font-weight: 500; }
.data-table td { font-size: 13px; }
.mono { font-family: ui-monospace, monospace; }
.msg-cell { max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.form-item { display: flex; flex-direction: column; }
.form-item label { font-size: 13px; color: var(--text-secondary); }
.form-hint { font-size: 12px; color: var(--text-tertiary); }
.task-status { display: flex; align-items: center; }
.ml-8 { margin-left: 8px; }
.table-header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 12px; }
.btn-link { background: none; border: none; color: var(--color-error); cursor: pointer; font-size: 13px; }
.mt-16 { margin-top: 16px; }
.mb-16 { margin-bottom: 16px; }
.mb-8 { margin-bottom: 8px; }
</style>