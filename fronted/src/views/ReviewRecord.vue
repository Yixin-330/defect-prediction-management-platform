<template>
  <div class="review-record">
    <div class="page-header">
      <div>
        <h1 class="page-title">审查处理记录</h1>
        <p class="page-subtitle">查看所有审查记录与处理状态</p>
      </div>
      <div class="filter-bar">
        <select v-model="projectFilter" @change="loadData" class="filter-select">
          <option value="">全部项目</option>
          <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
        <select v-model="statusFilter" @change="loadData" class="filter-select">
          <option value="">全部状态</option>
          <option value="待审查">待审查</option>
          <option value="处理中">处理中</option>
          <option value="已处理">已处理</option>
          <option value="已忽略">已忽略</option>
        </select>
      </div>
    </div>

    <LoadingState v-if="loading" text="正在加载审查记录..." />

    <ErrorState v-else-if="error" :message="error" @retry="loadData" />

    <template v-else>
      <div class="card mt-16">
        <EmptyState v-if="!reviews.length" text="暂无审查记录" icon="📭" />
        <div v-if="!reviews.length" class="empty-guide mt-16">
          <p class="text-sm text-secondary mb-8">审查记录需要手动创建，请按以下步骤操作：</p>
          <router-link to="/commits" class="btn btn-primary">前往提交风险列表 → 安排审查</router-link>
        </div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>审查ID</th>
              <th>提交ID</th>
              <th>状态</th>
              <th>处理人</th>
              <th>风险分数</th>
              <th>备注</th>
              <th>创建时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in reviews" :key="r.id">
              <td>{{ r.id }}</td>
              <td>{{ r.commit_id }}</td>
              <td><span class="tag" :style="statusStyle(r.status)">{{ r.status }}</span></td>
              <td>{{ r.handler || '-' }}</td>
              <td>{{ r.risk_score_at_creation?.toFixed(2) || '-' }}</td>
              <td>{{ r.note || '-' }}</td>
              <td>{{ formatDateTime(r.created_at) }}</td>
              <td>
                <button v-if="r.status === '待审查'" class="btn btn-text" @click="updateStatus(r, '处理中')">开始处理</button>
                <button v-if="r.status === '处理中'" class="btn btn-text" @click="updateStatus(r, '已处理')">标记完成</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import { getReviews, updateReview } from '@/api/review'
import { getProjects, getRiskRanking } from '@/api/project'
import { formatDateTime } from '@/utils/format'

const loading = ref(true)
const error = ref(null)
const reviews = ref([])
const allReviews = ref([])
const projects = ref([])
const statusFilter = ref('')
const projectFilter = ref('')
const projectCommitIds = ref(new Set())

function statusStyle(status) {
  const map = {
    '待审查': { background: 'var(--color-info-bg)', color: 'var(--color-info)' },
    '处理中': { background: 'var(--color-warning-bg)', color: 'var(--color-warning)' },
    '已处理': { background: 'var(--color-success-bg)', color: 'var(--color-success)' },
    '已忽略': { background: 'var(--bg-tag)', color: 'var(--text-tertiary)' }
  }
  return map[status] || {}
}

async function loadData() {
  loading.value = true
  error.value = null
  try {
    if (projects.value.length === 0) {
      projects.value = await getProjects() || []
    }

    if (projectFilter.value) {
      try {
        const ranking = await getRiskRanking(projectFilter.value)
        projectCommitIds.value = new Set((ranking.items || []).map(i => i.commit_id))
      } catch (e) {
        projectCommitIds.value = new Set()
      }
    } else {
      projectCommitIds.value = new Set()
    }

    const params = statusFilter.value ? { status: statusFilter.value } : {}
    try {
      allReviews.value = await getReviews(params) || []
    } catch (e) {
      if (e.code === 500) {
        allReviews.value = []
      } else {
        throw e
      }
    }

    reviews.value = projectFilter.value
      ? allReviews.value.filter(r => projectCommitIds.value.has(r.commit_id))
      : allReviews.value
  } catch (e) {
    error.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

async function updateStatus(review, newStatus) {
  try {
    await updateReview(review.id, { status: newStatus })
    loadData()
  } catch (e) {
    error.value = e.message || '操作失败'
  }
}

onMounted(loadData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.filter-bar { display: flex; gap: 12px; }
.filter-select { min-width: 120px; padding: 8px 12px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); background: var(--bg-input); color: var(--text-primary); font-size: 14px; }
.data-table { width: 100%; }
.data-table th, .data-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border-color); }
.data-table th { font-size: 12px; color: var(--text-tertiary); font-weight: 500; }
.data-table td { font-size: 14px; }
.data-table tbody tr:hover { background-color: var(--bg-table-hover); }
.empty-guide { text-align: center; padding: 16px; }
.mb-8 { margin-bottom: 8px; }
</style>