<template>
  <div class="page-container" v-if="book">
    <ReadingNav v-if="from === 'reading'" />
    <NavBar v-else />
    <!-- 头部 -->
    <div class="detail-header">
      <div class="header-top">
        <button class="btn btn-ghost btn-sm" @click="$router.back()">&larr; 返回</button>
      </div>
      <div class="header-actions">
        <button class="btn btn-primary btn-sm" @click="startReading">开始阅读</button>
        <button class="btn btn-outline btn-sm" @click="toggleShelf">
          {{ onShelf ? '已加入书架' : '加入书架' }}
        </button>
        <button class="btn btn-ghost btn-sm" @click="shareBook">分享</button>
      </div>
    </div>

    <!-- 书籍信息 -->
    <div class="book-info">
      <div class="book-cover" :class="coverClass(book.type)">
        <span class="cover-type">{{ typeLabel(book.type) }}</span>
      </div>
      <div class="book-detail">
        <div class="book-meta">
          <span class="type-badge">{{ typeLabel(book.type) }}</span>
          <span class="source-badge" v-if="book.source === 'work'">原创</span>
          <span class="source-badge" v-else>书库</span>
        </div>
        <h1>{{ book.title }}</h1>
        <p class="book-author">作者：{{ book.author }}</p>
        <p v-if="book.summary" class="book-summary">{{ book.summary }}</p>
        <p v-if="book.tags" class="tags">
          <span v-for="t in book.tags.split(',')" :key="t" class="tag">{{ t.trim() }}</span>
        </p>
        <div class="stats">
          <div class="stat-item">
            <span class="stat-value">{{ formatWordCount(book.word_count) }}</span>
            <span class="stat-label">字数</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ chapters.length }}</span>
            <span class="stat-label">章节</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ book.views || 0 }}</span>
            <span class="stat-label">阅读</span>
          </div>
          <div class="stat-item" v-if="book.rating_avg > 0">
            <span class="stat-value">{{ book.rating_avg }}</span>
            <span class="stat-label">评分</span>
          </div>
          <div class="stat-item">
            <span class="stat-value">{{ book.favorites_count || 0 }}</span>
            <span class="stat-label">收藏</span>
          </div>
        </div>
      </div>
    </div>

    <hr />

    <!-- 评分和书评 -->
    <div class="section-reviews">
      <h3 class="section-title">评分与书评</h3>

      <!-- 评分统计 -->
      <div class="rating-summary glass-card" v-if="reviewStats.count > 0">
        <div class="rating-big">
          <span class="rating-number">{{ reviewStats.avg_rating }}</span>
          <div class="rating-stars">{{ '★'.repeat(Math.round(reviewStats.avg_rating)) }}{{ '☆'.repeat(5 - Math.round(reviewStats.avg_rating)) }}</div>
          <span class="rating-count">{{ reviewStats.count }} 条评价</span>
        </div>
        <div class="rating-bars">
          <div v-for="i in 5" :key="i" class="rating-bar-row">
            <span class="bar-label">{{ 6 - i }}星</span>
            <div class="bar-track">
              <div class="bar-fill" :style="{ width: getBarWidth(6 - i) + '%' }"></div>
            </div>
            <span class="bar-count">{{ reviewStats['star' + (6 - i)] || 0 }}</span>
          </div>
        </div>
      </div>

      <!-- 写书评 -->
      <div class="review-form glass-card" v-if="userStore.isLoggedIn">
        <h4>{{ userReview ? '修改书评' : '写书评' }}</h4>
        <div class="star-input">
          <span v-for="i in 5" :key="i"
                class="star-btn" :class="{ active: reviewForm.rating >= i }"
                @click="reviewForm.rating = i">★</span>
          <span class="rating-text">{{ ratingTexts[reviewForm.rating - 1] }}</span>
        </div>
        <textarea v-model="reviewForm.content" rows="3" placeholder="分享你的读后感..."></textarea>
        <div class="form-actions">
          <button class="btn btn-primary btn-sm" @click="submitReview" :disabled="submitting">
            {{ userReview ? '更新' : '发布' }}
          </button>
          <button v-if="userReview" class="btn btn-ghost btn-sm" @click="deleteReview">删除</button>
        </div>
      </div>
      <div v-else class="login-hint glass-card">
        <p>登录后可发表书评</p>
        <router-link to="/login" class="btn btn-primary btn-sm">登录</router-link>
      </div>

      <!-- 书评列表 -->
      <div class="review-list">
        <div v-for="r in reviews" :key="r.review_id" class="review-item glass-card">
          <div class="review-header">
            <span class="review-avatar">{{ r.username?.charAt(0) }}</span>
            <div class="review-meta">
              <strong>{{ r.username }}</strong>
              <span class="review-stars">{{ '★'.repeat(r.rating) }}{{ '☆'.repeat(5 - r.rating) }}</span>
            </div>
            <span class="review-time">{{ r.created_at }}</span>
          </div>
          <p class="review-content" v-if="r.content">{{ r.content }}</p>
        </div>
        <div v-if="reviews.length === 0" class="empty-hint">暂无书评，快来写第一条吧</div>
      </div>
    </div>

    <hr />

    <!-- 目录 -->
    <div class="section-catalog">
      <h3 class="section-title">目录</h3>
      <div v-if="volumes.length > 0" class="volume-list">
        <div v-for="vol in volumes" :key="vol.volume_id" class="volume-group">
          <div class="volume-header" @click="vol._open = !vol._open">
            <span class="volume-toggle">{{ vol._open ? '▼' : '▶' }}</span>
            <span class="volume-title">{{ vol.title || `第${vol.volume_no}卷` }}</span>
            <span class="volume-count">{{ getVolumeChapters(vol.volume_id).length }} 章</span>
          </div>
          <div v-if="vol._open" class="chapter-list">
            <div v-for="ch in getVolumeChapters(vol.volume_id)" :key="ch.chapter_id"
                 class="chapter-item" @click="readChapter(ch)">
              <span class="ch-no">{{ ch.chapter_no }}</span>
              <span class="ch-title">{{ ch.title || `第${ch.chapter_no}章` }}</span>
              <span class="ch-wc">{{ formatWordCount(ch.word_count) }}字</span>
            </div>
          </div>
        </div>
      </div>
      <div v-else-if="chapters.length > 0" class="chapter-list">
        <div v-for="ch in chapters" :key="ch.chapter_id"
             class="chapter-item" @click="readChapter(ch)">
          <span class="ch-no">{{ ch.chapter_no }}</span>
          <span class="ch-title">{{ ch.title || `第${ch.chapter_no}章` }}</span>
          <span class="ch-wc">{{ formatWordCount(ch.word_count) }}字</span>
        </div>
      </div>
      <div v-else class="empty-hint">暂无章节</div>
    </div>
  </div>
  <div v-else-if="error" class="page-container center">{{ error }}</div>
  <div v-else class="page-container center">加载中...</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api/index.js'
