<template>
  <div id="inkstone-app">
    <NavBar />
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <Toast />
  </div>
</template>

<script setup>
import NavBar from './components/NavBar.vue'
import Toast from './components/Toast.vue'
import { useUserStore } from './stores/user.js'

useUserStore()
</script>

<style scoped>
#inkstone-app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  z-index: 1;
}
.main-content {
  flex: 1;
  padding-top: 64px;
}
</style>
