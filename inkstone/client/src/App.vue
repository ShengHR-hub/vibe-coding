<template>
  <div id="inkstone-app">
    <SilkBackground :hue="bgHue" :saturation="bgSat" :brightness="bgBright" :speed="bgSpeed" />
    <NavBar />
    <main class="main-content">
      <router-view />
    </main>
    <Toast />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import NavBar from './components/NavBar.vue'
import Toast from './components/Toast.vue'
import SilkBackground from './components/SilkBackground.vue'
import { useUserStore } from './stores/user.js'

useUserStore()

const bgHue = ref(220)
const bgSat = ref(0.3)
const bgBright = ref(0.6)
const bgSpeed = ref(0.8)
</script>

<style scoped>
#inkstone-app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
}
#inkstone-app :deep(.silk-bg) {
  position: fixed; top: 0; right: 0; bottom: 0; left: 0;
  z-index: -1;
  pointer-events: none;
}
.main-content {
  flex: 1;
  padding-top: 80px;
}
</style>
