<template>
  <div class="commit-detail">
    <div class="page-header">
      <div>

        <h1 class="page-title">提交详情与风险解释</h1>
        <p class="page-subtitle">提交风险列表 / 8f3a2c1 · 先理解风险来源，再决定审查重点。</p>
      </div>
      <div class="flex gap-12">
        <router-link to="/commits" class="btn btn-secondary">返回列表</router-link>
        <router-link to="/commits/8f3a2c1/arrange" class="btn btn-primary">安排代码审查</router-link>
      </div>
    </div>

    <div class="two-col mt-24">
      <div class="card p-20">
        <div class="section-title mb-16">提交信息</div>
        <div class="commit-title">重构任务权限校验</div>
        <div class="commit-meta">
          <div class="meta-row"><span class="meta-label">提交ID</span><span>8f3a2c1 · 校园协作平台</span></div>
          <div class="meta-row"><span class="meta-label">作者</span><span>张晨</span></div>
          <div class="meta-row"><span class="meta-label">时间</span><span>2026-10-09 09:42</span></div>
          <div class="meta-row"><span class="meta-label">分支</span><span>main</span></div>
          <div class="meta-row"><span class="meta-label">变更</span><span>12个文件 · +286 / -94行</span></div>
        </div>
        <div class="meta-tags">
          <StatusTag type="predict" status="completed" />
          <StatusTag status="pending" />
        </div>
        <p class="commit-desc text-sm text-secondary mt-16">统一任务权限判断入口，合并角色判断与访问校验逻辑，调整接口级权限入口。</p>
      </div>

      <div class="card p-20 risk-score-card">
        <div class="section-title mb-16">预测风险信号</div>
        <p class="text-sm text-tertiary mb-8">示例结果 · 非确定缺陷</p>
        <div class="risk-score">0.86</div>
        <RiskTag level="high" :score="0.86" show-score />
        <p class="text-sm text-secondary mt-16">建议优先审查 · 分数范围 0–1</p>
        <div class="review-status mt-16">
          <span class="text-sm text-tertiary">人工结论：</span>
          <span class="text-sm">尚未审查</span>
        </div>
      </div>
    </div>

    <InfoAlert type="info" class="mt-24">风险分数用于安排审查优先级，不是缺陷认定。以下特征贡献为 SHAP 解释示意，不代表已验证模型表现，也不能直接定位缺陷。</InfoAlert>

    <div class="two-col-2 mt-24">
      <div class="card p-20">
        <div class="section-title mb-8">哪些特征推动了风险信号？</div>
        <p class="text-sm text-secondary mb-16">Kamei 14维特征中的主要贡献 · 示例贡献值</p>
        <div class="legend mb-16">
          <span><i style="background:#ef4444"></i>提高预测风险</span>
          <span><i style="background:#22c55e"></i>降低预测风险</span>
        </div>
        <FeatureContributionChart :features="featureData" />
        <p class="text-sm text-tertiary mt-16">基线 0.25 + 示例贡献合计 0.61 = 风险信号 0.86。提取时间：10/09 10:28；只使用本次提交及提交前历史信息。</p>
      </div>

      <div class="card p-20">
        <div class="section-title mb-8">建议的审查重点</div>
        <p class="text-sm text-secondary mb-16">帮助审查人理解变更，不替代代码阅读</p>
        <div class="suggestion-list">
          <div v-for="s in suggestions" :key="s.title" class="suggestion-item">
            <span class="suggestion-icon">▸</span>
            <div>
              <div class="suggestion-title">{{ s.title }}</div>
              <div class="suggestion-desc text-sm text-secondary">{{ s.desc }}</div>
            </div>
          </div>
        </div>
        <button class="btn btn-primary mt-16" style="width:100%;justify-content:center">按建议安排审查</button>
      </div>
    </div>

    <div class="card p-20 mt-24">
      <div class="flex justify-between items-center mb-16">
        <span class="section-title">变更文件摘要</span>
        <span class="text-sm text-secondary">显示重点文件 3/12 · 合计 +286/-94行</span>
      </div>
      <table class="data-table">
        <thead><tr><th>文件路径</th><th>新增/删除</th><th>变更摘要</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="f in files" :key="f.path">
            <td class="file-path">{{ f.path }}</td>
            <td><span style="color:var(--color-low-risk)">+{{ f.add }}</span> / <span style="color:var(--color-high-risk)">-{{ f.del }}</span></td>
            <td class="text-secondary">{{ f.summary }}</td>
            <td><a class="text-sm">查看详情</a></td>
          </tr>
        </tbody>
      </table>
      <a class="text-sm mt-16" style="display:inline-block">查看全部文件</a>
    </div>
  </div>
