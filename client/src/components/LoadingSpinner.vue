<template>
  <div class="spinner-overlay" v-if="visible">
    <div class="spinner"></div>
  </div>
</template>

<script setup>
defineProps({ visible: { type: Boolean, default: true } })
</script>

<style scoped>
.spinner-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-2xl);
}
.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--border-glass);
  border-top-color: var(--accent-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
</style>
