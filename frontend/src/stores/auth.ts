import { defineStore } from 'pinia'
import { login as apiLogin, register as apiRegister, logout as apiLogout, fetchMe } from '@/api/auth'

interface UserInfo {
  id: number
  username: string
  role: string
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '' as string,
    user: null as UserInfo | null,
    loaded: false
  }),
  getters: {
    isLogin: (s) => !!s.token,
    isAdmin: (s) => s.user?.role === 'admin',
    isReady: (s) => s.loaded || !s.token
  },
  actions: {
    async register(username: string, password: string) {
      const resp = await apiRegister({ username, password })
      this.token = resp.token
      this.user = resp.user
      this.loaded = true
      localStorage.setItem('token', resp.token)
      return resp
    },
    async login(username: string, password: string) {
      const resp = await apiLogin({ username, password })
      this.token = resp.token
      this.user = resp.user
      this.loaded = true
      localStorage.setItem('token', resp.token)
      return resp
    },
    async fetchMe() {
      try {
        const me = await fetchMe()
        this.user = me
      } catch {
        // token 过期或无效 → 清除状态
        this.token = ''
        this.user = null
        localStorage.removeItem('token')
      } finally {
        this.loaded = true
      }
    },
    async logout() {
      try { await apiLogout() } catch {}
      this.token = ''
      this.user = null
      this.loaded = false
      localStorage.removeItem('token')
    }
  }
})
