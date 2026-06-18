import { defineStore } from 'pinia'

import { request } from '../api'

const TOKEN_KEY = 'smawell-store-token'
const USER_KEY = 'smawell-store-user'

export const useAuthStore = defineStore('store-auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: JSON.parse(localStorage.getItem(USER_KEY) || 'null'),
    initialized: false,
    loading: false,
    error: '',
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.token && state.user),
  },
  actions: {
    async initialize() {
      if (!this.token || !this.user) {
        this.clearLocalAuth()
        this.initialized = true
        return
      }

      try {
        const data = await request('/api/auth/me', {
          headers: {
            Authorization: `Bearer ${this.token}`,
          },
        })
        this.user = data.user
        localStorage.setItem(USER_KEY, JSON.stringify(this.user))
      } catch {
        this.clearLocalAuth()
      } finally {
        this.initialized = true
      }
    },
    async login(payload) {
      this.loading = true
      this.error = ''

      try {
        const data = await request('/api/auth/store/login', {
          method: 'POST',
          body: JSON.stringify({
            email: String(payload?.email || '')
              .trim()
              .toLowerCase(),
            password: String(payload?.password || '').trim(),
          }),
        })
        this.user = data.user
        this.token = data.token
        localStorage.setItem(TOKEN_KEY, this.token)
        localStorage.setItem(USER_KEY, JSON.stringify(data.user))
        return true
      } catch (error) {
        this.error = error.message || 'Login failed'
        return false
      } finally {
        this.loading = false
      }
    },
    async logout() {
      try {
        if (this.token) {
          await request('/api/auth/logout', {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${this.token}`,
            },
          })
        }
      } catch {
        // Ignore logout failures and clear local session anyway.
      } finally {
        this.clearLocalAuth()
      }
    },
    clearLocalAuth() {
      this.token = ''
      this.user = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },
  },
})
