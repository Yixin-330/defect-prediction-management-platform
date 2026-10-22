import axios from 'axios'

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const err = {
      code: error.response?.status || -1,
      message: error.response?.data?.message || error.message || '请求失败',
      detail: error.response?.data?.detail || null
    }
    return Promise.reject(err)
  }
)

export default request