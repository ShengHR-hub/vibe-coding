<template>
  <div class="page-container" v-if="profile">
    <NavBar />
    <!-- Cover -->
    <div class="cover" :style="profile.user.cover_image ? { backgroundImage: `url(${profile.user.cover_image})` } : {}">
      <div class="cover-overlay"></div>
    </div>

    <!-- Header -->
    <div class="profile-header">
      <div class="avatar-wrap">
        <img v-if="profile.user.avatar" :src="profile.user.avatar" class="avatar-img" />
        <div v-else class="avatar">{{ profile.user.username?.charAt(0) }}</div>
      </div>
      <div class="header-info">
        <div class="name-row">
          <h2>{{ profile.user.username }}</h2>
          <span class="level-badge" :class="`lv-${profile.user.level}`">{{ levelLabel }}</span>
        </div>
        <p v-if="profile.user.bio" class="bio">{{ profile.user.bio }}</p>
        <p v-else class="bio muted">暂无简介</p>
        <div class="meta-row">
          <span class="join-date">加入于 {{ fmtDate(profile.user.created_at) }}</span>
          <span v-if="profile.reading_preferences?.length" class="reading-pref">
            阅读偏好：{{ profile.reading_preferences.map(p => typeLabel(p)).join(' · ') }}
          </span>
        </div>
      </div>
      <div class="header-actions">
        <button v-if="profile.is_own" class="btn btn-ghost btn-sm" @click="openEdit">编辑资料</button>
        <button v-else-if="userStore.isLoggedIn" class="btn btn-sm" :class="profile.is_following ? 'btn-ghost' : 'btn-primary'" @click="doFollow">
          {{ profile.is_following ? '已关注' : '+ 关注' }}
        </button>
      </div>
    </div>

    <!-- Stats: Writing -->
    <div class="stats-section">
      <div class="stats-label">创作</div>
      <div class="stats-bar glass-card">
        <div class="stat">
          <span class="stat-num">{{ profile.stats.works_count }}</span>
          <span class="stat-label">作品</span>
        </div>
        <div class="stat">
          <span class="stat-num">{{ fmtNum(profile.stats.total_words) }}</span>
          <span class="stat-label">总字数</span>
        </div>
        <div class="stat">
          <span class="stat-num">{{ profile.stats.total_likes }}</span>
          <span class="stat-label">获赞</span>
        </div>
        <div class="stat">
          <span class="stat-num">{{ profile.stats.followers_count }}</span>
          <span class="stat-label">粉丝</span>
        </div>
        <div class="stat">
          <span class="stat-num">{{ profile.stats.following_count }}</span>
          <span class="stat-label">关注</span>
        </div>
      </div>
    </div>

    <!-- Stats: Reading -->
    <div class="stats-section">
      <div class="stats-label">阅读</div>
      <div class="stats-bar glass-card">
        <div class="stat">
          <span class="stat-num">{{ profile.stats.reading_count }}</span>
          <span class="stat-label">在读</span>
        </div>
        <div class="stat">
          <span class="stat-num">{{ profile.stats.completed_count }}</span>
          <span class="stat-label">读完</span>
        </div>
        <div class="stat">
          <span class="stat-num">{{ fmtMinutes(profile.stats.reading_minutes) }}</span>
          <span class="stat-label">阅读时长</span>
        </div>
        <div class="stat">
          <span class="stat-num">{{ profile.stats.checkin_days }}</span>
          <span class="stat-label">打卡</span>
        </div>
        <div class="stat">
          <span class="stat-num">{{ profile.stats.annotation_count }}</span>
          <span class="stat-label">批注</span>
        </div>
      </div>
    </div>

    <!-- Exp bar (own profile only) -->
    <div v-if="profile.is_own && profile.next_level_exp" class="exp-section glass-card">
      <div class="exp-header">
        <span>经验值 {{ profile.user.exp }}</span>
        <span v-if="profile.next_level_exp">升级还需 {{ profile.next_level_exp - profile.user.exp }}</span>
        <span v-else>已满级</span>
      </div>
      <div class="exp-bar-bg">
        <div class="exp-bar-fill" :style="{ width: expPercent + '%' }"></div>
      </div>
    </div>

    <!-- Overview Card -->
    <div class="overview-card glass-card">
      <div class="overview-title">数据概览</div>
      <div class="overview-rows">
        <div class="overview-row">
          <span class="ov-label">创作</span>
          <div class="ov-bar-bg">
            <div class="ov-bar-fill writing" :style="{ width: writingBar + '%' }"></div>
          </div>
          <span class="ov-value">{{ profile.stats.works_count }}篇 · {{ fmtNum(profile.stats.total_words) }}字</span>
        </div>
        <div class="overview-row">
          <span class="ov-label">阅读</span>
          <div class="ov-bar-bg">
            <div class="ov-bar-fill reading" :style="{ width: readingBar + '%' }"></div>
          </div>
          <span class="ov-value">{{ profile.stats.completed_count }}本 · {{ fmtMinutes(profile.stats.reading_minutes) }}</span>
        </div>
        <div class="overview-row">
          <span class="ov-label">互动</span>
          <div class="ov-bar-bg">
            <div class="ov-bar-fill interact" :style="{ width: interactBar + '%' }"></div>
          </div>
          <span class="ov-value">{{ profile.stats.total_likes }}赞 · {{ profile.stats.annotation_count }}批注</span>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button v-for="tab in visibleTabs" :key="tab.key" class="tab" :class="{ active: activeTab === tab.key }" @click="switchTab(tab.key)">
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab: Works -->
    <div v-if="activeTab === 'works'">
      <div v-if="loadingTab" class="center"><LoadingSpinner /></div>
      <div v-else-if="tabItems.length === 0" class="center muted">暂无作品</div>
      <div v-else class="works-grid">
        <div v-for="w in tabItems" :key="w.work_id" class="work-card glass-card" @click="$router.push(`/read/${w.work_id}`)">
          <div class="card-type">{{ typeLabel(w.type) }}</div>
          <h3>{{ w.title }}</h3>
          <p v-if="w.summary" class="card-summary">{{ w.summary }}</p>
          <div class="card-meta">
            <span>{{ w.word_count || 0 }} 字</span>
            <span>{{ w.likes_count || 0 }} 赞</span>
            <span>{{ w.comments_count || 0 }} 评</span>
          </div>
        </div>
      </div>
      <div v-if="tabTotal > pageSize" class="pagination">
        <button class="btn btn-ghost" :disabled="tabPage <= 1" @click="tabPage--; loadTab()">上一页</button>
        <span>{{ tabPage }} / {{ Math.ceil(tabTotal / pageSize) }}</span>
        <button class="btn btn-ghost" :disabled="tabPage >= Math.ceil(tabTotal / pageSize)" @click="tabPage++; loadTab()">下一页</button>
      </div>
    </div>

    <!-- Tab: Favorites -->
    <div v-if="activeTab === 'favorites'">
      <div v-if="loadingTab" class="center"><LoadingSpinner /></div>
      <div v-else-if="tabItems.length === 0" class="center muted">暂无收藏</div>
      <div v-else class="works-grid">
        <div v-for="w in tabItems" :key="w.work_id" class="work-card glass-card" @click="$router.push(`/read/${w.work_id}`)">
          <div class="card-type">{{ typeLabel(w.type) }}</div>
          <h3>{{ w.title }}</h3>
          <p class="card-meta">
            <span>{{ w.username }}</span>
            <span>{{ w.likes_count || 0 }} 赞</span>
          </p>
        </div>
      </div>
      <div v-if="tabTotal > pageSize" class="pagination">
        <button class="btn btn-ghost" :disabled="tabPage <= 1" @click="tabPage--; loadTab()">上一页</button>
        <span>{{ tabPage }} / {{ Math.ceil(tabTotal / pageSize) }}</span>
        <button class="btn btn-ghost" :disabled="tabPage >= Math.ceil(tabTotal / pageSize)" @click="tabPage++; loadTab()">下一页</button>
      </div>
    </div>

    <!-- Tab: Reading -->
    <div v-if="activeTab === 'reading'">
      <div v-if="loadingTab" class="center"><LoadingSpinner /></div>
      <div v-else-if="tabItems.length === 0" class="center muted">暂无阅读记录</div>
      <div v-else class="works-grid">
        <div v-for="b in tabItems" :key="b.shelf_id" class="work-card glass-card reading-card" @click="b.book_id && $router.push(`/library/library/${b.book_id}`)">
          <img v-if="b.cover_image" :src="b.cover_image" class="reading-cover" />
          <div v-else class="reading-cover-placeholder">{{ b.title?.charAt(0) }}</div>
          <div class="reading-info">
            <h3>{{ b.title || '未知书籍' }}</h3>
            <p class="card-meta">
              <span v-if="b.author">{{ b.author }}</span>
              <span class="shelf-badge" :class="b.shelf_group">{{ shelfLabel(b.shelf_group) }}</span>
            </p>
          </div>
        </div>
      </div>
      <div v-if="tabTotal > pageSize" class="pagination">
        <button class="btn btn-ghost" :disabled="tabPage <= 1" @click="tabPage--; loadTab()">上一页</button>
        <span>{{ tabPage }} / {{ Math.ceil(tabTotal / pageSize) }}</span>
        <button class="btn btn-ghost" :disabled="tabPage >= Math.ceil(tabTotal / pageSize)" @click="tabPage++; loadTab()">下一页</button>
      </div>
    </div>

    <!-- Tab: Reviews -->
    <div v-if="activeTab === 'reviews'">
      <div v-if="loadingTab" class="center"><LoadingSpinner /></div>
      <div v-else-if="tabItems.length === 0" class="center muted">暂无书评</div>
      <div v-else class="reviews-list">
        <div v-for="r in tabItems" :key="r.review_id" class="review-card glass-card" @click="r.book_id && $router.push(`/library/library/${r.book_id}`)">
          <div class="review-header">
            <span class="review-book">{{ r.book_title }}</span>
            <span class="review-rating">
              <span v-for="i in 5" :key="i" :class="i <= r.rating ? 'star-filled' : 'star-empty'">★</span>
            </span>
          </div>
          <p v-if="r.content" class="review-content">{{ r.content }}</p>
          <span class="review-date">{{ fmtDate(r.created_at) }}</span>
        </div>
      </div>
      <div v-if="tabTotal > pageSize" class="pagination">
        <button class="btn btn-ghost" :disabled="tabPage <= 1" @click="tabPage--; loadTab()">上一页</button>
        <span>{{ tabPage }} / {{ Math.ceil(tabTotal / pageSize) }}</span>
        <button class="btn btn-ghost" :disabled="tabPage >= Math.ceil(tabTotal / pageSize)" @click="tabPage++; loadTab()">下一页</button>
      </div>
    </div>

    <!-- Tab: Achievements -->
    <div v-if="activeTab === 'achievements'">
      <div v-if="loadingTab" class="center"><LoadingSpinner /></div>
      <div v-else class="achievements-section">
        <div class="ach-category">
          <h3 class="ach-cat-title">写作成就</h3>
          <div class="achievements-grid">
            <div v-for="ach in writingAchievements" :key="ach.achievement_id" class="ach-card glass-card" :class="{ unlocked: ach.unlocked }">
              <span class="ach-icon">{{ ach.icon }}</span>
              <div class="ach-info">
                <strong>{{ ach.name }}</strong>
                <p>{{ ach.description }}</p>
                <div class="ach-progress-bar">
                  <div class="ach-progress-fill" :style="{ width: Math.min(100, ach.current / ach.condition_value * 100) + '%' }"></div>
                </div>
                <span class="ach-progress-text">{{ ach.current }}/{{ ach.condition_value }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="ach-category">
          <h3 class="ach-cat-title">阅读成就</h3>
          <div class="achievements-grid">
            <div v-for="ach in readingAchievements" :key="ach.achievement_id" class="ach-card glass-card" :class="{ unlocked: ach.unlocked }">
              <span class="ach-icon">{{ ach.icon }}</span>
              <div class="ach-info">
                <strong>{{ ach.name }}</strong>
                <p>{{ ach.description }}</p>
                <div class="ach-progress-bar">
                  <div class="ach-progress-fill" :style="{ width: Math.min(100, ach.current / ach.condition_value * 100) + '%' }"></div>
                </div>
                <span class="ach-progress-text">{{ ach.current }}/{{ ach.condition_value }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Tab: Followers -->
    <div v-if="activeTab === 'followers'">
      <div v-if="loadingTab" class="center"><LoadingSpinner /></div>
      <div v-else-if="tabItems.length === 0" class="center muted">暂无粉丝</div>
      <div v-else class="user-list">
        <div v-for="u in tabItems" :key="u.user_id" class="user-item glass-card" @click="$router.push(`/profile/${u.user_id}`)">
          <span class="avatar-dot">{{ u.username?.charAt(0) }}</span>
          <span class="user-name">{{ u.username }}</span>
          <span v-if="u.bio" class="user-bio">{{ u.bio }}</span>
        </div>
      </div>
    </div>

    <!-- Tab: Following -->
    <div v-if="activeTab === 'following'">
      <div v-if="loadingTab" class="center"><LoadingSpinner /></div>
      <div v-else-if="tabItems.length === 0" class="center muted">暂未关注任何人</div>
      <div v-else class="user-list">
        <div v-for="u in tabItems" :key="u.user_id" class="user-item glass-card" @click="$router.push(`/profile/${u.user_id}`)">
          <span class="avatar-dot">{{ u.username?.charAt(0) }}</span>
          <span class="user-name">{{ u.username }}</span>
          <span v-if="u.bio" class="user-bio">{{ u.bio }}</span>
        </div>
      </div>
    </div>

    <!-- Edit Profile Modal -->
    <div v-if="showEdit" class="modal-overlay" @click.self="showEdit = false">
      <div class="modal glass-card">
        <h3>编辑资料</h3>

        <label>头像</label>
        <div class="upload-avatar-wrap" @click="$refs.avatarInput.click()">
          <img v-if="editForm.avatar" :src="editForm.avatar" class="avatar-preview" />
          <span v-else class="avatar-placeholder">{{ profile.user.username?.charAt(0) }}</span>
          <div class="upload-overlay">更换</div>
        </div>
        <input ref="avatarInput" type="file" accept="image/*" hidden @change="e => handleUpload(e, 'avatar')" />

        <label>封面图</label>
        <div class="upload-cover-wrap" @click="$refs.coverInput.click()">
          <img v-if="editForm.cover_image" :src="editForm.cover_image" class="cover-preview" />
          <span v-else class="cover-placeholder">点击上传封面图</span>
        </div>
        <input ref="coverInput" type="file" accept="image/*" hidden @change="e => handleUpload(e, 'cover_image')" />

        <label>个人简介</label>
        <textarea v-model="editForm.bio" rows="3" placeholder="介绍一下自己..."></textarea>
        <div class="modal-actions">
          <button class="btn btn-ghost btn-sm" @click="showEdit = false">取消</button>
          <button class="btn btn-primary btn-sm" @click="saveProfile" :disabled="saving">{{ saving ? '保存中...' : '保存' }}</button>
        </div>
      </div>
    </div>
  </div>
  <div v-else-if="errorMsg" class="page-container center error">{{ errorMsg }}</div>
  <div v-else class="page-container center"><LoadingSpinner /></div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../api/index.js'
import { useUserStore } from '../../stores/user.js'
import LoadingSpinner from '../../components/LoadingSpinner.vue'
import NavBar from '../../components/NavBar.vue'

import { useToast } from '../../composables/useToast.js'
const toast = useToast()
const route = useRoute()
const userStore = useUserStore()

const profile = ref(null)
const errorMsg = ref('')
const activeTab = ref('works')
const achievements = ref([])
const tabItems = ref([])
const tabPage = ref(1)
const tabTotal = ref(0)
const loadingTab = ref(false)
const pageSize = 12
const showEdit = ref(false)
const saving = ref(false)
const editForm = ref({ avatar: '', cover_image: '', bio: '' })

const levelNames = ['', '初窥门径', '小有所成', '初露锋芒', '渐入佳境', '笔力浑厚', '妙笔生花', '文采斐然', '文坛翘楚', '一代文豪', '文坛巨匠']

const READING_TYPES = ['books_read', 'reading_streak', 'reading_hours', 'annotations', 'highlights']

const levelLabel = computed(() => {
  const lv = profile.value?.user?.level || 1
  return `Lv.${lv} ${levelNames[Math.min(lv, 10)]}`
})

const expPercent = computed(() => {
  if (!profile.value || !profile.value.next_level_exp) return 100
  const prev = profile.value.prev_level_exp
  const next = profile.value.next_level_exp
  return Math.min(100, ((profile.value.user.exp - prev) / (next - prev)) * 100)
})

const writingAchievements = computed(() => achievements.value.filter(a => !READING_TYPES.includes(a.condition_type)))
const readingAchievements = computed(() => achievements.value.filter(a => READING_TYPES.includes(a.condition_type)))

const writingBar = computed(() => {
  const s = profile.value?.stats
  if (!s) return 0
  return Math.min(100, Math.max(5, (s.works_count * 5 + Math.min(s.total_words / 1000, 50))))
})
const readingBar = computed(() => {
  const s = profile.value?.stats
  if (!s) return 0
  return Math.min(100, Math.max(5, (s.completed_count * 8 + Math.min(s.reading_minutes / 60, 50))))
})
const interactBar = computed(() => {
  const s = profile.value?.stats
  if (!s) return 0
  return Math.min(100, Math.max(5, (s.total_likes + s.annotation_count) / 5))
})

const allTabs = [
  { key: 'works', label: '作品' },
  { key: 'favorites', label: '收藏' },
  { key: 'achievements', label: '成就' },
  { key: 'followers', label: '粉丝' },
  { key: 'following', label: '关注' },
]

const visibleTabs = computed(() => {
  if (profile.value?.is_own) return allTabs
  return allTabs.filter(t => t.key !== 'favorites')
})

onMounted(async () => {
  const uid = route.params.id
  if (route.query.tab && allTabs.some(t => t.key === route.query.tab)) {
    activeTab.value = route.query.tab
  }
  const res = await api.get(`/api/users/${uid}`)
  if (res.code === 0) {
    profile.value = res.data
    loadTab()
  } else {
    errorMsg.value = res.msg || '用户不存在'
  }
})

watch(() => route.params.id, async (newId) => {
  profile.value = null
  errorMsg.value = ''
  activeTab.value = 'works'
  const res = await api.get(`/api/users/${newId}`)
  if (res.code === 0) {
    profile.value = res.data
    loadTab()
  } else {
    errorMsg.value = res.msg || '用户不存在'
  }
})

async function loadTab() {
  loadingTab.value = true
  const uid = route.params.id

  if (activeTab.value === 'achievements') {
    if (profile.value?.is_own) {
      const res = await api.get('/api/users/achievements')
      if (res.code === 0) achievements.value = res.data.achievements
    }
    loadingTab.value = false
    return
  }

  let url
  switch (activeTab.value) {
    case 'works': url = `/api/users/${uid}/works`; break
    case 'favorites': url = `/api/users/${uid}/favorites`; break
    case 'followers': url = `/api/users/${uid}/followers`; break
    case 'following': url = `/api/users/${uid}/following`; break
  }
  url += `?page=${tabPage.value}&page_size=${pageSize}`

  const res = await api.get(url)
  if (res.code === 0) {
    tabItems.value = res.data.items
    tabTotal.value = res.data.total
  }
  loadingTab.value = false
}

function switchTab(key) {
  activeTab.value = key
  tabPage.value = 1
  loadTab()
}

async function doFollow() {
  if (!userStore.isLoggedIn) { toast.error('请先登录'); return }
  const res = await api.post('/api/users/follow', { user_id: profile.value.user.user_id })
  if (res.code === 0) {
    profile.value.is_following = res.data.following
    profile.value.stats.followers_count += res.data.following ? 1 : -1
  }
}

function openEdit() {
  editForm.value = {
    avatar: profile.value.user.avatar || '',
    cover_image: profile.value.user.cover_image || '',
    bio: profile.value.user.bio || ''
  }
  showEdit.value = true
}

async function handleUpload(e, field) {
  const file = e.target.files[0]
  if (!file) return
  const res = await api.upload(file)
  if (res.code === 0) {
    editForm.value[field] = res.data.url
  } else {
    toast.error(res.msg || '上传失败')
  }
}

async function saveProfile() {
  saving.value = true
  const res = await api.put('/api/users/profile', editForm.value)
  if (res.code === 0) {
    profile.value.user.avatar = editForm.value.avatar
    profile.value.user.cover_image = editForm.value.cover_image
    profile.value.user.bio = editForm.value.bio
    if (userStore.user) {
      userStore.user.avatar = editForm.value.avatar
      userStore.user.bio = editForm.value.bio
    }
    showEdit.value = false
  } else {
    toast.info(res.msg)
  }
  saving.value = false
}

function typeLabel(t) {
  return { novel: '小说', poetry: '诗歌', essay: '散文', script: '剧本', webfiction: '网文' }[t] || t
}

function shelfLabel(g) {
  return { reading: '在读', completed: '读完', want_read: '想读' }[g] || g
}

function fmtDate(d) {
  if (!d) return ''
  return d.slice(0, 10)
}

function fmtNum(n) {
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  return String(n)
}

function fmtMinutes(m) {
  if (!m) return '0小时'
  if (m < 60) return m + '分钟'
  const h = Math.floor(m / 60)
  if (h < 10) return (m / 60).toFixed(1) + '小时'
  return h + '小时'
}
</script>

<style scoped>
.page-container { padding-top: 80px; }
.cover { height: 200px; background: linear-gradient(135deg, var(--accent-primary), var(--accent-purple)); border-radius: var(--radius-lg); position: relative; overflow: hidden; background-size: cover; background-position: center; }
.cover-overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.2); }

