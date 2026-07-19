import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api/index.js'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const initialized = ref(false)
  const isLoggedIn = computed(() => !!user.value)

  async function fetchUser() {
    try {
      const res = await api.get('/api/auth/me')
      if (res.code === 0) {
        user.value = res.data
      } else if (res.code === -1) {
        // 网络错误，保持当前状态不清除用户
        console.warn('[UserStore] Network error during fetchUser, keeping current state')
      } else {
        user.value = null
      }
    } catch {
      // 异常也保持当前状态
      console.warn('[UserStore] Unexpected error during fetchUser')
    }
    initialized.value = true
    return { code: user.value ? 0 : -1 }
  }

  async function login(username, password) {
    const res = await api.post('/api/auth/login', { username, password })
    if (res.code === 0) {
      user.value = res.data
    }
    return res
  }

  async function register(username, password) {
    const res = await api.post('/api/auth/register', { username, password })
    return res
  }

  async function logout() {
    await api.post('/api/auth/logout')
    user.value = null
  }

  return { user, initialized, isLoggedIn, fetchUser, login, register, logout }
})
