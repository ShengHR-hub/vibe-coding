<template>
  <div class="auth-wrapper">
    <div class="auth-decor" aria-hidden="true">
      <span class="ink-blot ink-1"></span>
      <span class="ink-blot ink-2"></span>
      <span class="ink-char ink-3">墨</span>
      <span class="ink-char ink-4">池</span>
    </div>

    <div class="auth-card">
      <LiquidGlass
        :radius="24"
        :blur="11"
        :alpha="0.93"
        :scale="-180"
        :frost="0.05"
        :border="0.07"
        :lightness="50"
        :r-offset="0"
        :g-offset="10"
        :b-offset="20"
        blend="difference"
        class="auth-liquid"
      >
        <div class="card-inner">
          <div class="auth-brand">
            <span class="brand-mark">&#10045;</span>
          </div>
          <h2 class="auth-title">注册墨池</h2>
          <p class="auth-sub">提笔入墨，自此为家</p>

          <form @submit.prevent="handleRegister" class="auth-form">
            <div class="input-group">
              <span class="input-icon">&#9998;</span>
              <input
                v-model="username"
                type="text"
                placeholder="用户名"
                required
                autocomplete="username"
              />
              <span class="input-underline"></span>
            </div>

            <div class="input-group">
              <span class="input-icon">&#9900;</span>
              <input
                v-model="password"
                type="password"
                placeholder="密码"
                required
                autocomplete="new-password"
              />
              <span class="input-underline"></span>
            </div>

            <div class="input-group">
              <span class="input-icon">&#9900;</span>
              <input
                v-model="confirmPassword"
                type="password"
                placeholder="确认密码"
                required
                autocomplete="new-password"
              />
              <span class="input-underline"></span>
            </div>

            <button type="submit" class="auth-btn" :disabled="loading">
              <span class="btn-text">{{ loading ? '注册中...' : '注 册' }}</span>
              <span class="btn-shine"></span>
            </button>
          </form>

          <p class="auth-switch">
            已有账号？<router-link to="/login">去登录</router-link>
          </p>
        </div>
      </LiquidGlass>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user.js'
import LiquidGlass from '../components/LiquidGlass.vue'

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
.auth-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 80px);
  position: relative;
}

.auth-decor {
  position: fixed; inset: 0; pointer-events: none; z-index: 0;
}
.ink-blot {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.06;
  animation: inkFloat 8s ease-in-out infinite;
}
.ink-blot.ink-1 {
  width: 300px; height: 300px;
  background: radial-gradient(circle, var(--accent-primary), transparent 70%);
  top: 15%; left: 10%;
  animation-delay: 0s;
}
.ink-blot.ink-2 {
  width: 240px; height: 240px;
  background: radial-gradient(circle, var(--accent-purple), transparent 70%);
  bottom: 20%; right: 8%;
  animation-delay: -4s;
}
.ink-char {
  position: absolute;
  font-family: var(--font-calligraphy);
  font-size: 8rem;
  opacity: 0.03;
  color: var(--accent-primary);
  animation: inkFloat 10s ease-in-out infinite;
}
.ink-char.ink-3 { top: 5%; right: 15%; animation-delay: -2s; }
.ink-char.ink-4 { bottom: 8%; left: 12%; animation-delay: -6s; font-size: 6rem; }

@keyframes inkFloat {
  0%, 100% { transform: translateY(0) scale(1); }
  25% { transform: translateY(-12px) scale(1.05); }
  50% { transform: translateY(6px) scale(0.97); }
  75% { transform: translateY(-8px) scale(1.03); }
}

.auth-card {
  position: relative;
  width: 100%;
  max-width: 420px;
  z-index: 1;
}

.auth-liquid {
  width: 100%;
}

.card-inner {
  padding: 2.5rem 2rem;
}

.auth-brand {
  display: flex;
  justify-content: center;
  margin-bottom: 0.5rem;
}
.brand-mark {
  font-size: 2.4rem;
  color: var(--accent-primary);
  opacity: 0.5;
  animation: markPulse 3s ease-in-out infinite;
}
@keyframes markPulse {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.08); }
}

.auth-title {
  text-align: center;
  font-family: var(--font-serif);
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--text-primary);
  margin-bottom: 0.3rem;
}
.auth-sub {
  text-align: center;
  font-size: 0.8rem;
  color: var(--text-muted);
  letter-spacing: 0.1em;
  margin-bottom: 2rem;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.input-group {
  position: relative;
  display: flex;
  align-items: center;
}
.input-icon {
  position: absolute;
  left: 14px;
  font-size: 0.95rem;
  color: var(--text-muted);
  z-index: 1;
  transition: color 0.3s ease;
  pointer-events: none;
}
.input-group input {
  width: 100%;
  padding: 12px 14px 12px 40px;
  font-size: 0.95rem;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(196, 163, 90, 0.12);
  border-radius: 10px;
  color: var(--text-primary);
  outline: none;
  transition: border-color 0.3s ease, box-shadow 0.3s ease, background 0.3s ease;
}
.input-group input::placeholder {
  color: var(--text-muted);
  opacity: 0.5;
}
.input-underline {
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--accent-primary), transparent);
  transition: width 0.4s ease, left 0.4s ease;
}
.input-group input:focus {
  border-color: rgba(196, 163, 90, 0.4);
  box-shadow: 0 0 0 4px rgba(196, 163, 90, 0.05), 0 0 20px rgba(196, 163, 90, 0.06);
  background: rgba(255, 255, 255, 0.06);
}
.input-group input:focus ~ .input-underline {
  width: 100%;
  left: 0;
}
.input-group:has(input:focus) .input-icon {
  color: var(--accent-primary);
}

.auth-btn {
  position: relative;
  width: 100%;
  padding: 12px;
  margin-top: 0.5rem;
  font-size: 0.95rem;
  font-weight: 600;
  letter-spacing: 0.25em;
  color: var(--bg-primary);
  background: linear-gradient(135deg, #c4a35a 0%, #9b7d3c 100%);
  border: none;
  border-radius: 10px;
  cursor: pointer;
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.3s ease;
}
.auth-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 30px rgba(196, 163, 90, 0.3);
}
.auth-btn:active:not(:disabled) {
  transform: translateY(0);
}
.auth-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-text {
  position: relative;
  z-index: 1;
}

.btn-shine {
  position: absolute;
  top: 0; left: -100%;
  width: 60%; height: 100%;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.13),
    transparent
  );
  transform: skewX(-25deg);
}
.auth-btn:hover:not(:disabled) .btn-shine {
  animation: shine 0.75s ease forwards;
}
@keyframes shine {
  to { left: 120%; }
}

.auth-switch {
  text-align: center;
  margin-top: 1.5rem;
  font-size: 0.85rem;
  color: var(--text-muted);
}
.auth-switch a {
  color: var(--accent-primary);
  font-weight: 500;
  transition: color 0.2s;
}
.auth-switch a:hover {
  color: var(--accent-secondary);
}

@media (max-width: 480px) {
  .card-inner {
    padding: 2rem 1.25rem;
  }
  .auth-title {
    font-size: 1.3rem;
  }
}
</style>
