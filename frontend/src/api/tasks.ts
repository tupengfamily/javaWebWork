import request from '@/utils/request'
import type { PageResp } from './rankings'

export interface TaskVO {
  id: number
  siteCode: string
  siteName: string
  rankingType: string
  category: string | null
  triggerType: 'manual' | 'scheduled'
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled'
  progress: number
  fetchedCount: number
  errorMessage: string | null
  createdBy: string | null
  createdAt: string
  startedAt: string | null
  finishedAt: string | null
  durationMs: number | null
}

export const listTasks = (params: any) =>
  request.get<any, PageResp<TaskVO>>('/admin/tasks', { params })

export const createTask = (data: { siteCode: string; rankingType: string; category?: string }) =>
  request.post<any, { taskId: number }>('/admin/tasks', data)

export const cancelTask = (id: number) => request.post(`/admin/tasks/${id}/cancel`)

export const retryTask = (id: number) => request.post<any, { taskId: number }>(`/admin/tasks/${id}/retry`)

export const getTaskLog = (id: number) =>
  request.get<any, { task: TaskVO; logs: { time: string; level: string; message: string }[] }>(`/admin/tasks/${id}/log`)

export const listDashboardLogs = (params: { level?: string; site?: string; limit?: number; before?: string } = {}) =>
  request.get<any, { records: { time: string; level: string; site: string; message: string }[]; nextBefore: string }>('/admin/dashboard/logs', { params })

export const dashboardSites = () =>
  request.get<any, {
    siteId: number
    siteCode: string
    siteName: string
    color: string
    enabled: boolean
    lastTask: { id: number; status: string; finishedAt: string; fetchedCount: number } | null
    novelCount: number
    recentFailureCount: number
  }[]>('/admin/dashboard/sites')