</template>

<script setup>
import RiskTag from '@/components/common/RiskTag.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import InfoAlert from '@/components/common/InfoAlert.vue'
import FeatureContributionChart from '@/components/charts/FeatureContributionChart.vue'

const featureData = [
  { name: '新增代码量', value: 0.24 },
  { name: '涉及文件数', value: 0.18 },
  { name: '开发者经验', value: 0.12 },
  { name: '删除代码量', value: 0.08 },
  { name: '距上次变更时间', value: -0.04 }
]

const suggestions = [
  { title: '变更规模较大', desc: '新增286行涉及12个文件，重点检查权限入口重构后的角色一致性。' },
  { title: '作者项目经验较少', desc: '提交前有8次历史提交，建议关注权限相关模块的边界场景。' },
  { title: '补充边界测试', desc: '重点检查角色切换、无权限用户访问、成员退出后的缓存失效。' }
]

const files = [
  { path: '后端/权限/任务权限服务.java', add: 124, del: 48, summary: '合并角色判断与访问校验' },
  { path: '后端/接口/任务控制器.java', add: 68, del: 32, summary: '调整接口级权限入口' },
  { path: '测试/权限/任务权限测试.java', add: 42, del: 0, summary: '新增角色与权限边界测试' }
]
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.phase-tag { font-size: 12px; color: var(--text-tertiary); margin-bottom: 8px; }
.two-col { display: grid; grid-template-columns: 1.5fr 1fr; gap: 16px; }
.two-col-2 { display: grid; grid-template-columns: 1.5fr 1fr; gap: 16px; }
.p-20 { padding: 20px; }
.commit-title { font-size: 18px; font-weight: 600; margin-bottom: 16px; }
.commit-meta { display: flex; flex-direction: column; gap: 8px; }
.meta-row { display: flex; gap: 12px; font-size: 14px; }
.meta-label { color: var(--text-tertiary); min-width: 60px; }
.meta-tags { display: flex; gap: 8px; margin-top: 16px; }
.commit-desc { line-height: 1.6; }
.risk-score-card { text-align: center; }
.risk-score { font-size: 48px; font-weight: 700; color: var(--color-high-risk); line-height: 1; margin: 8px 0 12px; }
.review-status { padding-top: 16px; border-top: 1px solid var(--border-color); }
.legend { display: flex; gap: 16px; font-size: 12px; color: var(--text-secondary); }
.legend i { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 4px; }
.suggestion-list { display: flex; flex-direction: column; gap: 16px; }
.suggestion-item { display: flex; gap: 8px; }
.suggestion-icon { color: var(--color-primary); }
.suggestion-title { font-size: 14px; font-weight: 500; margin-bottom: 4px; }
.suggestion-desc { line-height: 1.5; }
.data-table { width: 100%; }
.data-table th, .data-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border-color); }
.data-table th { font-size: 12px; color: var(--text-tertiary); font-weight: 500; }
.data-table td { font-size: 14px; }
.data-table tbody tr:hover { background-color: var(--bg-table-hover); }
.file-path { font-family: monospace; color: var(--color-primary-light); }
</style>