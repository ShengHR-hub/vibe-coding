<template>
  <nav class="navbar">
    <LiquidGlass
      :radius="24"
      :frost="0.08"
      :scale="-120"
      :blur="8"
      :border="0.06"
      :lightness="50"
      :alpha="0.9"
    >
      <div class="nav-links">
        <router-link to="/write" class="nav-item">写作</router-link>
        <router-link to="/explore" class="nav-item">广场</router-link>
        <router-link to="/challenges" class="nav-item">挑战</router-link>
      </div>
    </LiquidGlass>
  </nav>

  <!-- 左上角标志 -->
  <InkstoneLogo class="corner-logo" />

  <!-- 右上角头像（独立于导航栏，相对于视口定位） -->
  <div class="user-area">
    <template v-if="userStore.isLoggedIn">
      <div class="avatar-wrapper" @click.stop="toggleMenu">
        <img v-if="userStore.user?.avatar" :src="userStore.user.avatar" class="avatar-img" />
        <div v-else class="avatar-placeholder">
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
      <router-link to="/login" class="login-btn">登录</router-link>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user.js'
import { api } from '../api/index.js'
import LiquidGlass from './LiquidGlass.vue'
import InkstoneLogo from './InkstoneLogo.vue'

const userStore = useUserStore()
const router = useRouter()
const menuOpen = ref(false)

function toggleMenu() {
  menuOpen.value = !menuOpen.value
}

function closeMenu() {
  menuOpen.value = false
}

function onDocumentClick(e) {
  // 关闭菜单（如果点击在头像区域外）
  if (menuOpen.value) {
    menuOpen.value = false
  }
}

async function handleLogout() {
  menuOpen.value = false
  await api.post('/api/auth/logout')
  userStore.logout()
  router.push('/')
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
})

onUnmounted(() => {
  document.removeEventListener('click', onDocumentClick)
})
</script>

<style scoped>
.navbar {
  position: fixed;
  top: 16px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  width: auto;
}

.nav-links {
  display: flex;
  align-items: center;
  justify-content: space-evenly;
  padding: 6px 10px;
  width: 300px;
}

.nav-item {
  position: relative;
  padding: 8px 0;
  border-radius: 20px;
  width: 72px;
  text-align: center;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-secondary);
  transition: all 0.3s ease;
  text-decoration: none;
  white-space: nowrap;
}

.nav-item:hover {
  color: var(--text-primary);
}

.nav-item.router-link-active {
  color: var(--accent-primary);
  background: rgba(196, 163, 90, 0.1);
}

/* 左上角标志 */
.corner-logo {
  position: fixed;
  top: 16px;
  left: 24px;
  z-index: 101;
}

/* 右上角用户区域 */
.user-area {
  position: fixed;
  top: 16px;
  right: 24px;
  z-index: 101;
}

.login-btn {
  padding: 8px 20px;
  border: 1px solid var(--accent-primary);
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--accent-primary);
  text-decoration: none;
  transition: all 0.3s ease;
  background: rgba(196, 163, 90, 0.06);
}

.login-btn:hover {
  background: rgba(196, 163, 90, 0.15);
}

/* 头像 */
.avatar-wrapper {
  position: relative;
  cursor: pointer;
}

.avatar-placeholder {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--accent-primary);
  color: var(--bg-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.avatar-placeholder:hover {
  transform: scale(1.1);
  box-shadow: 0 0 12px rgba(196, 163, 90, 0.4);
}

.avatar-img {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.avatar-img:hover {
  transform: scale(1.1);
  box-shadow: 0 0 12px rgba(196, 163, 90, 0.4);
}

/* 下拉菜单 */
.dropdown-menu {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 150px;
  padding: 4px 0;
  display: flex;
  flex-direction: column;
  z-index: 200;
}

.dropdown-menu a {
  padding: 10px 16px;
  color: var(--text-secondary);
  font-size: 0.85rem;
  transition: all 0.15s ease;
  text-decoration: none;
}

.dropdown-menu a:hover {
  background: rgba(196, 163, 90, 0.08);
  color: var(--accent-primary);
}

.dropdown-menu hr {
  border: none;
  border-top: 1px solid var(--border-glass);
  margin: 4px 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
