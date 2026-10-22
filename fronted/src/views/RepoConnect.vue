<template>
  <div class="repo-connect">
    <div class="page-header">
      <div>
        <h1 class="page-title">连接团队项目仓库</h1>
        <p class="page-subtitle">完成仓库授权后，同步提交、提取特征并请求风险预测。</p>
      </div>
      <span class="tag" style="background:var(--color-success-bg);color:var(--color-success)">仓库连接成功</span>
    </div>

    <div class="two-col mt-24">
      <div class="card form-card">
        <div class="form-intro">
          <span class="section-title">仓库连接信息</span>
          <p class="text-sm text-secondary mt-8">仅需要代码读取权限；不写入或修改仓库。</p>
        </div>
        <div class="form-body">
          <div class="form-item">
            <label>项目名称</label>
            <input v-model="form.name" type="text" />
          </div>
          <div class="form-item">
            <label>团队名称</label>
            <input v-model="form.group" type="text" />
          </div>
          <div class="form-item">
            <label>仓库地址</label>
            <input v-model="form.repoUrl" type="text" />
            <p class="form-hint">演示地址，不代表已实际接入的仓库。</p>
          </div>
          <div class="form-row">
            <div class="form-item">
              <label>默认分支</label>
              <select v-model="form.branch">
                <option value="main">main</option>
                <option value="dev">dev</option>
              </select>
            </div>
            <div class="form-item">
              <label>同步范围</label>
              <select v-model="form.syncRange">
                <option value="7">最近7天</option>
                <option value="14">最近14天</option>
                <option value="30">最近30天</option>
              </select>
            </div>
          </div>
          <div class="form-item">
            <label>访问凭据</label>
            <input v-model="form.token" type="password" placeholder="············ 安全占位" />
            <p class="form-hint">只读访问令牌 · 加密保存，不在页面回显真实密钥。</p>
          </div>
          <div class="form-actions">
            <button class="btn btn-primary" @click="handleUpdate">更新连接</button>
            <button class="btn btn-secondary" @click="handleVerify">重新验证连接</button>
            <button class="btn btn-secondary btn-disconnect" @click="handleDisconnect">断开连接</button>
          </div>
          <p class="form-hint">连接更新后保留历史预测与处理记录。</p>
        </div>
      </div>

      <div class="right-col">
        <div class="card p-20">
          <div class="flex justify-between items-center mb-16">
            <span class="section-title">接入进度</span>
            <a class="text-sm">查看提交 →</a>
          </div>
          <p class="text-sm text-secondary mb-16">本次任务 · 今日 10:28 发起</p>
          <div class="step-list">
            <div v-for="step in syncSteps" :key="step.label" class="step-item" :class="`step-${step.status}`">
              <span class="step-icon">{{ stepIcon(step.status) }}</span>
              <div class="step-content">
                <span class="step-label">{{ step.label }}</span>
                <span class="step-detail text-sm text-secondary">{{ step.detail }}</span>
              </div>
            </div>
          </div>
          <div v-if="syncing" class="progress-bar mt-16">
            <div class="progress-fill" style="width:75%"></div>
          </div>
          <p v-if="syncing" class="text-sm text-secondary mt-8">已完成 6/8 · 失败项支持单独重试</p>
          <router-link to="/commits" class="btn btn-primary mt-16" style="width:100%;justify-content:center">进入提交风险列表</router-link>
        </div>

        <div class="card p-20 mt-16">
          <div class="section-title mb-8">连接失败时如何处理</div>
          <p class="text-sm text-secondary mb-16">静态状态说明 · 非当前连接状态</p>
          <InfoAlert type="error">授权失败：凭据失效或仓库不可访问。</InfoAlert>
          <p class="text-sm text-secondary mt-16">检查仓库地址、访问权限与凭据有效期。失败时不启动同步，历史结果仍可查看。</p>
          <div class="flex gap-12 mt-16">
            <button class="btn btn-secondary">修改凭据</button>
            <button class="btn btn-secondary">重新连接</button>
          </div>
        </div>
      </div>
    </div>

    <InfoAlert type="info" class="mt-24">系统仅使用提交当时可获得的信息。离线训练与模型选型由研究侧完成，不属于仓库接入流程。</InfoAlert>

    <div class="card p-20 mt-16">
      <div class="section-title mb-16">数据隐私与安全</div>
      <div class="privacy-list">
        <div class="privacy-item">
          <span class="privacy-icon">🔒</span>
          <div>
            <div class="privacy-title">源代码不持久化</div>
            <div class="text-sm text-secondary">系统仅读取提交元数据与变更统计用于特征提取，不存储完整源代码内容。</div>
          </div>
        </div>
        <div class="privacy-item">
          <span class="privacy-icon">🔑</span>
          <div>
            <div class="privacy-title">凭据加密存储</div>
            <div class="text-sm text-secondary">访问令牌加密保存，仅用于读取仓库，不会回显或泄露。断开连接后凭据立即删除。</div>
          </div>
        </div>
        <div class="privacy-item">
          <span class="privacy-icon">👥</span>
          <div>
            <div class="privacy-title">团队数据隔离</div>
            <div class="text-sm text-secondary">每个团队的项目数据、预测结果与审查记录相互隔离，仅团队成员可访问本团队数据。</div>
          </div>
        </div>
        <div class="privacy-item">
          <span class="privacy-icon">🛡</span>
          <div>
            <div class="privacy-title">预测结果仅限审查参考</div>
            <div class="text-sm text-secondary">风险评分与特征解释仅用于审查优先级排序，不对外公开，不作为绩效或考核依据。</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import InfoAlert from '@/components/common/InfoAlert.vue'