.profile-header { display: flex; align-items: flex-start; gap: var(--space-lg); margin-top: -40px; position: relative; z-index: 1; padding: 0 var(--space-md); }
.avatar-wrap { flex-shrink: 0; }
.avatar { width: 80px; height: 80px; border-radius: 50%; background: var(--accent-primary); color: var(--bg-primary); display: flex; align-items: center; justify-content: center; font-size: 2rem; font-weight: 700; border: 4px solid var(--bg-primary); }
.avatar-img { width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 4px solid var(--bg-primary); }
.header-info { flex: 1; padding-top: 44px; }
.name-row { display: flex; align-items: center; gap: var(--space-md); margin-bottom: var(--space-sm); }
.name-row h2 { margin: 0; }
.level-badge { padding: 2px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 700; background: var(--bg-glass); color: var(--accent-primary); }
.lv-5, .lv-6 { color: var(--accent-warm); }
.lv-7, .lv-8 { color: var(--accent-purple); }
.lv-9, .lv-10 { color: #f59e0b; background: rgba(245,158,11,0.15); }
.bio { font-size: 0.9rem; margin-bottom: var(--space-xs); }
.meta-row { display: flex; align-items: center; gap: var(--space-lg); flex-wrap: wrap; }
.join-date { font-size: 0.8rem; color: var(--text-muted); }
.reading-pref { font-size: 0.78rem; color: var(--accent-primary); opacity: 0.8; }
.header-actions { padding-top: 44px; flex-shrink: 0; }

/* Stats */
.stats-section { margin-top: var(--space-lg); }
.stats-label { font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.15em; margin-bottom: var(--space-xs); padding-left: var(--space-xs); }
.stats-bar { display: flex; justify-content: space-around; padding: var(--space-md) var(--space-lg); }
.stat { text-align: center; }
.stat-num { display: block; font-size: 1.3rem; font-weight: 700; color: var(--accent-primary); }
.stat-label { font-size: 0.75rem; color: var(--text-muted); }

.exp-section { padding: var(--space-md) var(--space-lg); margin-top: var(--space-lg); }
.exp-header { display: flex; justify-content: space-between; font-size: 0.85rem; margin-bottom: var(--space-sm); color: var(--text-secondary); }
.exp-bar-bg { height: 8px; border-radius: 4px; background: var(--bg-glass); overflow: hidden; }
.exp-bar-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, var(--accent-primary), var(--accent-purple)); transition: width 0.5s ease; }

