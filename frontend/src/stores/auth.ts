import { defineStore } from 'pinia'
import { login as apiLogin, logout as apiLogout, fetchMe } from '@/api/auth'

interface UserInfo {
  id: number
  username: string
  role: string
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '' as string,
    user: null as UserInfo | null
  }),
  getters: {
    isLogin: (s) => !!s.token,
    isAdmin: (s) => s.user?.role === 'admin'
  },
  actions: {
    async login(username: string, password: string) {
      const resp = await apiLogin({ username, password })
      this.token = resp.token
      this.user = resp.user
      localStorage.setItem('token', resp.token)
      return resp
    },
    async fetchMe() {
      const me = await fetchMe()
      this.user = me
      return me
    },
    async logout() {
      try { await apiLogout() } catch {}
      this.token = ''
      this.user = null
      localStorage.removeItem('token')
    }
  }
})
