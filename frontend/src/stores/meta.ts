import { defineStore } from 'pinia'
import { listRankingTypes, listCategories } from '@/api/meta'

export const useMetaStore = defineStore('meta', {
  state: () => ({
    rankingTypes: [] as { code: string; name: string; description: string }[],
    categories: [] as string[]
  }),
  actions: {
    async loadAll() {
      const [rt, cats] = await Promise.all([listRankingTypes(), listCategories()])
      this.rankingTypes = rt
      this.categories = cats
    }
  }
})