/* Overview Card */
.overview-card { padding: var(--space-lg); margin-top: var(--space-lg); }
.overview-title { font-size: 0.85rem; font-weight: 600; color: var(--text-secondary); margin-bottom: var(--space-md); }
.overview-rows { display: flex; flex-direction: column; gap: var(--space-sm); }
.overview-row { display: flex; align-items: center; gap: var(--space-md); }
.ov-label { font-size: 0.78rem; color: var(--text-muted); width: 32px; flex-shrink: 0; }
.ov-bar-bg { flex: 1; height: 6px; border-radius: 3px; background: var(--bg-glass); overflow: hidden; }
.ov-bar-fill { height: 100%; border-radius: 3px; transition: width 0.8s ease; }
.ov-bar-fill.writing { background: var(--accent-primary); }
.ov-bar-fill.reading { background: var(--accent-purple); }
.ov-bar-fill.interact { background: var(--accent-warm); }
.ov-value { font-size: 0.75rem; color: var(--text-muted); width: 140px; text-align: right; flex-shrink: 0; }

/* Tabs */
.tabs { display: flex; gap: var(--space-sm); margin: var(--space-xl) 0; border-bottom: 1px solid var(--border-glass); padding-bottom: var(--space-sm); overflow-x: auto; }
.tab { padding: 6px 14px; font-size: 0.85rem; color: var(--text-muted); background: none; border-radius: var(--radius-sm); transition: all var(--transition-fast); white-space: nowrap; }
.tab:hover { color: var(--text-secondary); }
.tab.active { color: var(--accent-primary); background: var(--bg-glass); }

