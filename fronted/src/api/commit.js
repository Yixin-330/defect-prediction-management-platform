import request from './request'

export function getRepoCommits(repoId) {
  return request.get(`/repos/${repoId}/commits`)
}