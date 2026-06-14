import request from '@/utils/request'

export interface ScheduleConfig {
  dailyCrawlTimes: string[]
  maxConcurrentTasks: number
  taskTimeoutMinutes: number
  crawlAllRankingTypes: string[]
  updatedAt: string
}

export const getSchedule = () => request.get<any, ScheduleConfig>('/admin/schedule')
export const updateSchedule = (data: Partial<ScheduleConfig>) => request.put('/admin/schedule', data)
