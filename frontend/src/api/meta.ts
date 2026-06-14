import request from '@/utils/request'

export const listRankingTypes = () =>
  request.get<any, { code: string; name: string; description: string }[]>('/meta/ranking-types')

export const listCategories = () => request.get<any, string[]>('/meta/categories')
