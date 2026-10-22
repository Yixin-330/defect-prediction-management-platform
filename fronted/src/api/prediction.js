import request from './request'

export function predictCommit(projectId, commitId) {
  return request.post(`/projects/${projectId}/commits/${commitId}/predict`)
}

export function getPrediction(projectId, commitId) {
  return request.get(`/projects/${projectId}/commits/${commitId}/prediction`)
}

export function getPredictionHistory(projectId, params) {
  return request.get(`/projects/${projectId}/predictions`, { params })
}

export function getRankedCommits(projectId, params) {
  return request.get(`/projects/${projectId}/commits/ranked`, { params })
}

export function getFeatureContributions(projectId, commitId) {
  return request.get(`/projects/${projectId}/commits/${commitId}/contributions`)
}