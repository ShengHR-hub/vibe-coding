<template>
  <div id="inkstone-app" v-cloak>
    <SilkBackground :hue="bgHue" :saturation="bgSat" :brightness="bgBright" :speed="bgSpeed" />
    <NavBar v-if="showNav" />
    <main class="main-content" :class="{ standalone: isStandalone, 'no-nav': route.meta.noNav }">
      <router-view />
    </main>
    <Toast />
    <GuideModal />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import NavBar from './components/NavBar.vue'
import Toast from './components/Toast.vue'
import GuideModal from './components/GuideModal.vue'
import SilkBackground from './components/SilkBackground.vue'
import { useUserStore } from './stores/user.js'

useUserStore()
const route = useRoute()
const router = useRouter()
const routeReady = ref(false)

const isStandalone = computed(() => route.meta.standalone === true)
const showNav = computed(() => routeReady.value && !isStandalone.value && !route.meta.noNav)

onMounted(async () => {
  await router.isReady()
  routeReady.value = true
})

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
.main-content.standalone,
.main-content.no-nav {
  padding-top: 0;
}
</style>
