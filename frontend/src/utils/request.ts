import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: '/api',
  timeout: 15000
})

request.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (resp) => {
    // The backend wraps every payload in a Result<T> envelope:
    //   { code: 0, message: "ok", data: T }
    // Unwrap it here so callers receive T directly (e.g. LoginResponse instead
    // of { code, message, data: { token, ... } }).
    const wrapped = resp.data
    if (wrapped && typeof wrapped === 'object' && 'code' in wrapped) {
      if (wrapped.code !== 0) {
        ElMessage.error(wrapped.message || '请求失败')
        return Promise.reject(wrapped)
      }
      return wrapped.data
    }
    return wrapped
  },
  (err: AxiosError<any>) => {
    const status = err.response?.status
    const msg = err.response?.data?.message || err.message
    if (status === 401) {
      ElMessage.error('未登录或登录已过期')
      localStorage.removeItem('token')
      router.push('/login')
    } else if (status === 403) {
      ElMessage.error('无权限')
    } else if (status === 404) {
      ElMessage.error(msg || '资源不存在')
    } else {
      ElMessage.error(msg || '网络错误')
    }
    return Promise.reject(err)
  }
)

export default request
