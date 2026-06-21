import request from '@/utils/request'

export interface RankingItemVO {
  rank: number
  novelId: number
  title: string
  author: string
  category: string
  coverUrl: string
  viewCount: number
  recCount: number
  wordCount: number
  status: string
  description: string
  novelUrl: string
  crawlTime?: string
}

export interface PageResp<T> {
  records: T[]
  total: number
  pageNum: number
  pageSize: number
  pages: number
}

export interface TrendSeries {
  novelId: number
  title: string
  siteCode: string
  color: string
  points: { time: string; value: number }[]
}

export const listRankings = (params: {
  site: string
  type: string
  category?: string
  keyword?: string
  pageNum?: number
  pageSize?: number
}) => request.get<any, PageResp<RankingItemVO>>('/rankings', { params })

export const compareTrend = (params: {
  novelIds: number[]
  metric: 'rank' | 'viewCount' | 'recCount'
  days?: number
}) => request.get<any, { metric: string; series: TrendSeries[] }>('/trends/compare', { params: { ...params, novelIds: params.novelIds.join(',') } })

export const topList = (params: { limit?: number; by?: string; category?: string } = {}) =>
  request.get<any, any[]>('/trends/top', { params })