import { useUserStore } from '../../stores/user.js'
import NavBar from '../../components/NavBar.vue'
import ReadingNav from '../../components/ReadingNav.vue'

import { useToast } from '../../composables/useToast.js'
const toast = useToast()
const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const from = computed(() => route.query.from || 'write')
const book = ref(null)
const chapters = ref([])
const volumes = ref([])
const onShelf = ref(false)
const shelfId = ref(null)
const error = ref('')

// 书评相关
const reviews = ref([])
const reviewStats = ref({ count: 0, avg_rating: 0, star5: 0, star4: 0, star3: 0, star2: 0, star1: 0 })
const userReview = ref(null)
const reviewForm = reactive({ rating: 5, content: '' })
const submitting = ref(false)
const ratingTexts = ['很差', '较差', '一般', '推荐', '力荐']

const source = ref(route.params.source || 'library')
const bookId = ref(route.params.id)

onMounted(async () => {
  const res = await api.get(`/api/library/${bookId.value}?source=${source.value}`)
  if (res.code === 0) {
    book.value = res.data.book
    chapters.value = res.data.chapters || []
    volumes.value = (res.data.volumes || []).map(v => ({ ...v, _open: true }))
    onShelf.value = res.data.on_shelf || false
    shelfId.value = res.data.shelf_id || null
    // 加载书评
    loadReviews()
    if (userStore.isLoggedIn) loadUserReview()
  } else {
    error.value = res.msg || '加载失败'
  }
})

