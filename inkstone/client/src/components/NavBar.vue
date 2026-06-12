<template>
  <nav class="navbar glass-card">
    <div class="nav-inner">
      <router-link to="/" class="logo">
        <span class="logo-icon">&#x1f58b;</span>
        <span class="logo-text">墨池</span>
      </router-link>
      <div class="nav-links">
        <router-link to="/write">写作</router-link>
        <router-link to="/explore">广场</router-link>
        <router-link to="/challenges">挑战</router-link>
        <NotificationBell />
        <template v-if="userStore.isLoggedIn">
          <div class="avatar-wrapper" @click="menuOpen = !menuOpen" v-click-outside="() => menuOpen = false">
            <img v-if="userStore.user?.avatar" :src="userStore.user.avatar" class="avatar-link-img" />
            <div v-else class="avatar-link">
              {{ userStore.user?.username?.charAt(0) }}
            </div>
            <transition name="fade">
              <div class="dropdown-menu glass-card" v-if="menuOpen" @click.stop>
                <router-link :to="`/profile/${userStore.user?.user_id}`" @click="menuOpen = false">我的主页</router-link>
                <router-link to="/works" @click="menuOpen = false">我的作品</router-link>
                <router-link to="/stats" @click="menuOpen = false">数据洞察</router-link>
                <router-link to="/notifications" @click="menuOpen = false">消息中心</router-link>
                <hr>
                <a href="#" @click.prevent="handleLogout">退出登录</a>
              </div>
            </transition>
          </div>
        </template>
        <template v-else>
          <router-link to="/login" class="btn btn-outline btn-sm">登录</router-link>
        </template>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user.js'
import { api } from '../api/index.js'
import NotificationBell from './NotificationBell.vue'

const userStore = useUserStore()
const router = useRouter()
const menuOpen = ref(false)

async function handleLogout() {
  menuOpen.value = false
  await api.post('/api/auth/logout')
  userStore.logout()
  router.push('/')
}

const vClickOutside = {
  mounted(el, binding) {
    el._clickOutside = (e) => {
      if (!el.contains(e.target)) binding.value()
    }
    document.addEventListener('click', el._clickOutside)
  },
  unmounted(el) {
    document.removeEventListener('click', el._clickOutside)
  }
}
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  border-radius: 0;
  border-top: none;
  border-left: none;
  border-right: none;
  height: 64px;
}
.nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-xl);
}
.logo {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary);
}
.logo-icon { font-size: 1.5rem; }
.nav-links {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
}
.nav-links a {
  color: var(--text-secondary);
  font-size: 0.9rem;
  transition: color var(--transition-fast);
}
.nav-links a:hover,
.nav-links a.router-link-active { color: var(--accent-primary); }

.avatar-wrapper {
  position: relative;
  cursor: pointer;
}
.avatar-link {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: var(--accent-primary);
  color: var(--bg-primary) !important;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.85rem;
}
.avatar-link-img {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  object-fit: cover;
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 160px;
  padding: var(--space-xs) 0;
  display: flex;
  flex-direction: column;
  z-index: 200;
}
.dropdown-menu a {
  padding: 10px 16px;
  color: var(--text-secondary);
  font-size: 0.85rem;
  transition: all var(--transition-fast);
}
.dropdown-menu a:hover {
  background: rgba(196,163,90,0.08);
  color: var(--accent-primary);
}
.dropdown-menu hr {
  border: none;
  border-top: 1px solid var(--border-glass);
  margin: 4px 0;
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.btn-sm { padding: 4px 14px; font-size: 0.85rem; }
</style>
