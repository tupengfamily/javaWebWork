/**
 * Tests for auth store
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'

// Mock the API module
vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  logout: vi.fn(),
  fetchMe: vi.fn()
}))

import * as authApi from '@/api/auth'

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.clear()
  })

  it('initial state - no token, no user', () => {
    const auth = useAuthStore()
    expect(auth.token).toBe('')
    expect(auth.user).toBeNull()
    expect(auth.isLogin).toBe(false)
    expect(auth.isAdmin).toBe(false)
  })

  it('login - stores token and user', async () => {
    const auth = useAuthStore()
    vi.mocked(authApi.login).mockResolvedValue({
      token: 'abc.def.ghi',
      expiresIn: 86400,
      user: { id: 1, username: 'admin', role: 'admin' }
    })

    await auth.login('admin', 'admin123')
    expect(auth.token).toBe('abc.def.ghi')
    expect(auth.user).toEqual({ id: 1, username: 'admin', role: 'admin' })
    expect(localStorage.getItem('token')).toBe('abc.def.ghi')
    expect(auth.isLogin).toBe(true)
    expect(auth.isAdmin).toBe(true)
  })

  it('logout - clears state', async () => {
    const auth = useAuthStore()
    vi.mocked(authApi.login).mockResolvedValue({
      token: 'xxx', expiresIn: 1,
      user: { id: 1, username: 'admin', role: 'admin' }
    })
    await auth.login('admin', 'p')
    expect(auth.isLogin).toBe(true)

    vi.mocked(authApi.logout).mockResolvedValue(undefined as any)
    await auth.logout()
    expect(auth.token).toBe('')
    expect(auth.user).toBeNull()
    expect(localStorage.getItem('token')).toBeNull()
    expect(auth.isLogin).toBe(false)
  })

  it('fetchMe - updates user', async () => {
    const auth = useAuthStore()
    vi.mocked(authApi.fetchMe).mockResolvedValue({
      id: 1, username: 'admin', role: 'admin'
    } as any)
    await auth.fetchMe()
    expect(auth.user).toEqual({ id: 1, username: 'admin', role: 'admin' })
  })

  it('isAdmin - false for non-admin', () => {
    const auth = useAuthStore()
    auth.user = { id: 2, username: 'u', role: 'user' }
    expect(auth.isAdmin).toBe(false)
  })
})
