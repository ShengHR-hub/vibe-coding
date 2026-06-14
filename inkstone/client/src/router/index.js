import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user.js'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/Home.vue') },
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { guest: true } },
  { path: '/register', name: 'Register', component: () => import('../views/Register.vue'), meta: { guest: true } },
  { path: '/write', name: 'Write', component: () => import('../views/write/WriteStudio.vue'), meta: { auth: true } },
  { path: '/works', name: 'Works', component: () => import('../views/works/MyWorks.vue'), meta: { auth: true } },
  { path: '/works/:id', name: 'WorkDetail', component: () => import('../views/works/WorkDetail.vue') },
  { path: '/works/:id/edit', name: 'WorkEditor', component: () => import('../views/works/WorkEditor.vue'), meta: { auth: true } },
  { path: '/read/:id', name: 'Reader', component: () => import('../views/works/Reader.vue') },
  { path: '/explore', name: 'Explore', component: () => import('../views/community/Explore.vue') },
  { path: '/stats', name: 'Stats', component: () => import('../views/stats/Dashboard.vue'), meta: { auth: true } },
  { path: '/graph/:work_id', name: 'Graph', component: () => import('../views/graph/CharacterGraph.vue'), meta: { auth: true } },
  { path: '/challenges', name: 'Challenges', component: () => import('../views/challenges/ChallengeList.vue') },
  { path: '/profile/:id', name: 'Profile', component: () => import('../views/user/Profile.vue') },
  { path: '/notifications', name: 'Notifications', component: () => import('../views/notifications/NotificationCenter.vue'), meta: { auth: true } },
  { path: '/review/:work_id', name: 'Review', component: () => import('../views/review/ReviewPage.vue'), meta: { auth: true } },
  { path: '/works/:id/volumes', name: 'VolumeManager', component: () => import('../views/serialize/VolumeManager.vue'), meta: { auth: true } },
  { path: '/rp/:work_id', name: 'RolePlay', component: () => import('../views/rp/RolePlay.vue'), meta: { auth: true } },
  { path: '/poems', name: 'Poems', component: () => import('../views/poems/PoemLibrary.vue') },
  { path: '/materials', name: 'Materials', component: () => import('../views/materials/MaterialLibrary.vue') },
  { path: '/daily', name: 'Daily', component: () => import('../views/daily/DailyPractice.vue') },
  { path: '/rankings', name: 'Rankings', component: () => import('../views/rankings/Rankings.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  const userStore = useUserStore()

  if (!userStore.initialized) {
    await userStore.fetchUser()
  }

  if (to.meta.guest && userStore.isLoggedIn) {
    return '/'
  }
  if (to.meta.auth && !userStore.isLoggedIn) {
    return '/login'
  }
})

export default router
