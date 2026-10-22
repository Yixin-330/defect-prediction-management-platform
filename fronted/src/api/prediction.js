import request from './request'

export function getPrediction(commitId) {
  return request.get(`/predictions/${commitId}`)
}

