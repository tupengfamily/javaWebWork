/**
 * URL Query 状态同步工具
 *
 * 解决两个 UX 问题：
 * 1. 刷新页面后筛选条件丢失
 * 2. 用户无法通过 URL 分享/收藏特定筛选状态
 *
 * 设计为最小依赖的纯函数式 API，避免引入 vueuse/router 的额外 query 反序列化逻辑。
 */
import type { LocationQueryRaw } from 'vue-router'

/**
 * 将对象序列化为 URL query（仅写入非空字段）
 */
export function toQuery(obj: Record<string, any>): LocationQueryRaw {
  const out: LocationQueryRaw = {}
  for (const [k, v] of Object.entries(obj)) {
    if (v === undefined || v === null) continue
    if (typeof v === 'string' && v === '') continue
    if (typeof v === 'number' && Number.isNaN(v)) continue
    out[k] = String(v)
  }
  return out
}

/**
 * 从 URL query 读取字段，提供类型安全的默认值
 *
 * 用法：
 *   const filters = reactive({
 *     site: readQuery(route.query, 'site', '') as string,
 *     pageNum: readQuery(route.query, 'pageNum', 1) as number,
 *   })
 */
export function readQuery<T>(query: Record<string, any>, key: string, fallback: T): T {
  const raw = query[key]
  if (raw === undefined || raw === null || raw === '') return fallback
  if (typeof fallback === 'number') {
    const n = Number(Array.isArray(raw) ? raw[0] : raw)
    return (Number.isFinite(n) ? n : fallback) as T
  }
  return (Array.isArray(raw) ? raw[0] : raw) as T
}