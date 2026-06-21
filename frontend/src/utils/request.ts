/**
 * Axios 请求封装 —— 全局拦截逻辑的单一入口
 *
 * 设计要点
 * --------
 * 1. <b>统一 Token 注入</b>：所有请求自动从 localStorage 读取 token 并写入
 *    {@code Authorization: Bearer <token>} 头，业务侧无需重复处理。
 * 2. <b>Result 解包</b>：后端所有接口返回 {@link Result<T>} 信封，
 *    这里在响应拦截器里把 {@code data} 字段直接 return，业务侧拿到的就是 T 本身。
 * 3. <b>错误集中处理</b>：业务错误 (code != 0) 和 HTTP 错误统一走 ElMessage 提示，
 *    并按状态码执行跳转/清理等副作用，业务侧仅需关心成功分支。
 */
import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建 axios 实例：基础路径走 /api（由前端 nginx 或 vite 代理转发到后端）
const request = axios.create({
  baseURL: '/api',
  timeout: 15000
})

// ============================================================
// 请求拦截器 —— 自动注入 JWT
// ============================================================
request.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token')
  if (token) {
    // Bearer 是 JWT 的标准认证方案，与后端 JwtAuthenticationFilter 配套
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ============================================================
// 响应拦截器 —— Result 解包 & 错误集中处理
// ============================================================
request.interceptors.response.use(
  // ---- 成功分支（HTTP 2xx） ----
  (resp) => {
    // 后端统一返回 Result<T> 信封：
    //   { code: 0, message: "ok", data: T }
    // 这里解包后，业务侧拿到的就是 T 本身（例如 LoginResponse），
    // 而非套了一层 { code, message, data } 的对象。
    const wrapped = resp.data
    if (wrapped && typeof wrapped === 'object' && 'code' in wrapped) {
      if (wrapped.code !== 0) {
        // 业务错误：用 ElMessage 弹错，并把后端消息向下抛以便调用方进一步处理
        ElMessage.error(wrapped.message || '请求失败')
        return Promise.reject(wrapped)
      }
      return wrapped.data
    }
    // 非 Result 格式（极少见，可能是文件下载等场景），原样返回
    return wrapped
  },

  // ---- 失败分支（HTTP 非 2xx 或网络异常） ----
  (err: AxiosError<any>) => {
    const status = err.response?.status
    const msg = err.response?.data?.message || err.message

    if (status === 401) {
      // 未登录或 token 过期：清掉本地登录态并跳登录页
      // 注：登录页通过 query.redirect 保留来源路径，便于登录后回跳
      ElMessage.error('未登录或登录已过期')
      localStorage.removeItem('token')
      router.push('/login')
    } else if (status === 403) {
      // 已登录但无权限：仅提示，不动登录态
      ElMessage.error('无权限')
    } else if (status === 404) {
      ElMessage.error(msg || '资源不存在')
    } else {
      // 其余错误（5xx、网络断开、超时等）
      ElMessage.error(msg || '网络错误')
    }
    return Promise.reject(err)
  }
)

export default request