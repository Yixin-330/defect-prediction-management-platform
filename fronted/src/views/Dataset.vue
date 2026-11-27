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
              <td class="action-cell">
                <button class="btn btn-link btn-view" :disabled="d.status !== 'success'" @click="openView(d)">查看</button>
                <button class="btn btn-link btn-view" :disabled="d.status !== 'success'" @click="handleDownload(d)">下载</button>
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

    <div v-if="viewVisible" class="modal-mask" @click.self="closeView">
      <div class="modal-box">
        <div class="modal-header">
          <span class="modal-title">数据集内容 · {{ viewDataset && (viewDataset.dataset_id || viewDataset.task_id.slice(0, 8)) }}</span>
          <button class="modal-close" @click="closeView">×</button>
        </div>
        <div class="modal-body">
          <LoadingState v-if="viewLoading" text="正在加载数据集内容..." />
          <ErrorState v-else-if="viewError" :message="viewError" />
          <template v-else>
            <div class="modal-meta">
              <StatCard label="样本总数" :value="viewRows.length" />
              <StatCard label="来源仓库" :value="viewDataset && (viewDataset.repo_name || ('repo#' + viewDataset.repo_id))" />
              <StatCard label="生成时间" :value="viewDataset && formatShortDateTime(viewDataset.updated_at)" />
            </div>
            <div class="modal-tip">说明：当前数据集内容来源于该仓库的提交记录（哈希、作者、时间、信息），可作为缺陷预测的原始样本。</div>
            <div class="modal-table-wrap">
              <table class="data-table">
                <thead>
                  <tr><th>提交哈希</th><th>作者</th><th>时间</th><th>信息</th></tr>
                </thead>
                <tbody>
                  <tr v-for="c in viewRows" :key="c.id || c.hash">
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
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="closeView">关闭</button>
          <button class="btn btn-primary" :disabled="viewLoading || !viewRows.length" @click="handleDownload(viewDataset)">下载 CSV</button>
        </div>
      </div>
    </div>
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

const viewVisible = ref(false)
const viewLoading = ref(false)
const viewError = ref(null)
const viewDataset = ref(null)
const viewRows = ref([])

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

async function fetchDatasetRows(d) {
  if (!d || !d.repo_id) throw new Error('该数据集记录缺少来源仓库信息')
  const data = await getRepoCommits(d.repo_id)
  return data.commits || []
}

async function openView(d) {
  viewVisible.value = true
  viewDataset.value = d
  viewLoading.value = true
  viewError.value = null
  viewRows.value = []
  try {
    viewRows.value = await fetchDatasetRows(d)
  } catch (e) {
    viewError.value = e.message || '加载数据集内容失败'
  } finally {
    viewLoading.value = false
  }
}

function closeView() {
  viewVisible.value = false
  viewDataset.value = null
  viewRows.value = []
  viewError.value = null
}

function buildCsv(rows) {
  const headers = ['hash', 'author', 'date', 'message']
  const escape = (v) => {
    const s = String(v == null ? '' : v)
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
  }
  const lines = [headers.join(',')]
  for (const r of rows) {
    lines.push([
      escape(r.hash),
      escape(r.author),
      escape(r.date || r.committed_at),
      escape(r.message)
    ].join(','))
  }
  return lines.join('\n')
}

function triggerCsvDownload(filename, rows) {
  const csv = buildCsv(rows)
  const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

async function handleDownload(d) {
  if (!d) return
  try {
    const rows = viewVisible.value && viewDataset.value && viewDataset.value.task_id === d.task_id
      ? viewRows.value
      : await fetchDatasetRows(d)
    if (!rows.length) {
      previewError.value = '该数据集暂无可下载的内容'
      return
    }
    const name = (d.dataset_id || d.task_id.slice(0, 8)) + '.csv'
    triggerCsvDownload(name, rows)
  } catch (e) {
    previewError.value = e.message || '下载数据集失败'
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
.action-cell { display: flex; gap: 12px; align-items: center; }
.btn-view { color: var(--color-primary, #4c8dff); }
.btn-view:disabled { color: var(--text-tertiary); cursor: not-allowed; opacity: 0.6; }
.mt-16 { margin-top: 16px; }
.mb-16 { margin-bottom: 16px; }
.mb-8 { margin-bottom: 8px; }

.modal-mask { position: fixed; inset: 0; background: rgba(0,0,0,0.55); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-box { width: 820px; max-width: 92vw; max-height: 86vh; display: flex; flex-direction: column; background: var(--bg-card, #1e2330); border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; }
.modal-header { display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; border-bottom: 1px solid var(--border-color); }
.modal-title { font-size: 15px; color: var(--text-primary); font-weight: 600; }
.modal-close { background: none; border: none; color: var(--text-secondary); font-size: 22px; cursor: pointer; line-height: 1; }
.modal-body { padding: 16px 20px; overflow: auto; flex: 1; }
.modal-meta { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 12px; }
.modal-tip { font-size: 12px; color: var(--text-tertiary); margin-bottom: 12px; }
.modal-table-wrap { max-height: 360px; overflow: auto; border: 1px solid var(--border-color); border-radius: 4px; }
.modal-footer { display: flex; justify-content: flex-end; gap: 10px; padding: 12px 20px; border-top: 1px solid var(--border-color); }
</style>