/* Works Grid */
.works-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--space-lg); }
.work-card { padding: var(--space-lg); cursor: pointer; transition: all var(--transition-fast); }
.work-card:hover { border-color: var(--accent-primary); transform: translateY(-2px); }
.card-type { font-size: 0.7rem; color: var(--accent-primary); text-transform: uppercase; margin-bottom: var(--space-sm); }
.work-card h3 { margin-bottom: var(--space-sm); font-size: 1rem; }
.card-summary { font-size: 0.85rem; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-bottom: var(--space-md); }
.card-meta { display: flex; gap: var(--space-md); font-size: 0.8rem; color: var(--text-muted); }

/* Reading Cards */
.reading-card { display: flex; gap: var(--space-md); align-items: center; }
.reading-cover { width: 50px; height: 68px; object-fit: cover; border-radius: 4px; flex-shrink: 0; }
.reading-cover-placeholder { width: 50px; height: 68px; background: var(--bg-glass); border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem; color: var(--accent-primary); flex-shrink: 0; }
.reading-info { flex: 1; min-width: 0; }
.reading-info h3 { font-size: 0.95rem; margin-bottom: var(--space-xs); }
.shelf-badge { font-size: 0.7rem; padding: 1px 8px; border-radius: 10px; }
.shelf-badge.reading { color: var(--accent-primary); background: rgba(196,163,90,0.1); }
.shelf-badge.completed { color: var(--accent-green); background: rgba(107,207,127,0.1); }
.shelf-badge.want_read { color: var(--text-muted); background: var(--bg-glass); }

