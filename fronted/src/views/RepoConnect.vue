<template>
  <div class="repo-connect">
    <div class="page-header">
      <div>
        <h1 class="page-title">连接团队项目仓库</h1>
        <p class="page-subtitle">克隆Git仓库，同步提交记录并请求风险预测。</p>
      </div>
    </div>

    <div class="card p-20 mt-24 form-card">
      <div class="section-title mb-24">仓库连接</div>
      <div class="form-body">
        <div class="form-item mb-24">
          <label>仓库地址 <span class="required">*</span></label>
          <input v-model="repoUrl" type="text" placeholder="https://github.com/team/project.git" class="mt-8" />
          <p class="form-hint mt-8">仅需要代码读取权限</p>
        </div>

        <div class="form-actions">
          <button class="btn btn-primary" :disabled="submitting" @click="handleClone">
            {{ submitting ? '克隆中...' : '连接仓库' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="result" class="card p-20 mt-16">
      <div class="section-title mb-16">连接结果</div>
      <InfoAlert :type="result.error ? 'error' : 'success'">{{ result.message }}</InfoAlert>
      <div v-if="result.total_commits_saved" class="text-sm text-secondary mt-8">
        共保存 {{ result.total_commits_saved }} 条提交记录
      </div>
      <div v-if="generating" class="text-sm text-secondary mt-8">
        ⏳ 正在生成风险预测...（{{ generateProgress }}/{{ generateTotal }}）
      </div>
      <div v-if="generateDone" class="text-sm mt-8" style="color:var(--color-success)">
        ✅ 已为 {{ generateDoneCount }} 条提交生成风险预测
      </div>
      <router-link v-if="generateDone" to="/commits" class="btn btn-primary mt-16">查看提交列表</router-link>
    </div>

    <div class="card p-20 mt-16">
      <div class="section-title mb-16">数据隐私与安全</div>
      <div class="privacy-list">
        <div class="privacy-item">
          <span class="privacy-icon">🔒</span>
          <div>
            <div class="privacy-title">源代码不持久化</div>
            <div class="text-sm text-secondary">系统仅读取提交元数据与变更统计，不存储完整源代码内容。</div>
          </div>
        </div>
        <div class="privacy-item">
          <span class="privacy-icon">👥</span>
          <div>
            <div class="privacy-title">团队数据隔离</div>
            <div class="text-sm text-secondary">每个团队的项目数据相互隔离，仅团队成员可访问。</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import InfoAlert from '@/components/common/InfoAlert.vue'
import { cloneRepo, getRepoCommits } from '@/api/project'
import { getPrediction } from '@/api/prediction'
import { ensureProject } from '@/utils/dataSync'

const repoUrl = ref('')
const submitting = ref(false)
const result = ref(null)
const generating = ref(false)
const generateProgress = ref(0)
const generateTotal = ref(0)
const generateDone = ref(false)
const generateDoneCount = ref(0)

async function handleClone() {
  if (!repoUrl.value) return
  submitting.value = true
  result.value = null
  generating.value = false
  generateDone.value = false
  try {
    const cloneRes = await cloneRepo(repoUrl.value)
    result.value = {
      message: cloneRes.message || '仓库解析并保存成功',
      total_commits_saved: cloneRes.total_commits_saved || 0,
      error: false
    }

    const repoId = cloneRes.repository_id
    if (repoId) {
      generating.value = true
      const repoData = await getRepoCommits(repoId)
      const commits = repoData.commits || []
      generateTotal.value = commits.length
      generateProgress.value = 0
      let count = 0
      for (const commit of commits) {
        try {
          await getPrediction(commit.id)
          count++
        } catch (e) {
          // skip
        }
        generateProgress.value++
      }
      generateDoneCount.value = count
      generateDone.value = true
      generating.value = false
      await ensureProject(repoUrl.value)
    }
  } catch (e) {
    result.value = { message: e.message || '连接失败', error: true }
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; }
.p-20 { padding: 20px; }
.form-card { max-width: 700px; }
.form-item { display: flex; flex-direction: column; }
.form-item label { font-size: 13px; color: var(--text-secondary); }
.required { color: var(--color-error); }
.form-hint { font-size: 12px; color: var(--text-tertiary); }
.form-actions { display: flex; gap: 12px; }
.privacy-list { display: flex; flex-direction: column; gap: 16px; }
.privacy-item { display: flex; gap: 12px; align-items: flex-start; }
.privacy-icon { font-size: 20px; flex-shrink: 0; }
.privacy-title { font-size: 14px; font-weight: 500; margin-bottom: 4px; }
.mb-24 { margin-bottom: 24px; }
</style>