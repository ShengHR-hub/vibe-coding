<template>
  <router-link v-if="userStore.isLoggedIn" to="/notifications" class="bell">
    &#x1f514;
    <span v-if="count > 0" class="badge">{{ count > 99 ? '99+' : count }}</span>
  </router-link>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/index.js'
import { useUserStore } from '../stores/user.js'

const route = useRoute()
const userStore = useUserStore()
const count = ref(0)

async function refresh() {
  if (!userStore.isLoggedIn) return
  try {
    const res = await api.get('/api/notifications?page=1&page_size=1')
    if (res.code === 0) count.value = res.data?.unread || 0
  } catch {}
}

onMounted(refresh)
watch(() => route.fullPath, refresh)
</script>

<style scoped>
.bell {
  position: relative;
  font-size: 1.2rem;
  color: var(--text-secondary);
  line-height: 1;
}
.badge {
  position: absolute;
  top: -6px;
  right: -8px;
  background: var(--accent-red);
  color: white;
  font-size: 0.65rem;
  min-width: 16px;
  height: 16px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
}
</style>
