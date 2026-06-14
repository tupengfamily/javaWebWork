import request from '@/utils/request'

export interface SiteVO {
  id: number
  code: string
  name: string
  color: string
  sortOrder: number
}

export const listEnabledSites = () => request.get<any, SiteVO[]>('/sites')

export const listAllSites = () => request.get<any, SiteVO[]>('/admin/sites')
