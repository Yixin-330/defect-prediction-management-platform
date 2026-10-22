<template>
  <div class="review-record">
    <div class="page-header">
      <div>
        <h1 class="page-title">审查处理记录</h1>
        <p class="page-subtitle">查看所有审查记录与处理状态</p>
      </div>
      <div class="filter-bar">
        <select v-model="statusFilter" @change="loadData">
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
import { formatDateTime } from '@/utils/format'

const loading = ref(true)
const error = ref(null)
const reviews = ref([])
const statusFilter = ref('')

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
    const params = statusFilter.value ? { status: statusFilter.value } : {}
    reviews.value = await getReviews(params) || []
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
.filter-bar select { min-width: 120px; }
.data-table { width: 100%; }
.data-table th, .data-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border-color); }
.data-table th { font-size: 12px; color: var(--text-tertiary); font-weight: 500; }
.data-table td { font-size: 14px; }
.data-table tbody tr:hover { background-color: var(--bg-table-hover); }
</style>