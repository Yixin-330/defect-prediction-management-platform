<template>
  <div class="quality-trend">
    <div class="page-header">
      <div>

        <h1 class="page-title">项目质量趋势</h1>
      </div>
      <router-link to="/" class="btn btn-secondary">返回项目工作台</router-link>
    </div>

    <div class="filter-bar mt-16">
      <select v-model="filters.project"><option>校园协作平台</option></select>
      <select v-model="filters.date"><option>10月03日—10月10日</option></select>
      <span class="tag" style="background:var(--bg-tag);color:var(--text-secondary)">最近8天</span>
      <span class="text-sm text-secondary">分支：main</span>
    </div>

    <div class="grid-4 mt-16">
      <StatCard value="9/7" label="提交 / 已完成预测" sub="含1次修复提交" />
      <StatCard value="28.6%" label="高风险占比" sub="2/7 已完成预测" danger />
      <StatCard value="4/6" label="审查完成" sub="含1项审查中" primary />
      <StatCard value="1" label="人工确认问题" sub="已修复并复核" />
    </div>

    <div class="two-col mt-24">
      <div class="card p-20">
        <div class="section-title mb-8">提交风险分布与时间趋势</div>
        <div class="legend mb-16">
          <span><i style="background:#ef4444"></i>高风险</span>
          <span><i style="background:#f97316"></i>中风险</span>
          <span><i style="background:#22c55e"></i>低风险</span>
        </div>
        <RiskTrendChart :data="trendData" />
        <p class="text-sm text-tertiary mt-16">10月10日新增低风险修复提交（a19b730），修复了10/09的高风险提交中的权限缓存问题。</p>
      </div>

      <div class="card p-20">
        <div class="section-title mb-16">审查任务完成状况</div>
        <div class="progress-list">
          <div v-for="p in progressItems" :key="p.label" class="progress-item">
            <div class="flex justify-between mb-8">
              <span class="text-sm">{{ p.label }}</span>
              <span class="text-sm text-secondary">{{ p.count }}项</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: p.percent + '%', background: p.color }"></div>
            </div>
          </div>
        </div>
        <router-link to="/reviews" class="btn btn-secondary mt-16" style="width:100%;justify-content:center">查看审查处理记录</router-link>
      </div>
    </div>

    <div class="card p-20 mt-24">
      <div class="section-title mb-16">贡献者风险分布</div>
      <table class="data-table">
        <thead>
          <tr><th>贡献者</th><th>提交 / 预测完成</th><th>高风险</th><th>中风险</th><th>低风险</th><th>审查完成任务</th><th>建议关注</th></tr>
        </thead>
        <tbody>
          <tr v-for="c in contributors" :key="c.name">
            <td><strong>{{ c.name }}</strong></td>
            <td>{{ c.commits }}/{{ c.predicted }}</td>
            <td><span :class="{ 'text-danger': c.high > 0 }">{{ c.high }}</span></td>
            <td>{{ c.mid }}</td>
            <td>{{ c.low }}</td>
            <td>{{ c.reviewDone }}</td>
            <td class="text-secondary text-sm">{{ c.suggestion }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card p-20 mt-24">
      <div class="section-title mb-16">重点提交跟进</div>
      <div class="follow-up">
        <div class="flex gap-12 mb-8">
          <RiskTag level="high" :score="0.86" show-score />
          <span class="text-sm text-secondary">8f3a2c1 · 重构任务权限校验 · 张晨 · main</span>
        </div>
        <p class="text-sm">人工审查已完成，问题已修复。关联修复提交 a19b730（低风险 0.21）已合并。</p>
        <div class="flex gap-12 mt-16">
          <router-link to="/commits/8f3a2c1" class="btn btn-secondary">查看详情</router-link>
          <router-link to="/reviews/8f3a2c1" class="btn btn-secondary">查看记录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import StatCard from '@/components/common/StatCard.vue'
import RiskTag from '@/components/common/RiskTag.vue'
import RiskTrendChart from '@/components/charts/RiskTrendChart.vue'

const filters = ref({ project: '', date: '' })

const trendData = [
  { date: '10/03', high: 0, mid: 1, low: 0 },
  { date: '10/04', high: 0, mid: 0, low: 1 },
  { date: '10/05', high: 1, mid: 0, low: 1 },
  { date: '10/06', high: 0, mid: 0, low: 1 },
  { date: '10/07', high: 0, mid: 1, low: 0 },
  { date: '10/09', high: 1, mid: 0, low: 0 },
  { date: '10/10', high: 0, mid: 0, low: 1 }
]

const progressItems = [
  { label: '已完成', count: 4, percent: 67, color: 'var(--color-success)' },
  { label: '审查中', count: 1, percent: 17, color: 'var(--color-primary)' },
  { label: '待分配', count: 1, percent: 17, color: 'var(--text-tertiary)' }
]

const contributors = [
  { name: '张晨', commits: 3, predicted: 3, high: 1, mid: 0, low: 2, reviewDone: 2, suggestion: '高风险提交已修复' },
  { name: '陈思', commits: 2, predicted: 2, high: 1, mid: 0, low: 1, reviewDone: 1, suggestion: '1项高风险待审查' },
  { name: '林悦', commits: 2, predicted: 1, high: 0, mid: 1, low: 0, reviewDone: 1, suggestion: '1项分析中' },
  { name: '王浩', commits: 2, predicted: 1, high: 0, mid: 1, low: 0, reviewDone: 0, suggestion: '1项预测失败' }
]
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.phase-tag { font-size: 12px; color: var(--text-tertiary); margin-bottom: 8px; }
.filter-bar { display: flex; gap: 12px; align-items: center; }
.two-col { display: grid; grid-template-columns: 1.5fr 1fr; gap: 16px; }
.p-20 { padding: 20px; }
.legend { display: flex; gap: 16px; font-size: 12px; color: var(--text-secondary); }
.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 4px; }
.progress-list { display: flex; flex-direction: column; gap: 20px; }
.progress-bar { height: 8px; background-color: var(--bg-input); border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; border-radius: 4px; transition: width 0.3s; }
.data-table { width: 100%; }
.data-table th, .data-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border-color); }
.data-table th { font-size: 12px; color: var(--text-tertiary); font-weight: 500; }
.data-table td { font-size: 14px; }
.data-table tbody tr:hover { background-color: var(--bg-table-hover); }
.text-danger { color: var(--color-high-risk); font-weight: 600; }
.follow-up { padding: 16px; background-color: var(--bg-page); border-radius: var(--radius-sm); }
</style>