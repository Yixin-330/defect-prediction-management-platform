import request from './request'

export function getProjects() {
  return request.get('/projects')
}

export function getCurrentProject() {
  return request.get('/projects/current')
}

export function registerProject(data) {
  return request.post('/projects', data)
}

export function updateProjectConnection(projectId, data) {
  return request.put(`/projects/${projectId}/connection`, data)
}

export function verifyConnection(projectId) {
  return request.post(`/projects/${projectId}/connection/verify`)
}

export function disconnectProject(projectId) {
  return request.delete(`/projects/${projectId}/connection`)
}

export function getSyncProgress(projectId) {
  return request.get(`/projects/${projectId}/sync-progress`)
}

export function getProjectStats(projectId) {
  return request.get(`/projects/${projectId}/stats`)
}

export function getQualityTrend(projectId, params) {
  return request.get(`/projects/${projectId}/quality-trend`, { params })
}
