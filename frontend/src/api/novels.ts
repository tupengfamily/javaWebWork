import request from '@/utils/request'
import type { PageResp } from './rankings'

export interface NovelVO {
  id: number
  siteCode: string
  siteName: string
  title: string
  author: string
  category: string
  coverUrl: string
  novelUrl: string
  wordCount: number
  status: string
  description: string      // rich-crawler-data: 简介
  tags: string             // rich-crawler-data: 逗号分隔标签
  outline: string          // 故事大纲
  characters: string       // 角色说明
  firstSeen: string
  lastCrawlTime: string
}

export const getNovel = (id: number) => request.get<any, NovelVO>(`/novels/${id}`)

export const getNovelRecords = (id: number, params: any) =>
  request.get<any, PageResp<any>>(`/novels/${id}/records`, { params })

export const getNovelTrend = (id: number, params: { type?: string; days?: number } = {}) =>
  request.get<any, {
    ranking: { time: string; value: number }[]
    viewCount: { time: string; value: number }[]
    recCount: { time: string; value: number }[]
  }>(`/novels/${id}/trend`, { params })