/* Reviews */
.reviews-list { display: flex; flex-direction: column; gap: var(--space-md); }
.review-card { padding: var(--space-lg); cursor: pointer; transition: all var(--transition-fast); }
.review-card:hover { border-color: var(--accent-primary); }
.review-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-sm); }
.review-book { font-weight: 600; font-size: 0.95rem; }
.review-rating { font-size: 0.85rem; }
.star-filled { color: #f59e0b; }
.star-empty { color: var(--text-muted); opacity: 0.3; }
.review-content { font-size: 0.85rem; color: var(--text-secondary); line-height: 1.6; margin-bottom: var(--space-sm); display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.review-date { font-size: 0.75rem; color: var(--text-muted); }

/* Achievements */
.achievements-section { display: flex; flex-direction: column; gap: var(--space-xl); }
.ach-cat-title { font-size: 0.9rem; font-weight: 600; color: var(--text-secondary); margin-bottom: var(--space-md); }
.achievements-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--space-md); }
.ach-card { display: flex; align-items: center; gap: var(--space-md); padding: var(--space-md) var(--space-lg); opacity: 0.5; transition: all var(--transition-fast); }
.ach-card.unlocked { opacity: 1; border-color: var(--accent-warm); }
.ach-icon { font-size: 1.5rem; flex-shrink: 0; }
.ach-info { flex: 1; min-width: 0; }
.ach-info strong { font-size: 0.9rem; }
.ach-info p { font-size: 0.8rem; color: var(--text-muted); margin-bottom: var(--space-xs); }
.ach-progress-bar { height: 4px; border-radius: 2px; background: var(--bg-glass); margin-top: var(--space-xs); }
.ach-progress-fill { height: 100%; border-radius: 2px; background: var(--accent-primary); }
.ach-progress-text { font-size: 0.7rem; color: var(--text-muted); }

