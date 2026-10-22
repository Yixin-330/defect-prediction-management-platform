import request from './request'

export function getProjects() {
  return request.get('/projects/')
}

export function registerProject(data) {
  return request.post('/projects/', data)
}

export function getProject(projectId) {
  return request.get(`/projects/${projectId}`)
}

export function getDashboardSummary() {
  return request.get('/dashboard/summary')
}

export function getRiskRanking(projectId) {
  return request.get(`/projects/${projectId}/risk-ranking`)
}

export function getProjectPredictions(projectId) {
  return request.get(`/projects/${projectId}/predictions`)
}

export function cloneRepo(repoUrl) {
  return request.post('/repos/clone', { repo_url: repoUrl })
}

export function cloneRepoAsync(repoUrl) {
  return request.post('/repos/clone-async', { repo_url: repoUrl })
}

export function getTaskStatus(taskId) {
  return request.get(`/tasks/${taskId}`)
}

export function getRepoCommits(repoId) {
  return request.get(`/repos/${repoId}/commits`)
}