function getVolumeChapters(volumeId) {
  return chapters.value.filter(ch => ch.volume_id === volumeId)
}

function startReading() {
  if (chapters.value.length > 0) {
    readChapter(chapters.value[0])
  }
}

function readChapter(ch) {
  router.push(`/reader/${source.value}/${bookId.value}?chapter=${ch.chapter_id}`)
}

async function toggleShelf() {
  if (onShelf.value) {
    // 移除书架
    if (!shelfId.value) return
    const res = await api.delete(`/api/bookshelf/${shelfId.value}`)
    if (res.code === 0) {
      onShelf.value = false
      shelfId.value = null
    } else {
      toast.info(res.msg)
    }
  } else {
    // 加入书架
    const res = await api.post('/api/bookshelf', {
      book_type: source.value,
      book_id: Number(bookId.value),
      shelf_group: 'want_read',
    })
    if (res.code === 0) {
      onShelf.value = true
      shelfId.value = res.data.shelf_id
    } else {
      toast.info(res.msg)
    }
  }
}

function shareBook() {
  const url = window.location.href
  if (navigator.clipboard) {
    navigator.clipboard.writeText(url)
    toast.success('链接已复制到剪贴板')
  } else {
    toast.info(url)
  }
}

function typeLabel(t) {
  return { novel: '小说', poetry: '诗歌', essay: '散文', webfiction: '网文', script: '剧本' }[t] || t
}

function coverClass(t) {
  return t || 'default'
}

function formatWordCount(wc) {
  if (!wc) return '0'
  if (wc >= 10000) return (wc / 10000).toFixed(1) + '万'
  return wc.toLocaleString()
}

// ====== 书评 ======
async function loadReviews() {
  const res = await api.get(`/api/library/reviews/${bookId.value}`)
  if (res.code === 0) {
    reviews.value = res.data.reviews
    reviewStats.value = res.data.stats
  }
}

async function loadUserReview() {
  const res = await api.get(`/api/library/reviews/user/${bookId.value}`)
  if (res.code === 0 && res.data.review) {
    userReview.value = res.data.review
    reviewForm.rating = res.data.review.rating
    reviewForm.content = res.data.review.content || ''
  }
}

async function submitReview() {
  submitting.value = true
  const res = await api.post('/api/library/reviews', {
    book_id: Number(bookId.value),
    rating: reviewForm.rating,
    content: reviewForm.content.trim(),
  })
  if (res.code === 0) {
    toast.success(userReview.value ? '书评已更新' : '书评已发布')
    loadReviews()
    loadUserReview()
  } else {
    toast.info(res.msg)
  }
  submitting.value = false
}

async function deleteReview() {
  if (!userReview.value) return
  const res = await api.delete(`/api/library/reviews/${userReview.value.review_id}`)
  if (res.code === 0) {
    userReview.value = null
    reviewForm.rating = 5
    reviewForm.content = ''
    loadReviews()
  }
}

function getBarWidth(star) {
  if (!reviewStats.value.count) return 0
  return (reviewStats.value['star' + star] / reviewStats.value.count) * 100
}
</script>

<style scoped>
.page-container { }
/* ====== 头部 ====== */
.detail-header {
  margin-bottom: var(--space-xl);
}
.header-top { margin-bottom: var(--space-md); }
.header-actions { display: flex; gap: var(--space-sm); flex-wrap: wrap; }

/* ====== 书籍信息 ====== */
.book-info { display: flex; gap: var(--space-2xl); margin-bottom: var(--space-xl); }

