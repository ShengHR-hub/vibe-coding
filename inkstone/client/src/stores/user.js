import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '../api/index.js'

export const useUserStore = defineStore('user', () => {
  const user = ref(null)
  const initialized = ref(false)
  const isLoggedIn = computed(() => !!user.value)

  async function fetchUser() {
    const res = await api.get('/api/auth/me')
    if (res.code === 0) {
      user.value = res.data
    }
    initialized.value = true
    return res
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