/* User List */
.user-list { display: flex; flex-direction: column; gap: var(--space-sm); }
.user-item { display: flex; align-items: center; gap: var(--space-md); padding: var(--space-md); cursor: pointer; transition: all var(--transition-fast); }
.user-item:hover { border-color: var(--accent-primary); }
.avatar-dot { width: 36px; height: 36px; border-radius: 50%; background: var(--accent-primary); color: var(--bg-primary); display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 700; flex-shrink: 0; }
.user-name { font-weight: 600; }
.user-bio { font-size: 0.85rem; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 100; display: flex; align-items: center; justify-content: center; }
.modal { width: 90%; max-width: 480px; padding: var(--space-2xl); display: flex; flex-direction: column; gap: var(--space-md); }
.modal h3 { margin: 0; }
.modal input, .modal textarea { padding: 8px 12px; font-size: 0.9rem; background: var(--bg-primary); border: 1px solid var(--border-glass); border-radius: var(--radius-sm); color: var(--text-primary); }
.modal-actions { display: flex; justify-content: flex-end; gap: var(--space-sm); margin-top: var(--space-md); }

.upload-avatar-wrap { width: 80px; height: 80px; border-radius: 50%; cursor: pointer; position: relative; overflow: hidden; background: var(--bg-glass); display: flex; align-items: center; justify-content: center; }
.upload-avatar-wrap:hover .upload-overlay { opacity: 1; }
.avatar-preview { width: 100%; height: 100%; object-fit: cover; }
.avatar-placeholder { font-size: 2rem; color: var(--accent-primary); font-weight: 700; }