.book-cover {
  width: 180px; height: 240px; flex-shrink: 0;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, rgba(196,163,90,0.12), rgba(196,163,90,0.04));
  display: flex; align-items: flex-end; justify-content: center;
  padding: var(--space-md);
  position: relative; overflow: hidden;
}
.book-cover::after {
  content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 4px;
  background: linear-gradient(90deg, var(--accent-primary), transparent);
}
.book-cover.poetry { background: linear-gradient(135deg, rgba(167,139,250,0.12), rgba(167,139,250,0.04)); }
.book-cover.poetry::after { background: linear-gradient(90deg, var(--accent-purple), transparent); }
.book-cover.essay { background: linear-gradient(135deg, rgba(126,200,227,0.12), rgba(126,200,227,0.04)); }
.book-cover.essay::after { background: linear-gradient(90deg, var(--accent-cool), transparent); }
.book-cover.webfiction { background: linear-gradient(135deg, rgba(244,132,95,0.12), rgba(244,132,95,0.04)); }
.book-cover.webfiction::after { background: linear-gradient(90deg, var(--accent-warm), transparent); }

.cover-type {
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.06em;
  color: var(--text-muted); z-index: 1;
}

.book-detail { flex: 1; }
.book-meta { display: flex; gap: var(--space-sm); margin-bottom: var(--space-sm); }
.type-badge { font-size: 0.72rem; color: var(--accent-primary); text-transform: uppercase; letter-spacing: 0.06em; }
.source-badge {
  font-size: 0.65rem; padding: 1px 8px; border-radius: var(--radius-full);
  background: rgba(196,163,90,0.1); color: var(--accent-primary);
  border: 1px solid rgba(196,163,90,0.2);
}

h1 {
  font-family: var(--font-serif); font-size: 1.8rem; font-weight: 700;
  margin-bottom: var(--space-sm); line-height: 1.3;
}
.book-author { font-size: 0.9rem; color: var(--text-muted); margin-bottom: var(--space-md); }
.book-summary {
  font-size: 0.9rem; color: var(--text-secondary); line-height: 1.7;
  margin-bottom: var(--space-md);
}
.tags { display: flex; gap: var(--space-sm); flex-wrap: wrap; margin-bottom: var(--space-md); }
.tag {
  font-size: 0.78rem; padding: 2px 10px; border-radius: var(--radius-full);
  background: var(--bg-glass); border: 1px solid var(--border-glass); color: var(--text-secondary);
}

.stats {
  display: flex; gap: var(--space-xl); padding: var(--space-md) 0;
  border-top: 1px solid var(--border-glass);
}
.stat-item { text-align: center; }
.stat-value {
  display: block; font-size: 1.1rem; font-weight: 600; color: var(--text-primary);
}
.stat-label { font-size: 0.72rem; color: var(--text-muted); }

hr { border: none; border-top: 1px solid var(--border-glass); margin: var(--space-xl) 0; }

/* ====== 书评 ====== */
.section-reviews { margin-bottom: var(--space-2xl); }

.rating-summary {
  display: flex; gap: var(--space-xl); padding: var(--space-xl);
  margin-bottom: var(--space-lg);
}
.rating-big { text-align: center; min-width: 100px; }
.rating-number {
  display: block; font-size: 2.5rem; font-weight: 700;
  font-family: var(--font-serif); color: var(--accent-primary);
}
.rating-stars { font-size: 1.1rem; color: var(--accent-primary); letter-spacing: 2px; }
.rating-count { font-size: 0.78rem; color: var(--text-muted); }
.rating-bars { flex: 1; display: flex; flex-direction: column; gap: 6px; justify-content: center; }
.rating-bar-row { display: flex; align-items: center; gap: var(--space-sm); }
.bar-label { font-size: 0.72rem; color: var(--text-muted); width: 28px; text-align: right; }
.bar-track { flex: 1; height: 6px; background: rgba(255,255,255,0.06); border-radius: 3px; overflow: hidden; }
.bar-fill { height: 100%; background: var(--accent-primary); border-radius: 3px; }
.bar-count { font-size: 0.72rem; color: var(--text-muted); width: 24px; }

