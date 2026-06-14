/**
 * Tests for meta store
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useMetaStore } from '@/stores/meta'

vi.mock('@/api/meta', () => ({
  listRankingTypes: vi.fn(),
  listCategories: vi.fn()
}))

import * as metaApi from '@/api/meta'

describe('meta store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initial state - empty', () => {
    const meta = useMetaStore()
    expect(meta.rankingTypes).toEqual([])
    expect(meta.categories).toEqual([])
  })

  it('loadAll - fetches both', async () => {
    const meta = useMetaStore()
    vi.mocked(metaApi.listRankingTypes).mockResolvedValue([
      { code: 'daily', name: 'Daily', description: '' },
      { code: 'monthly', name: 'Monthly', description: '' }
    ] as any)
    vi.mocked(metaApi.listCategories).mockResolvedValue(['Xuanhuan', 'Dushi'])

    await meta.loadAll()
    expect(meta.rankingTypes).toHaveLength(2)
    expect(meta.categories).toEqual(['Xuanhuan', 'Dushi'])
  })

  it('loadAll - failure leaves empty (no crash)', async () => {
    const meta = useMetaStore()
    vi.mocked(metaApi.listRankingTypes).mockRejectedValue(new Error('network'))
    vi.mocked(metaApi.listCategories).mockRejectedValue(new Error('network'))
    await expect(meta.loadAll()).rejects.toThrow('network')
  })
})
