<template>
  <div class="arrange-review">
    <div class="page-header">
      <div>

        <h1 class="page-title">安排代码审查</h1>
        <p class="page-subtitle">为高风险变更选择合适的审查人，补充审查重点与优先级。</p>
      </div>
      <router-link to="/commits/8f3a2c1" class="btn btn-secondary">返回提交详情</router-link>
    </div>

    <div class="two-col mt-24">
      <div class="left-col">
        <div class="card p-20">
          <div class="commit-title">重构任务权限校验</div>
          <div class="commit-sub text-sm text-secondary mb-16">校园协作平台 / 8f3a2c1</div>
          <div class="flex gap-12 mb-16">
            <RiskTag level="high" :score="0.86" show-score />
            <StatusTag status="pending" />
          </div>
          <div class="commit-meta">
            <div class="meta-row"><span class="meta-label">作者</span><span>张晨</span></div>
            <div class="meta-row"><span class="meta-label">分支</span><span>main</span></div>
            <div class="meta-row"><span class="meta-label">时间</span><span>2026-10-09 09:42</span></div>
            <div class="meta-row"><span class="meta-label">变更</span><span>12个文件 · +286 / -94行</span></div>
          </div>
          <InfoAlert type="warning" class="mt-16">模型预测已完成，人工结论尚未产生。请避免仅凭风险分数认定缺陷。</InfoAlert>
        </div>

        <div class="card p-20 mt-16">
          <div class="section-title mb-16">本次审查重点</div>
          <div class="focus-list">
            <div v-for="f in reviewFocus" :key="f" class="focus-item">
              <span class="focus-icon">▸</span><span>{{ f }}</span>
            </div>
          </div>
          <p class="text-sm text-secondary mt-16">负责人林悦安排审查；作者张晨负责响应意见。</p>
        </div>

        <div class="card p-20 mt-16">
          <div class="section-title mb-16">保存后的状态</div>
          <div class="flow-tags">
            <span class="flow-tag">待分配</span>
            <span class="flow-arrow">→</span>
            <span class="flow-tag active">待审查</span>
            <span class="flow-arrow">→</span>
            <span class="flow-tag">审查中</span>
          </div>
          <p class="text-sm text-secondary mt-16">保存后审查人将收到任务通知，提交作者可查看审查安排。</p>
        </div>
      </div>

      <div class="card p-20 form-card">
        <div class="section-title mb-24">审查任务分配</div>
        <div class="form-item mb-24">
          <label>审查人 <span class="required">*</span></label>
          <div class="reviewer-options mt-8">
            <div v-for="r in reviewers" :key="r.name" class="reviewer-card" :class="{ selected: selectedReviewer === r.name }" @click="selectedReviewer = r.name">
              <div class="reviewer-name">{{ r.name }}</div>
              <div class="reviewer-info text-sm text-secondary">{{ r.role }} · 当前{{ r.taskCount }}项审查任务</div>
            </div>
          </div>
          <p class="form-hint mt-8">张晨是提交作者，不可选择为本次审查人。</p>
        </div>

        <div class="form-row mb-24">
          <div class="form-item">
            <label>优先级</label>
            <select v-model="form.priority" class="mt-8">
              <option value="high">高 · 优先处理</option>
              <option value="mid">中 · 常规处理</option>
              <option value="low">低 · 有空时处理</option>
            </select>
          </div>
          <div class="form-item">
            <label>截止时间</label>
            <input v-model="form.deadline" type="text" class="mt-8" />
          </div>
        </div>

        <div class="form-item mb-24">
          <label>审查备注</label>
          <textarea v-model="form.note" rows="4" class="mt-8"></textarea>
        </div>

        <InfoAlert type="info">必填项已填写。保存后审查人{{ selectedReviewer }}将收到任务通知。</InfoAlert>

        <div class="form-actions mt-24">
          <button class="btn btn-secondary" @click="$router.back()">取消</button>
          <button class="btn btn-primary" @click="handleSave">✓ 保存并安排审查</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import RiskTag from '@/components/common/RiskTag.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import InfoAlert from '@/components/common/InfoAlert.vue'

const selectedReviewer = ref('王浩')
const form = ref({
  priority: 'high',
  deadline: '2026-10-10 18:00',
  note: '请重点核对任务权限入口重构后的角色边界，特别是成员退出后的权限缓存失效场景，以及无权限用户的访问测试。'
})

const reviewers = [
  { name: '王浩', role: '权限模块维护者', taskCount: 1 },
  { name: '陈思', role: '数据导入模块', taskCount: 0 }
]

const reviewFocus = [
  '权限入口重构后的角色一致性',
  '无权限用户与成员退出的边界场景',
  '大规模变更的测试覆盖'
]

function handleSave() {}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.phase-tag { font-size: 12px; color: var(--text-tertiary); margin-bottom: 8px; }
.two-col { display: grid; grid-template-columns: 1fr 0.85fr; gap: 16px; }
.left-col { display: flex; flex-direction: column; }
.p-20 { padding: 20px; }
.commit-title { font-size: 18px; font-weight: 600; }
.commit-sub { margin-top: 4px; }
.commit-meta { display: flex; flex-direction: column; gap: 8px; }
.meta-row { display: flex; gap: 12px; font-size: 14px; }
.meta-label { color: var(--text-tertiary); min-width: 50px; }
.focus-list { display: flex; flex-direction: column; gap: 12px; }
.focus-item { display: flex; gap: 8px; font-size: 14px; }
.focus-icon { color: var(--color-primary); }
.flow-tags { display: flex; align-items: center; gap: 8px; }
.flow-tag { padding: 4px 12px; border-radius: 4px; background-color: var(--bg-tag); color: var(--text-secondary); font-size: 13px; }
.flow-tag.active { background-color: var(--color-primary-bg); color: var(--color-primary); border: 1px solid var(--color-primary); }
.flow-arrow { color: var(--text-tertiary); }
.form-card { align-self: start; }
.form-item { display: flex; flex-direction: column; }
.form-item label { font-size: 13px; color: var(--text-secondary); }
.required { color: var(--color-error); }
.form-hint { font-size: 12px; color: var(--text-tertiary); }
.reviewer-options { display: flex; flex-direction: column; gap: 12px; }
.reviewer-card { padding: 16px; border: 1px solid var(--border-color); border-radius: var(--radius-sm); cursor: pointer; transition: all 0.2s; }
.reviewer-card:hover { border-color: var(--color-primary); }
.reviewer-card.selected { border-color: var(--color-primary); background-color: var(--color-primary-bg); }
.reviewer-name { font-size: 15px; font-weight: 500; margin-bottom: 4px; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-actions { display: flex; gap: 12px; justify-content: flex-end; }
.mb-24 { margin-bottom: 24px; }
</style>