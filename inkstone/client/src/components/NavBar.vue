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
        <router-link to="/library?from=write" class="nav-item">书库</router-link>
        <router-link to="/explore" class="nav-item">广场</router-link>
        <router-link to="/poems" class="nav-item">诗词</router-link>
        <router-link to="/materials" class="nav-item">素材</router-link>
        <router-link to="/daily" class="nav-item">练习</router-link>
        <router-link to="/rankings" class="nav-item">排行</router-link>
        <router-link to="/challenges" class="nav-item">挑战</router-link>
      </div>
    </LiquidGlass>
  </nav>

  <!-- 左上角标志 + 阅读入口 -->
  <div class="corner-area">
    <InkstoneLogo />
    <router-link to="/bookshelf" class="switch-btn">阅读</router-link>
  </div>

  <!-- 右上角头像（独立于导航栏，相对于视口定位） -->
  <div class="user-area">
    <UserMenu />
  </div>
</template>

<script setup>
import LiquidGlass from './LiquidGlass.vue'
import InkstoneLogo from './InkstoneLogo.vue'
import UserMenu from './UserMenu.vue'
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