.review-form {
  padding: var(--space-xl); margin-bottom: var(--space-lg);
}
.review-form h4 { font-size: 0.95rem; margin-bottom: var(--space-md); }
.star-input { display: flex; align-items: center; gap: 4px; margin-bottom: var(--space-md); }
.star-btn {
  font-size: 1.4rem; color: rgba(255,255,255,0.15); cursor: pointer;
  transition: color 0.2s ease;
}
.star-btn.active { color: var(--accent-primary); }
.star-btn:hover { color: var(--accent-primary); }
.rating-text { font-size: 0.82rem; color: var(--text-muted); margin-left: var(--space-sm); }
.review-form textarea {
  width: 100%; padding: 10px; font-size: 0.9rem; resize: vertical;
  background: rgba(255,255,255,0.04); color: var(--text-primary);
  border: 1px solid var(--border-glass); border-radius: var(--radius-sm); outline: none;
  margin-bottom: var(--space-md);
}
.review-form textarea:focus { border-color: var(--accent-primary); }
.form-actions { display: flex; gap: var(--space-sm); }

.login-hint {
  text-align: center; padding: var(--space-xl);
  margin-bottom: var(--space-lg);
}
.login-hint p { font-size: 0.85rem; color: var(--text-muted); margin-bottom: var(--space-md); }

.review-list { display: flex; flex-direction: column; gap: var(--space-md); }
.review-item { padding: var(--space-lg); }
.review-header { display: flex; align-items: center; gap: var(--space-md); margin-bottom: var(--space-md); }
.review-avatar {
  width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
  background: var(--accent-purple); color: white;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.8rem; font-weight: 700;
}
.review-meta { flex: 1; }
.review-meta strong { display: block; font-size: 0.88rem; }
.review-stars { font-size: 0.78rem; color: var(--accent-primary); letter-spacing: 1px; }
.review-time { font-size: 0.72rem; color: var(--text-muted); }
.review-content { font-size: 0.9rem; line-height: 1.7; color: var(--text-secondary); }

/* ====== 目录 ====== */
.section-title {
  font-family: var(--font-serif); font-size: 1.15rem; font-weight: 600;
  color: var(--text-primary); margin-bottom: var(--space-lg);
  padding-left: var(--space-md);
  border-left: 3px solid var(--accent-primary);
}

.volume-group { margin-bottom: var(--space-md); }
.volume-header {
  display: flex; align-items: center; gap: var(--space-sm);
  padding: var(--space-sm) var(--space-md);
  cursor: pointer; border-radius: var(--radius-sm);
  transition: background 0.2s ease;
}
.volume-header:hover { background: rgba(255,255,255,0.02); }
.volume-toggle { font-size: 0.7rem; color: var(--text-muted); width: 16px; }
.volume-title { font-size: 0.92rem; font-weight: 500; flex: 1; }
.volume-count { font-size: 0.75rem; color: var(--text-muted); }

.chapter-list { padding-left: var(--space-lg); }
.chapter-item {
  display: flex; align-items: center; gap: var(--space-md);
  padding: var(--space-sm) var(--space-md);
  cursor: pointer; border-radius: var(--radius-sm);
  transition: all 0.2s ease; border-left: 2px solid transparent;
}
.chapter-item:hover {
  background: rgba(196,163,90,0.03);
  border-left-color: var(--accent-primary);
}
.ch-no { font-size: 0.78rem; color: var(--text-muted); width: 32px; text-align: right; flex-shrink: 0; }
.ch-title { flex: 1; font-size: 0.88rem; }
.ch-wc { font-size: 0.72rem; color: var(--text-muted); flex-shrink: 0; }

.empty-hint { font-size: 0.85rem; color: var(--text-muted); text-align: center; padding: var(--space-xl) 0; }
.center { text-align: center; padding: var(--space-2xl); color: var(--text-muted); }

/* ====== 响应式 ====== */
@media (max-width: 768px) {
  .book-info { flex-direction: column; align-items: center; text-align: center; }
  .book-cover { width: 140px; height: 190px; }
  .book-meta { justify-content: center; }
  .tags { justify-content: center; }
  .stats { justify-content: center; }
}
</style>
