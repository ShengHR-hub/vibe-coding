<template>
  <template v-if="userStore.isLoggedIn">
    <div class="avatar-wrapper" @click.stop="toggleMenu">
      <img v-if="userStore.user?.avatar" :src="userStore.user.avatar" class="avatar-img" />
      <div v-else class="avatar-placeholder">
        {{ userStore.user?.username?.charAt(0) }}
      </div>
      <transition name="fade">
        <div class="dropdown-menu glass-card" v-if="menuOpen" @click.stop>
          <router-link :to="`/profile/${userStore.user?.user_id}`" @click="closeMenu">我的主页</router-link>
          <router-link to="/works" @click="closeMenu">我的作品</router-link>
          <router-link to="/inspire" @click="closeMenu">灵感馆</router-link>
          <router-link to="/stats" @click="closeMenu">数据洞察</router-link>
          <router-link to="/notifications" @click="closeMenu">消息中心</router-link>
          <hr>
          <a href="#" @click.prevent="handleLogout">退出登录</a>
        </div>
      </transition>
    </div>
  </template>
  <template v-else>
    <router-link to="/login" class="login-btn">登录</router-link>
  </template>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user.js'

const userStore = useUserStore()
const router = useRouter()
const menuOpen = ref(false)

function toggleMenu() {
  menuOpen.value = !menuOpen.value
}

function closeMenu() {
  menuOpen.value = false
}

function onDocumentClick() {
  if (menuOpen.value) {
    menuOpen.value = false
  }
}

async function handleLogout() {
  menuOpen.value = false
  await userStore.logout()
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
