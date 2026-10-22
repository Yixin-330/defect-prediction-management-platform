import request from './request'

export function createReviewItem(projectId, commitId) {
  return request.post(`/projects/${projectId}/commits/${commitId}/reviews`)
}

export function getReviews(projectId, params) {
  return request.get(`/projects/${projectId}/reviews`, { params })
}

export function getReviewDetail(projectId, reviewId) {
  return request.get(`/projects/${projectId}/reviews/${reviewId}`)
}

export function claimReview(projectId, reviewId, data) {
  return request.post(`/projects/${projectId}/reviews/${reviewId}/claim`, data)
}

export function submitReviewConclusion(projectId, reviewId, data) {
  return request.post(`/projects/${projectId}/reviews/${reviewId}/conclusion`, data)
}

export function updateReviewStatus(projectId, reviewId, status) {
  return request.patch(`/projects/${projectId}/reviews/${reviewId}/status`, { status })
}

export function ignoreReview(projectId, reviewId) {
  return request.post(`/projects/${projectId}/reviews/${reviewId}/ignore`)
}