import request from './request'

export function generateDataset(data) {
  return request.post('/datasets/generate', data)
}

export function getDatasetTaskStatus(taskId) {
  return request.get(`/tasks/${taskId}`)
}