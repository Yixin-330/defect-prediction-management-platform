<template>
  <div class="review-record">
    <div class="page-header">
      <div>

        <h1 class="page-title">审查处理记录</h1>
        <p class="page-subtitle">校园协作平台 / 8f3a2c1 · 保留意见、处理过程与人工结论</p>
      </div>
      <div class="flex gap-12">
        <router-link to="/commits/8f3a2c1" class="btn btn-secondary">返回提交详情</router-link>
        <router-link to="/trend" class="btn btn-secondary">查看质量趋势</router-link>
      </div>
    </div>

    <InfoAlert type="success" class="mt-24">审查已完成：1项权限边界问题已修复并复核通过，另1项测试建议已采纳。审查记录与预测信号已关联存档。</InfoAlert>

    <div class="two-col mt-24">
      <div class="card p-20">
        <div class="section-title mb-16">模型预测 · 原始信号</div>
        <div class="risk-score">0.86</div>
        <RiskTag level="high" :score="0.86" show-score />
        <div class="commit-meta mt-16">
          <div class="meta-row"><span class="meta-label">提交</span><span>8f3a2c1 · 重构任务权限校验</span></div>
          <div class="meta-row"><span class="meta-label">作者</span><span>张晨 · main · 10/09 09:42</span></div>
          <div class="meta-row"><span class="meta-label">变更</span><span>12个文件 · +286 / -94行</span></div>
        </div>
      </div>

      <div class="card p-20">
        <div class="section-title mb-16">人工审查 · 处理结论</div>
        <div class="meta-row mb-8"><span class="meta-label">审查人</span><span>王浩</span></div>
        <div class="meta-row mb-16"><span class="meta-label">负责人</span><span>林悦</span></div>
        <div class="flex gap-12 mb-16">
          <StatusTag status="done" />
          <span class="tag" style="background:var(--color-success-bg);color:var(--color-success)">发现问题 · 已修复</span>
        </div>
        <p class="text-sm text-secondary">审查发现任务权限服务存在缓存失效问题，已由张晨补充修复并复核通过。同时采纳增加边界测试的建议。</p>
      </div>
    </div>

    <div class="card p-20 mt-24">
      <div class="section-title mb-16">审查意见与处理结果</div>
      <table class="data-table">
        <thead><tr><th style="width:160px">类型/位置</th><th>发现的问题与建议</th><th style="width:240px">处理结果</th></tr></thead>
        <tbody>
          <tr>
            <td><div><strong>人工确认问题</strong></div><div class="text-sm text-tertiary">任务权限服务.java</div></td>
            <td>缓存权限失效：成员退出后权限未及时更新，仍可访问已退出项目的任务。</td>
            <td><div>张晨补充修复</div><div class="text-sm text-secondary">10/10 已复核</div></td>
          </tr>
          <tr>
            <td><div><strong>改进建议</strong></div><div class="text-sm text-tertiary">任务权限测试.java</div></td>
            <td>增加无权限用户访问测试，覆盖角色切换与成员退出边界场景。</td>
            <td><div>已新增2组边界测试</div><div class="text-sm text-secondary">10/10 已采纳</div></td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="card p-20 mt-24">
      <div class="flex justify-between items-center mb-16">
        <span class="section-title">关联的修复提交</span>
        <a class="text-sm">查看修复详情 →</a>
      </div>
      <div class="fix-card">
        <div class="fix-title">修复成员退出后的权限缓存</div>
        <div class="fix-meta text-sm text-secondary mt-8">a19b730 · 张晨 · main · 10月10日 15:40</div>
        <div class="flex gap-12 mt-16">
          <RiskTag level="low" :score="0.21" show-score />
          <span class="tag" style="background:var(--color-success-bg);color:var(--color-success)">已合并</span>
        </div>
        <p class="text-sm text-secondary mt-16">在成员退出时主动清除权限缓存，增加缓存失效的单元测试覆盖。</p>
      </div>
    </div>

    <div class="card p-20 mt-24">
      <div class="section-title mb-16">审查状态时间线</div>
      <div class="timeline">
        <div v-for="(t, i) in timeline" :key="i" class="timeline-item" :class="`tl-${t.status}`">
          <div class="timeline-dot"></div>
          <div class="timeline-content">
            <span class="timeline-time text-sm text-tertiary">{{ t.time }}</span>
            <span class="timeline-label">{{ t.label }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import RiskTag from '@/components/common/RiskTag.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import InfoAlert from '@/components/common/InfoAlert.vue'

const timeline = [
  { time: '10/09 10:30', label: '待分配 · 风险预测完成后自动创建', status: 'pending' },
  { time: '10/09 11:02', label: '待审查 · 负责人林悦分配审查人王浩', status: 'waiting' },
  { time: '10/09 14:00', label: '审查中 · 王浩开始代码审查', status: 'reviewing' },
  { time: '10/10 15:40', label: '待复核 · 张晨提交修复 a19b730', status: 'rechecking' },
  { time: '10/10 16:20', label: '已完成 · 王浩复核通过，审查闭环', status: 'done' }
]
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.phase-tag { font-size: 12px; color: var(--text-tertiary); margin-bottom: 8px; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.p-20 { padding: 20px; }
.risk-score { font-size: 36px; font-weight: 700; color: var(--color-high-risk); }
.commit-meta { display: flex; flex-direction: column; gap: 8px; }
.meta-row { display: flex; gap: 12px; font-size: 14px; }
.meta-label { color: var(--text-tertiary); min-width: 50px; }
.data-table { width: 100%; }
.data-table th, .data-table td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--border-color); vertical-align: top; }
.data-table th { font-size: 12px; color: var(--text-tertiary); font-weight: 500; }
.data-table td { font-size: 14px; }
.fix-card { padding: 16px; background-color: var(--bg-page); border-radius: var(--radius-sm); }
.fix-title { font-size: 15px; font-weight: 500; }
.timeline { display: flex; flex-direction: column; gap: 0; }
.timeline-item { display: flex; gap: 16px; padding-bottom: 24px; position: relative; }
.timeline-item:not(:last-child)::before { content: ''; position: absolute; left: 5px; top: 16px; bottom: 0; width: 2px; background-color: var(--border-color); }
.timeline-dot { width: 12px; height: 12px; border-radius: 50%; margin-top: 4px; flex-shrink: 0; z-index: 1; }
.tl-pending .timeline-dot { background-color: var(--text-tertiary); }
.tl-waiting .timeline-dot { background-color: var(--color-primary); }
.tl-reviewing .timeline-dot { background-color: var(--color-primary); }
.tl-rechecking .timeline-dot { background-color: var(--color-warning); }
.tl-done .timeline-dot { background-color: var(--color-success); }
.timeline-content { display: flex; flex-direction: column; gap: 2px; }
.timeline-label { font-size: 14px; }
</style>