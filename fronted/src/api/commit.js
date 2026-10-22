import request from './request'

export function getCommits(projectId, params) {
  return request.get(`/projects/${projectId}/commits/`, { params })
}

export function getCommitDetail(projectId, commitId) {
  return request.get(`/projects/${projectId}/commits/${commitId}`)
}

export function getCommitFiles(projectId, commitId) {
  return request.get(`/projects/${projectId}/commits/${commitId}/files`)
}

export function syncCommits(projectId) {
  return request.post(`/projects/${projectId}/commits/sync`)
}