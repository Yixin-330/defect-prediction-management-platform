<template>
  <div class="dashboard">
    <div class="page-header">
      <div>

        <h1 class="page-title">项目工作台</h1>
        <p class="page-subtitle">把有限的审查资源，优先投入值得关注的代码变更。</p>
      </div>
      <router-link to="/commits" class="btn btn-primary">→ 查看提交风险</router-link>
    </div>

    <div class="project-info card mt-24">
      <div class="info-header">
        <span class="info-name">校园协作平台</span>
        <span class="tag" style="background:var(--color-success-bg);color:var(--color-success)">已连接</span>
      </div>
      <div class="info-grid">
        <div class="info-item"><span class="info-label">团队</span><span class="info-value">开发团队 · 4名成员</span></div>
        <div class="info-item"><span class="info-label">仓库</span><span class="info-value">campus-collab · 默认分支 main</span></div>
        <div class="info-item"><span class="info-label">最近同步</span><span class="info-value">今日 10:28 · 已拉取8次提交 · 已预测6次</span></div>
        <div class="info-item"><span class="info-label">同步状态</span><span class="info-value">1次分析中 · 1次预测失败</span></div>
      </div>
      <div class="info-footer">
        <span class="text-secondary">下一步：优先分配高风险审查</span>
        <router-link to="/repo" class="btn btn-secondary">管理仓库</router-link>
      </div>
    </div>

    <div class="grid-4 mt-24">
      <StatCard value="8" label="已同步提交" sub="最近7天 · 6次已完成预测" />
      <StatCard value="2" label="待审查高风险" sub="按风险分数优先安排" danger />
      <StatCard value="2" label="待分配审查任务" sub="张晨、陈思的提交待分配" primary />
      <StatCard value="3/6" label="人工审查完成" sub="已完成预测的提交 · 50%" />
    </div>

    <div class="two-col mt-24">
      <div class="card p-20">
        <div class="flex justify-between items-center mb-16">
          <span class="section-title">优先审查队列</span>
          <router-link to="/commits" class="text-sm">全部提交 →</router-link>
        </div>
        <p class="text-sm text-secondary mb-16">仅包含已完成预测的高风险提交</p>
        <table class="data-table">
          <thead>
            <tr><th>提交摘要/编号</th><th>作者</th><th>风险信号</th><th>状态</th><th>操作</th></tr>
          </thead>
          <tbody>
            <tr v-for="item in priorityQueue" :key="item.id">
              <td><div class="commit-cell"><span class="commit-msg">{{ item.message }}</span><span class="commit-id text-sm text-tertiary">{{ item.id }} · {{ item.branch }}</span></div></td>
              <td>{{ item.author }}</td>
              <td><RiskTag :level="item.level" :score="item.score" show-score /></td>
              <td><StatusTag status="pending" /></td>
              <td><router-link :to="`/commits/${item.id}/arrange`" class="text-sm">安排审查</router-link></td>
            </tr>
          </tbody>
        </table>
        <InfoAlert type="warning" class="mt-16">高风险不等于已确认缺陷。结合变更规模与风险解释，安排同伴审查。</InfoAlert>
      </div>

      <div class="card p-20">
        <div class="section-title mb-8">近期预测风险</div>
        <p class="text-sm text-secondary mb-16">10月03日—10月09日 · 6次已完成预测</p>
        <RiskTrendChart :data="trendData" />
        <div class="trend-legend mt-16">
          <span><i style="background:#ef4444"></i>高风险 2</span>
          <span><i style="background:#f97316"></i>中风险 2</span>
          <span><i style="background:#22c55e"></i>低风险 2</span>
        </div>
      </div>
    </div>

    <div class="card p-20 mt-24">
      <div class="section-title mb-8">从提交到审查闭环</div>
      <p class="text-sm text-secondary mb-16">项目负责人的推荐工作路径</p>
      <div class="grid-4">
        <div v-for="step in workflowSteps" :key="step.title" class="workflow-step">
          <div class="step-title">{{ step.title }} →</div>
          <div class="step-desc text-sm text-secondary">{{ step.desc }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import StatCard from '@/components/common/StatCard.vue'
import RiskTag from '@/components/common/RiskTag.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import InfoAlert from '@/components/common/InfoAlert.vue'
import RiskTrendChart from '@/components/charts/RiskTrendChart.vue'

const priorityQueue = [
  { id: '8f3a2c1', message: '重构任务权限校验', author: '张晨', branch: 'main', score: 0.86, level: 'high' },
  { id: '2bd6e90', message: '新增批量导入功能', author: '陈思', branch: 'main', score: 0.78, level: 'high' }
]

const trendData = [
  { date: '10/03', high: 0, mid: 1, low: 0 },
  { date: '10/04', high: 0, mid: 0, low: 1 },
  { date: '10/05', high: 1, mid: 0, low: 1 },
  { date: '10/06', high: 0, mid: 0, low: 1 },
  { date: '10/07', high: 0, mid: 1, low: 0 },
  { date: '10/09', high: 1, mid: 0, low: 0 }
]

const workflowSteps = [
  { title: '连接仓库', desc: '查看同步与解析状态' },
  { title: '查看提交风险', desc: '筛选、排序并定位变更' },
  { title: '解释与安排审查', desc: '理解风险并分配同伴' },
  { title: '记录处理结果', desc: '关联修复，查看质量趋势' }
]
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.phase-tag { font-size: 12px; color: var(--text-tertiary); margin-bottom: 8px; }
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
.commit-cell { display: flex; flex-direction: column; }
.commit-msg { font-weight: 500; }
.trend-legend { display: flex; gap: 16px; font-size: 12px; color: var(--text-secondary); }
.trend-legend i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 4px; }
.workflow-step { padding: 16px; background-color: var(--bg-page); border-radius: var(--radius-sm); }
.step-title { font-size: 14px; font-weight: 500; color: var(--color-primary); margin-bottom: 4px; }
.step-desc { line-height: 1.5; }
</style>