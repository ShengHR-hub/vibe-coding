<template>
  <div class="toast-container">
    <TransitionGroup name="toast">
      <div v-for="t in toasts" :key="t.id" class="toast glass-card" :class="t.type">
        {{ t.message }}
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const toasts = ref([])
let id = 0

function show(message, type = 'info', duration = 3000) {
  const toast = { id: ++id, message, type }
  toasts.value.push(toast)
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== toast.id)
  }, duration)
}

defineExpose({ show })
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 999;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.toast {
  padding: 10px 20px;
  font-size: 0.9rem;
  min-width: 200px;
}
.toast.success { border-color: var(--accent-green); }
.toast.error { border-color: var(--accent-red); }
.toast-enter-active { transition: all 0.3s ease; }
.toast-leave-active { transition: all 0.2s ease; }
.toast-enter-from { opacity: 0; transform: translateX(40px); }
.toast-leave-to { opacity: 0; transform: translateX(40px); }
</style>
