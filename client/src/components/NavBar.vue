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
        <a href="#" class="nav-item" :class="{ active: navActive === 'write' }" @click.prevent="goWrite">写作</a>
        <router-link to="/inspire" class="nav-item" :class="{ active: navActive === 'inspire' }">灵感馆</router-link>
        <router-link to="/explore" class="nav-item" :class="{ active: navActive === 'explore' }">广场</router-link>
        <router-link to="/daily" class="nav-item" :class="{ active: navActive === 'daily' }">练习</router-link>
        <router-link to="/rankings" class="nav-item" :class="{ active: navActive === 'rankings' }">排行</router-link>
        <router-link to="/challenges" class="nav-item" :class="{ active: navActive === 'challenges' }">挑战</router-link>
      </div>
    </LiquidGlass>
  </nav>

  <!-- 左上角标志 + 灵感入口 -->
  <div class="corner-area">
    <InkstoneLogo />
    <router-link to="/inspire" class="switch-btn">灵感</router-link>
  </div>

  <!-- 右上角头像（独立于导航栏，相对于视口定位） -->
  <div class="user-area">
    <UserMenu />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LiquidGlass from './LiquidGlass.vue'
import InkstoneLogo from './InkstoneLogo.vue'
import UserMenu from './UserMenu.vue'

const route = useRoute()
const router = useRouter()

// P6-B7：导航「写作」按用户最近使用的写作系统跳回——
// 路由守卫在进入 /write、/write/new、/write/plain 时已记忆 inkstone_write_mode
function goWrite() {
  const mode = localStorage.getItem('inkstone_write_mode') || ''
  if (mode === 'new') router.push('/write/new')
  else if (mode === 'plain') router.push('/write/plain')
  else if (mode === 'pro') router.push('/write')
  else router.push('/start')
}

// 手动高亮：vue-router 的 router-link-active 只认嵌套路由，
// /write/new、/write/plain、/start 都是平级路由不会自动点亮「写作」，
// 这里按路径前缀统一映射（P6-B6）
const navActive = computed(() => {
  const p = route.path
  if (p === '/write' || p.startsWith('/write/') || p === '/start') return 'write'
  if (p.startsWith('/inspire')) return 'inspire'
  if (p.startsWith('/explore')) return 'explore'
  if (p.startsWith('/daily')) return 'daily'
  if (p.startsWith('/rankings')) return 'rankings'
  if (p.startsWith('/challenges')) return 'challenges'
  return ''
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
  width: 530px;
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

.nav-item.active,
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
  gap: 10px;
}
.switch-btn {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-muted);
  text-decoration: none;
  padding: 4px 12px;
  border: 1px solid var(--border-glass);
  border-radius: 20px;
  transition: all 0.25s ease;
  background: rgba(255, 255, 255, 0.03);
}
.switch-btn:hover {
  color: var(--accent-primary);
  border-color: var(--accent-primary);
  background: rgba(196, 163, 90, 0.08);
}

/* 右上角用户区域 */
.user-area {
  position: fixed;
  top: 16px;
  right: 24px;
  z-index: 101;
}
</style>
