<template>
  <div class="dashboard">
    <div class="page-header">
      <div>
        <h1 class="page-title">项目工作台</h1>
        <p class="page-subtitle">把有限的审查资源，优先投入值得关注的代码变更。</p>
      </div>
      <router-link to="/commits" class="btn btn-primary">→ 查看提交风险</router-link>
    </div>

    <LoadingState v-if="loading" text="正在加载看板数据..." />

    <ErrorState v-else-if="error" :message="error" @retry="loadData" />

    <template v-else>
      <div class="project-info card mt-24">
        <div class="info-header">
          <span class="info-name">{{ project?.name || '未选择项目' }}</span>
          <span class="tag" style="background:var(--color-success-bg);color:var(--color-success)">已连接</span>
        </div>
        <div class="info-grid">
          <div class="info-item"><span class="info-label">团队</span><span class="info-value">{{ project?.owner || '开发团队' }}</span></div>
          <div class="info-item"><span class="info-label">仓库</span><span class="info-value">{{ project?.git_url || '-' }}</span></div>
          <div class="info-item"><span class="info-label">总提交数</span><span class="info-value">{{ summary.total_commits || 0 }}</span></div>
          <div class="info-item"><span class="info-label">高风险提交</span><span class="info-value">{{ summary.high_risk_commits || 0 }}</span></div>
        </div>
        <div class="info-footer">
          <span class="text-secondary">下一步：优先分配高风险审查</span>
          <router-link to="/repo" class="btn btn-secondary">管理仓库</router-link>
        </div>
      </div>

      <div class="grid-4 mt-24">
        <StatCard :value="summary.total_commits || 0" label="已同步提交" :sub="`总仓库 ${summary.total_repos || 0}`" />
        <StatCard :value="summary.high_risk_commits || 0" label="高风险提交" sub="按风险分数优先安排" danger />
        <StatCard :value="summary.total_projects || 0" label="项目总数" sub="开发团队" primary />
        <StatCard :value="summary.abnormal_commits || 0" label="异常提交" sub="低信息量提交" />
      </div>

      <div class="two-col mt-24">
        <div class="card p-20">
          <div class="flex justify-between items-center mb-16">
            <span class="section-title">优先审查队列</span>
            <router-link to="/commits" class="text-sm">全部提交 →</router-link>
          </div>
          <p class="text-sm text-secondary mb-16">按风险分数降序排列</p>
          <EmptyState v-if="!rankingItems.length" text="暂无预测数据" icon="📭" />
          <table v-else class="data-table">
            <thead>
              <tr><th>提交ID</th><th>风险信号</th><th>操作</th></tr>
            </thead>
            <tbody>
              <tr v-for="item in rankingItems" :key="item.commit_id">
                <td>{{ item.commit_hash }}</td>
                <td><RiskTag :level="levelFromBackend(item.level)" :score="item.risk_score" show-score /></td>
                <td><router-link :to="`/commits/${item.commit_id}`" class="text-sm">查看详情</router-link></td>
              </tr>
            </tbody>
          </table>
          <InfoAlert type="warning" class="mt-16">高风险不等于已确认缺陷。结合变更规模与风险解释，安排同伴审查。</InfoAlert>
        </div>

        <div class="card p-20">
          <div class="section-title mb-8">近期风险趋势</div>
          <p class="text-sm text-secondary mb-16">基于历史预测数据</p>
          <RiskTrendChart :data="trendData" />
        </div>
      </div>

      <div class="card p-20 mt-24">
        <div class="section-title mb-8">从提交到审查闭环</div>
        <p class="text-sm text-secondary mb-16">推荐工作路径</p>
        <div class="grid-4">
          <div v-for="step in workflowSteps" :key="step.title" class="workflow-step">
            <div class="step-title">{{ step.title }} →</div>
            <div class="step-desc text-sm text-secondary">{{ step.desc }}</div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import StatCard from '@/components/common/StatCard.vue'
import RiskTag from '@/components/common/RiskTag.vue'
import InfoAlert from '@/components/common/InfoAlert.vue'
import LoadingState from '@/components/common/LoadingState.vue'
import ErrorState from '@/components/common/ErrorState.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import RiskTrendChart from '@/components/charts/RiskTrendChart.vue'
import { getDashboardSummary, getProjects, getRiskRanking } from '@/api/project'
import { levelFromBackend, buildTrendFromCommits } from '@/utils/format'

const loading = ref(true)
const error = ref(null)
const summary = ref({})
const project = ref(null)
const rankingItems = ref([])

const trendData = ref([])

const workflowSteps = [
  { title: '连接仓库', desc: '查看同步与解析状态' },
  { title: '查看提交风险', desc: '筛选、排序并定位变更' },
  { title: '解释与安排审查', desc: '理解风险并分配同伴' },
  { title: '记录处理结果', desc: '关联修复，查看质量趋势' }
]

async function loadData() {
  loading.value = true
  error.value = null
  try {
    const [summaryRes, projectsRes] = await Promise.all([
      getDashboardSummary(),
      getProjects()
    ])
    summary.value = summaryRes
    const projects = projectsRes || []
    project.value = projects[0] || null

    if (project.value) {
      const ranking = await getRiskRanking(project.value.id)
      rankingItems.value = ranking.items || []
    }

    trendData.value = buildTrendFromCommits(summaryRes.recent_commits)
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
.project-info { padding: 20px; }
.info-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.info-name { font-size: 18px; font-weight: 600; }
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.info-item { display: flex; flex-direction: column; gap: 4px; }
.info-label { font-size: 12px; color: var(--text-tertiary); }
.info-value { font-size: 14px; color: var(--text-primary); }
.info-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border-color); }
.two-col { display: grid; grid-template-columns: 1.5fr 1fr; gap: 16px; }
.p-20 { padding: 20px; }
.data-table th, .data-table td { padding: 12px 8px; text-align: left; border-bottom: 1px solid var(--border-color); }
.data-table th { font-size: 12px; color: var(--text-tertiary); font-weight: 500; }
.data-table td { font-size: 14px; }
.data-table tbody tr:hover { background-color: var(--bg-table-hover); }
.workflow-step { padding: 16px; background-color: var(--bg-page); border-radius: var(--radius-sm); }
.step-title { font-size: 14px; font-weight: 500; color: var(--color-primary); margin-bottom: 4px; }
.step-desc { line-height: 1.5; }
</style>