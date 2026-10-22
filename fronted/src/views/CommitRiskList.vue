<template>
  <div class="commit-list">
    <div class="page-header">
      <div>
        <h1 class="page-title">提交风险列表</h1>
        <p class="page-subtitle">优先查看已完成预测的高风险变更；分析中与失败项不参与风险排序。</p>
      </div>
      <button class="btn btn-secondary" @click="handleSync">↻ 同步最新提交</button>
    </div>

    <div class="stat-tabs mt-16">
      <button v-for="tab in statTabs" :key="tab.key" class="stat-tab" :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key">
        {{ tab.label }} <span :class="`tab-count ${tab.color}`">{{ tab.count }}</span>
      </button>
    </div>

    <div class="card filter-panel mt-16">
      <div class="filter-row">
        <input v-model="filters.search" placeholder="搜索提交…" class="filter-search" />
        <select v-model="filters.date"><option>10月03日—10月09日</option></select>
        <select v-model="filters.author"><option>全部作者</option><option>张晨</option><option>陈思</option><option>林悦</option><option>王浩</option></select>
        <select v-model="filters.branch"><option>全部分支</option><option>main</option><option>dev</option></select>
        <select v-model="filters.risk"><option>风险：全部</option><option>高风险</option><option>中风险</option><option>低风险</option></select>
        <select v-model="filters.reviewStatus"><option>审查状态：全部</option><option>待分配</option><option>审查中</option><option>已完成</option></select>
        <select v-model="filters.predictStatus"><option>预测状态：全部</option><option>已完成</option><option>分析中</option><option>预测失败</option></select>
        <button class="btn btn-primary">应用筛选</button>
        <button class="btn btn-text">重置</button>
      </div>
    </div>

    <div class="card mt-16">
      <div class="table-header">
        <span class="section-title">提交队列</span>
        <span class="text-sm text-secondary">排序：风险分数 ↓</span>
      </div>
      <table class="data-table">
        <thead>
          <tr>
            <th style="width:60px">优先级</th>
            <th>提交摘要 / ID</th>
            <th>作者 / 时间</th>
            <th>分支</th>
            <th>风险 / 分数</th>
            <th>预测状态</th>
            <th>审查状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in tableData" :key="row.id" :class="{ 'row-priority': row.priority === '优先' }">
            <td><span class="priority-tag" :class="row.priority === '优先' ? 'p-high' : 'p-normal'">{{ row.priority }}</span></td>
            <td><div class="commit-cell"><span class="commit-msg">{{ row.message }}</span><span class="commit-id text-sm text-tertiary">{{ row.id }}</span></div></td>
            <td><div class="commit-cell"><span>{{ row.author }}</span><span class="text-sm text-tertiary">{{ row.time }}</span></div></td>
            <td>{{ row.branch }}</td>
            <td><RiskTag v-if="row.score != null" :level="row.level" :score="row.score" show-score /><span v-else class="text-tertiary">— 无评分</span></td>
            <td><StatusTag type="predict" :status="row.predictStatus" /></td>
            <td><StatusTag :status="row.reviewStatus" /></td>
            <td><a class="text-sm" @click="handleAction(row)">{{ row.action }}</a></td>
          </tr>
        </tbody>
      </table>
      <div class="pagination">
        <span class="text-sm text-secondary">共{{ tableData.length }}条 · 每页10条 · 未评分项置于末尾</span>
        <div class="page-btns">
          <button class="btn btn-secondary" disabled>上一页</button>
          <button class="btn btn-primary">1</button>
          <button class="btn btn-secondary">下一页</button>
        </div>
      </div>
    </div>

    <InfoAlert type="info" class="mt-16">示例分级：高风险 ≥ 0.70，中风险 0.40–0.69，低风险 &lt; 0.40。阈值仅用于展示，不代表经过实际项目验证。</InfoAlert>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import RiskTag from '@/components/common/RiskTag.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import InfoAlert from '@/components/common/InfoAlert.vue'

const router = useRouter()
const activeTab = ref('all')
const filters = ref({ search: '', date: '', author: '', branch: '', risk: '', reviewStatus: '', predictStatus: '' })

