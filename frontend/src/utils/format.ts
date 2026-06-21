/**
 * 通用格式化工具函数
 *
 * 集中放置数字/时间等格式化逻辑，避免在多个 view 中复制粘贴。
 * 若新增格式化函数请优先放此处并补充注释。
 */
import dayjs from 'dayjs'

/**
 * 将整数格式化为"万 / 亿"为单位的可读字符串
 *
 * 规则：
 *  - null/undefined → '-'
 *  - >= 1亿          → "X.XX亿"
 *  - >= 1万          → "X.X万"
 *  - 其余           → 原值
 *
 * @example
 *   formatNum(12345)        // "1.2万"
 *   formatNum(120_000_000)  // "1.20亿"
 *   formatNum(999)          // "999"
 *   formatNum(null)         // "-"
 */
export const formatNum = (n: number | null | undefined): string => {
  if (n === null || n === undefined) return '-'
  if (n >= 1e8) return (n / 1e8).toFixed(2) + '亿'
  if (n >= 1e4) return (n / 1e4).toFixed(1) + '万'
  return String(n)
}

/**
 * 将 ISO / LocalDateTime 字符串格式化为 "MM-DD HH:mm"
 *
 * 用于列表/详情页中展示紧凑时间，空值返回 '-'。
 * 解析失败时回退到原字符串，便于排查异常数据。
 */
export const formatShortTime = (t?: string | null): string => {
  if (!t) return '-'
  if (typeof t !== 'string') return String(t)
  const d = dayjs(t)
  return d.isValid() ? d.format('MM-DD HH:mm') : t
}

/**
 * 将 ISO / LocalDateTime 字符串格式化为 "MM-DD HH:mm:ss"
 *
 * 用于任务/日志等需要秒级精度的场景。
 */
export const formatFullTime = (t?: string | null): string => {
  if (!t) return '-'
  if (typeof t !== 'string') return String(t)
  const d = dayjs(t)
  return d.isValid() ? d.format('MM-DD HH:mm:ss') : t
}