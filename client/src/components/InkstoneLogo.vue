<template>
  <router-link to="/" class="inkstone-logo" :class="{ compact }">
    <svg
      class="logo-mark"
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <!-- 墨池砚台 -->
      <ellipse cx="20" cy="22" rx="15" ry="5" stroke="currentColor" stroke-width="1.5" fill="none" opacity="0.7" />
      <ellipse cx="20" cy="22" rx="12" ry="3.5" stroke="currentColor" stroke-width="0.8" fill="none" opacity="0.4" />
      <!-- 墨滴 -->
      <path
        d="M20 4 C20 4 16 12 16 16 C16 18.2 17.8 20 20 20 C22.2 20 24 18.2 24 16 C24 12 20 4 20 4Z"
        fill="currentColor"
        opacity="0.9"
      />
      <!-- 墨滴高光 -->
      <ellipse cx="19" cy="14" rx="1.5" ry="2.5" fill="white" opacity="0.25" />
      <!-- 涟漪 -->
      <ellipse cx="20" cy="26" rx="6" ry="1.5" stroke="currentColor" stroke-width="0.6" fill="none" opacity="0.5" />
      <ellipse cx="20" cy="29" rx="10" ry="2" stroke="currentColor" stroke-width="0.4" fill="none" opacity="0.3" />
    </svg>
    <span class="logo-text">墨池</span>
  </router-link>
</template>

<script setup>
defineProps({
  compact: { type: Boolean, default: false }
})
</script>

<style scoped>
.inkstone-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  text-decoration: none;
  color: var(--accent-primary);
  transition: all 0.3s ease;
}

.inkstone-logo:hover {
  color: #d4b86a;
  filter: drop-shadow(0 0 8px rgba(196, 163, 90, 0.5));
}

.logo-mark {
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  transition: transform 0.3s ease;
}

.inkstone-logo:hover .logo-mark {
  transform: scale(1.08);
}

.compact .logo-mark {
  width: 22px;
  height: 22px;
}

.logo-text {
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: 2px;
  background: linear-gradient(135deg, #c4a35a, #d4b86a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.compact .logo-text {
  font-size: 0.95rem;
  letter-spacing: 1px;
}
</style>
