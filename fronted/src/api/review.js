import request from './request'

export function createReview(data) {
  return request.post('/reviews/', data)
}

export function getReviews(params) {
  return request.get('/reviews/', { params })
}

export function updateReview(reviewId, data) {
  return request.put(`/reviews/${reviewId}`, data)
}

export function deleteReview(reviewId) {
  return request.delete(`/reviews/${reviewId}`)
}