const form = ref({
  name: '校园协作平台',
  group: '开发团队',
  repoUrl: 'https://github.com/team-demo/campus-collab',
  branch: 'main',
  syncRange: '7',
  token: '············'
})

const syncing = ref(true)

const syncSteps = ref([
  { label: '授权校验通过', detail: '已成功读取 main 分支。', status: 'done' },
  { label: '仓库同步', detail: '8次提交已保存', status: 'done' },
  { label: '提交解析与特征提取', detail: '训练与在线预测共用特征规则', status: 'done' },
  { label: '提交风险预测', detail: '6次完成 · 1次分析中 · 1次失败', status: 'active' }
])

function stepIcon(status) {
  return { done: '✓', active: '◐', pending: '○' }[status] || '○'
}

function handleUpdate() {}
function handleVerify() {}
function handleDisconnect() {}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.two-col { display: grid; grid-template-columns: 1.2fr 1fr; gap: 16px; }
.form-card { padding: 24px; }
.form-intro { margin-bottom: 20px; }
.form-body { display: flex; flex-direction: column; gap: 16px; }
.form-item { display: flex; flex-direction: column; gap: 6px; }
.form-item label { font-size: 13px; color: var(--text-secondary); }
.form-hint { font-size: 12px; color: var(--text-tertiary); }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.form-actions { display: flex; gap: 12px; flex-wrap: wrap; }
.btn-disconnect { color: var(--color-error); border-color: var(--color-error); }
.right-col { display: flex; flex-direction: column; }
.p-20 { padding: 20px; }
.step-list { display: flex; flex-direction: column; gap: 16px; }
.step-item { display: flex; gap: 12px; align-items: flex-start; }
.step-icon { font-size: 18px; width: 24px; text-align: center; flex-shrink: 0; }
.step-done .step-icon { color: var(--color-success); }
.step-active .step-icon { color: var(--color-primary); }
.step-content { display: flex; flex-direction: column; gap: 2px; }
.step-label { font-size: 14px; font-weight: 500; }
.progress-bar { height: 8px; background-color: var(--bg-input); border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background-color: var(--color-primary); border-radius: 4px; }
.privacy-list { display: flex; flex-direction: column; gap: 16px; }
.privacy-item { display: flex; gap: 12px; align-items: flex-start; }
.privacy-icon { font-size: 20px; flex-shrink: 0; }
.privacy-title { font-size: 14px; font-weight: 500; margin-bottom: 4px; }
</style>