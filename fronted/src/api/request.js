import axios from 'axios'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const status = error.response?.status || -1
    const serverMsg = error.response?.data?.detail || error.response?.data?.message
    let message
    if (serverMsg) {
      message = typeof serverMsg === 'string' ? serverMsg : JSON.stringify(serverMsg)
    } else if (status === 500) {
      message = '服务端处理出错，请稍后重试或先完成前置步骤'
    } else if (status === 503) {
      message = '模型不可用，请先训练或选用兼容模型'
    } else if (status === 404) {
      message = '请求的资源不存在'
    } else if (status === 409) {
      message = '数据冲突或状态已变更，请刷新后重试'
    } else if (status === 422) {
      message = '输入数据无法处理，请检查提交内容'
    } else if (status === 400) {
      message = '请求参数有误'
    } else if (status === -1) {
      message = '网络异常或服务未启动，请确认后端服务已运行'
    } else {
      message = error.message || '请求失败'
    }
    const err = {
      code: status,
      message,
      detail: error.response?.data?.detail || null
    }
    return Promise.reject(err)
  }
)

export default request