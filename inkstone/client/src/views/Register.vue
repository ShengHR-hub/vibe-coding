<template>
  <div class="page-container auth-page">
    <div class="auth-card glass-card">
      <h2>注册墨池</h2>
      <form @submit.prevent="handleRegister">
        <input v-model="username" placeholder="用户名" required />
        <input v-model="password" type="password" placeholder="密码" required />
        <input v-model="confirmPassword" type="password" placeholder="确认密码" required />
        <button type="submit" class="btn btn-primary btn-full" :disabled="loading">
          {{ loading ? '注册中...' : '注册' }}
        </button>
      </form>
      <p class="auth-switch">已有账号？<router-link to="/login">去登录</router-link></p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user.js'

const router = useRouter()
const userStore = useUserStore()
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const loading = ref(false)

async function handleRegister() {
  if (password.value !== confirmPassword.value) {
    alert('两次密码不一致')
    return
  }
  loading.value = true
  const res = await userStore.register(username.value, password.value)
  loading.value = false
  if (res.code === 0) {
    router.push('/login')
  } else {
    alert(res.msg || '注册失败')
  }
}
</script>

<style scoped>
.auth-page { display: flex; align-items: center; justify-content: center; min-height: calc(100vh - 80px - 6rem); }
.auth-card { padding: var(--space-2xl); width: 100%; max-width: 400px; }
.auth-card h2 { text-align: center; margin-bottom: var(--space-xl); font-size: 1.5rem; }
form { display: flex; flex-direction: column; gap: var(--space-md); }
form input { padding: 10px 14px; font-size: 0.95rem; }
.btn-full { width: 100%; padding: 10px; }
.auth-switch { text-align: center; margin-top: var(--space-lg); color: var(--text-muted); font-size: 0.9rem; }
</style>
