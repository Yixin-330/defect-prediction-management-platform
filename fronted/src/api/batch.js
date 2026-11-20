import request from './request'

export function batchPredict(repoId) {
  return request.post(`/repos/${repoId}/batch-predict`)
}

export function getCommitDiff(commitId) {
  return request.get(`/commits/${commitId}/diff`)
}