const statTabs = [
  { key: 'all', label: '全部提交', count: 8, color: '' },
  { key: 'high', label: '高风险', count: 2, color: 'c-high' },
  { key: 'mid', label: '中风险', count: 2, color: 'c-mid' },
  { key: 'low', label: '低风险', count: 2, color: 'c-low' },
  { key: 'analyzing', label: '分析中', count: 1, color: 'c-gray' },
  { key: 'failed', label: '预测失败', count: 1, color: 'c-gray' }
]

const tableData = ref([
  { priority: '优先', message: '重构任务权限校验', id: '8f3a2c1', author: '张晨', time: '10/09 09:42', branch: 'main', score: 0.86, level: 'high', predictStatus: 'completed', reviewStatus: 'pending', action: '查看详情' },
  { priority: '优先', message: '新增批量导入功能', id: '2bd6e90', author: '陈思', time: '10/05 16:10', branch: 'main', score: 0.78, level: 'high', predictStatus: 'completed', reviewStatus: 'pending', action: '查看详情' },
  { priority: '常规', message: '调整成员邀请逻辑', id: '7c91b42', author: '林悦', time: '10/03 14:22', branch: 'main', score: 0.54, level: 'mid', predictStatus: 'completed', reviewStatus: 'reviewing', action: '查看详情' },
  { priority: '常规', message: '完善任务筛选条件', id: '6a4d812', author: '王浩', time: '10/07 11:35', branch: 'main', score: 0.46, level: 'mid', predictStatus: 'completed', reviewStatus: 'done', action: '查看记录' },
  { priority: '常规', message: '更新项目说明文档', id: '3e82f10', author: '张晨', time: '10/06 10:20', branch: 'main', score: 0.18, level: 'low', predictStatus: 'completed', reviewStatus: 'done', action: '查看记录' },
  { priority: '常规', message: '修正页面空状态文案', id: '5d10a77', author: '陈思', time: '10/05 09:18', branch: 'main', score: 0.12, level: 'low', predictStatus: 'completed', reviewStatus: 'done', action: '查看记录' },
  { priority: '—', message: '优化任务搜索接口', id: '9a0c5d2', author: '王浩', time: '10/09 10:12', branch: 'dev', score: null, level: 'none', predictStatus: 'analyzing', reviewStatus: 'pending', action: '查看进度' },
  { priority: '—', message: '新增附件预览', id: '4f7b009', author: '林悦', time: '10/08 15:06', branch: 'dev', score: null, level: 'none', predictStatus: 'failed', reviewStatus: 'pending', action: '重新预测' }
])

function handleSync() {}
function handleAction(row) {
  if (row.action === '查看详情') router.push(`/commits/${row.id}`)
  else if (row.action === '查看记录') router.push(`/reviews/${row.id}`)
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.stat-tabs { display: flex; gap: 8px; flex-wrap: wrap; }
.stat-tab { padding: 8px 16px; border-radius: var(--radius-sm); background-color: var(--bg-card); border: 1px solid var(--border-color); color: var(--text-secondary); font-size: 14px; display: flex; align-items: center; gap: 6px; }
.stat-tab.active { background-color: var(--color-primary-bg); border-color: var(--color-primary); color: var(--text-primary); }
.tab-count { font-weight: 600; }
.c-high { color: var(--color-high-risk); }
.c-mid { color: var(--color-mid-risk); }
.c-low { color: var(--color-low-risk); }
.c-gray { color: var(--text-tertiary); }
.filter-panel { padding: 16px; }
.filter-row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
.filter-search { flex: 1; min-width: 200px; }
.filter-row select { min-width: 120px; }
.table-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--border-color); }
.data-table { width: 100%; }
.data-table th, .data-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border-color); }
.data-table th { font-size: 12px; color: var(--text-tertiary); font-weight: 500; }
.data-table td { font-size: 14px; }
.data-table tbody tr:hover { background-color: var(--bg-table-hover); }
.row-priority { background-color: var(--bg-table-highlight); }
.priority-tag { font-size: 12px; padding: 2px 8px; border-radius: 4px; }
.p-high { background-color: var(--color-high-risk-bg); color: var(--color-high-risk); }
.p-normal { background-color: var(--bg-tag); color: var(--text-secondary); }
.commit-cell { display: flex; flex-direction: column; }
.commit-msg { font-weight: 500; }
.pagination { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; }
.page-btns { display: flex; gap: 8px; }
</style>