.upload-cover-wrap { width: 100%; height: 100px; border-radius: var(--radius-md); cursor: pointer; position: relative; overflow: hidden; background: var(--bg-glass); display: flex; align-items: center; justify-content: center; }
.upload-cover-wrap:hover .upload-overlay { opacity: 1; }
.cover-preview { width: 100%; height: 100%; object-fit: cover; }
.cover-placeholder { font-size: 0.85rem; color: var(--text-muted); }

.upload-overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; color: #fff; font-size: 0.85rem; opacity: 0; transition: opacity var(--transition-fast); pointer-events: none; }

.center { display: flex; justify-content: center; padding: var(--space-2xl); }
.error { color: var(--accent-red); }
.muted { color: var(--text-muted); }
.pagination { display: flex; justify-content: center; align-items: center; gap: var(--space-md); margin-top: var(--space-xl); }

@media (max-width: 640px) {
  .profile-header { flex-direction: column; align-items: center; text-align: center; }
  .header-info { padding-top: var(--space-md); }
  .meta-row { justify-content: center; }
  .header-actions { padding-top: 0; }
  .stats-bar { gap: var(--space-sm); }
  .stat-num { font-size: 1rem; }
  .tabs { gap: 2px; }
  .tab { padding: 6px 10px; font-size: 0.8rem; }
}
</style>
