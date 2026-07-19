import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user.js'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/Home.vue'), meta: { noNav: true } },
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { guest: true } },
  { path: '/register', name: 'Register', component: () => import('../views/Register.vue'), meta: { guest: true } },
  { path: '/write', name: 'Write', component: () => import('../views/write/WriteStudio.vue'), meta: { auth: true } },
  { path: '/works', name: 'Works', component: () => import('../views/works/MyWorks.vue'), meta: { auth: true } },
  { path: '/works/:id', name: 'WorkDetail', component: () => import('../views/works/WorkDetail.vue') },
  { path: '/works/:id/edit', name: 'WorkEditor', component: () => import('../views/works/WorkEditor.vue'), meta: { auth: true } },
  { path: '/read/:id', name: 'Reader', component: () => import('../views/works/Reader.vue'), meta: { standalone: true } },
  { path: '/reader/:type/:id', name: 'ReaderTyped', component: () => import('../views/works/Reader.vue'), meta: { standalone: true } },
  { path: '/bookshelf', name: 'Bookshelf', component: () => import('../views/library/Bookshelf.vue'), meta: { auth: true, standalone: true } },
  { path: '/explore', name: 'Explore', component: () => import('../views/community/Explore.vue') },
  { path: '/stats', name: 'Stats', component: () => import('../views/stats/Dashboard.vue'), meta: { auth: true } },
  { path: '/graph/:work_id', name: 'Graph', component: () => import('../views/graph/CharacterGraph.vue'), meta: { auth: true } },
  { path: '/challenges', name: 'Challenges', component: () => import('../views/challenges/ChallengeList.vue') },
  { path: '/profile/:id', name: 'Profile', component: () => import('../views/user/Profile.vue'), meta: { standalone: true } },
  { path: '/notifications', name: 'Notifications', component: () => import('../views/notifications/NotificationCenter.vue'), meta: { auth: true } },
  { path: '/review/:work_id', name: 'Review', component: () => import('../views/review/ReviewPage.vue'), meta: { auth: true } },
  { path: '/works/:id/volumes', name: 'VolumeManager', component: () => import('../views/serialize/VolumeManager.vue'), meta: { auth: true } },
  { path: '/rp/:work_id', name: 'RolePlay', component: () => import('../views/rp/RolePlay.vue'), meta: { auth: true } },
  { path: '/poems', name: 'Poems', component: () => import('../views/poems/PoemLibrary.vue') },
  { path: '/materials', name: 'Materials', component: () => import('../views/materials/MaterialLibrary.vue') },
  { path: '/daily', name: 'Daily', component: () => import('../views/daily/DailyPractice.vue') },
  { path: '/rankings', name: 'Rankings', component: () => import('../views/rankings/Rankings.vue') },
  { path: '/reading', redirect: '/library?from=reading' },
  { path: '/library', name: 'LibraryHome', component: () => import('../views/library/LibraryHome.vue'), meta: { standalone: true } },
  { path: '/library/upload', name: 'LibraryUpload', component: () => import('../views/library/LibraryUpload.vue'), meta: { standalone: true } },
  { path: '/library/:source/:id', name: 'LibraryDetail', component: () => import('../views/library/LibraryDetail.vue'), meta: { standalone: true } },
  { path: '/annotations', name: 'Annotations', component: () => import('../views/library/Annotations.vue'), meta: { auth: true, standalone: true } },
  { path: '/reading-report', name: 'ReadingReport', component: () => import('../views/library/ReadingReport.vue'), meta: { auth: true, standalone: true } },
  { path: '/compare', name: 'BookCompare', component: () => import('../views/library/BookCompare.vue'), meta: { standalone: true } },
  { path: '/highlights', name: 'Highlights', component: () => import('../views/library/Highlights.vue'), meta: { auth: true, standalone: true } },
  { path: '/my-records', name: 'MyRecords', component: () => import('../views/library/MyRecords.vue'), meta: { auth: true, standalone: true } },
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('../views/NotFound.vue') },
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to) => {
  const userStore = useUserStore()

  if (!userStore.initialized) {
    // 带超时的 fetchUser，防止网络问题导致白屏
    try {
      await Promise.race([
        userStore.fetchUser(),
        new Promise(resolve => setTimeout(resolve, 5000))
      ])
    } catch {
      // 超时或异常，标记为已初始化（视为未登录）
      userStore.initialized = true
    }
  }

  if (to.meta.guest && userStore.isLoggedIn) {
    return '/'
  }
  if (to.meta.auth && !userStore.isLoggedIn) {
    return '/login'
  }
})

export default router
