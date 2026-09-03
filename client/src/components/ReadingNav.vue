<template>
  <!-- 中央液态玻璃导航栏 -->
  <nav class="reading-navbar">
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
        <router-link to="/bookshelf" class="nav-item">书架</router-link>
        <router-link to="/library?from=reading" class="nav-item">书库</router-link>
        <router-link to="/annotations" class="nav-item">批注</router-link>
        <router-link to="/highlights" class="nav-item">好句</router-link>
        <router-link to="/reading-report" class="nav-item">报告</router-link>
      </div>
    </LiquidGlass>
  </nav>

  <!-- 左上角墨池标志 + 写作入口 -->
  <div class="corner-area">
    <InkstoneLogo />
    <LiquidGlass :radius="20" :frost="0.08" :scale="-120" :blur="8" :border="0.06" :lightness="50" :alpha="0.9">
      <router-link to="/write" class="switch-btn">写作</router-link>
    </LiquidGlass>
  </div>

  <!-- 右上角用户区域 -->
  <div class="user-area">
    <template v-if="userStore.isLoggedIn">
      <div class="avatar-wrapper" @click.stop="toggleMenu">
        <img v-if="userStore.user?.avatar" :src="userStore.user.avatar" class="avatar-img" />
        <div v-else class="avatar-placeholder">
          {{ userStore.user?.username?.charAt(0) }}
        </div>
        <transition name="fade">
          <div class="dropdown-menu glass-card" v-if="menuOpen" @click.stop>
            <router-link :to="`/profile/${userStore.user?.user_id}?from=reading`" @click="menuOpen = false">个人主页</router-link>
            <router-link to="/bookshelf" @click="menuOpen = false">我的书架</router-link>
            <router-link to="/my-records" @click="menuOpen = false">我的记录</router-link>
            <router-link to="/reading-report" @click="menuOpen = false">阅读报告</router-link>
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

const router = useRouter()
const userStore = useUserStore()
const menuOpen = ref(false)

function toggleMenu() {
  menuOpen.value = !menuOpen.value
}

function onDocumentClick() {
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
/* 中央导航栏 */
.reading-navbar {
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
  width: 380px;
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

/* 左上角标志 + 切换按钮 */
.corner-area {
  position: fixed;
  top: 16px;
  left: 24px;
  z-index: 101;
  display: flex;
  align-items: center;
  gap: 12px;
}
.switch-btn {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
  text-decoration: none;
  padding: 6px 16px;
  letter-spacing: 0.02em;
  transition: color 0.25s ease;
}
.switch-btn:hover {
  color: var(--accent-primary);
}

/* 右上角用户区域 */
.user-area {
  position: fixed;
  top: 16px;
  right: 24px;
  z-index: 101;
}

.login-btn {
  padding: 8px 24px;
  border: 1px solid var(--accent-primary);
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--accent-primary);
  text-decoration: none;
  transition: all 0.3s ease;
  background: rgba(15,15,26,0.85);
  backdrop-filter: blur(16px);
  letter-spacing: 0.02em;
}

.login-btn:hover {
  background: rgba(196, 163, 90, 0.15);
  box-shadow: 0 4px 16px rgba(196,163,90,0.3);
  transform: translateY(-2px);
}

/* 头像 */
.avatar-wrapper {
  position: relative;
  cursor: pointer;
}

.avatar-placeholder {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-warm));
  color: var(--bg-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  border: 2px solid rgba(196,163,90,0.3);
  box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}

.avatar-placeholder:hover {
  transform: scale(1.1);
  box-shadow: 0 0 20px rgba(196, 163, 90, 0.5);
  border-color: var(--accent-primary);
}

.avatar-img {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  object-fit: cover;
  transition: all 0.3s ease;
  border: 2px solid rgba(196,163,90,0.3);
  box-shadow: 0 4px 16px rgba(0,0,0,0.3);
}

.avatar-img:hover {
  transform: scale(1.1);
  box-shadow: 0 0 20px rgba(196, 163, 90, 0.5);
  border-color: var(--accent-primary);
}

/* 下拉菜单 */
.dropdown-menu {
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  min-width: 180px;
  padding: 8px 0;
  display: flex;
  flex-direction: column;
  z-index: 200;
  background: rgba(20,20,35,0.95);
  backdrop-filter: blur(32px) saturate(180%);
  -webkit-backdrop-filter: blur(32px) saturate(180%);
  border: 1px solid rgba(196,163,90,0.2);
  border-radius: 12px;
  box-shadow: 0 16px 48px rgba(0,0,0,0.4);
}

.dropdown-menu a {
  padding: 12px 20px;
  color: var(--text-secondary);
  font-size: 0.88rem;
  transition: all 0.15s ease;
  text-decoration: none;
  border-bottom: 1px solid rgba(255,255,255,0.03);
}

.dropdown-menu a:last-child {
  border-bottom: none;
}

.dropdown-menu a:hover {
  background: rgba(196, 163, 90, 0.1);
  color: var(--accent-primary);
}

.dropdown-menu hr {
  border: none;
  border-top: 1px solid rgba(196,163,90,0.1);
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

@media (max-width: 768px) {
  .nav-links { width: 300px; }
  .nav-item { width: 46px; font-size: 0.78rem; }
}
</style>
