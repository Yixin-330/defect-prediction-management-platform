import request from './request'

export function trainModel(data) {
  return request.post('/models/train', data)
}

export function getModelTaskStatus(taskId) {
  return request.get(`/tasks/${taskId}`)
}