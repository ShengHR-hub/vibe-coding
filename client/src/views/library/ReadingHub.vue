<template>
  <div class="reading-hub">
    <ReadingNav />

    <!-- 页面内容 -->
    <div class="hub-content">
      <!-- 头部 -->
      <div class="hub-header">
        <h2>阅读</h2>
        <p class="header-sub">沉浸阅读，发现好书</p>
      </div>

      <!-- 继续阅读 -->
      <section v-if="recentBooks.length" class="section-recent">
        <h3 class="section-title">继续阅读</h3>
        <div class="recent-list">
          <div v-for="book in recentBooks" :key="book.book_type + '-' + book.book_id"
               class="recent-item glass-card" @click="goRead(book)">
            <div class="recent-cover" :class="coverClass(book.type || '')"></div>
            <div class="recent-info">
              <h4>{{ book.title || '未知书籍' }}</h4>
              <p class="recent-meta">
                第{{ book.chapter_no }}章 · {{ book.total_percent }}%
              </p>
              <div class="recent-progress">
                <div class="progress-track">
                  <div class="progress-fill" :style="{ width: book.total_percent + '%' }"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 功能入口 -->
      <section class="section-entries">
        <div class="entries-grid">
          <div class="entry-card glass-card" @click="$router.push('/bookshelf')">
            <span class="entry-icon">&#128218;</span>
            <span class="entry-label">我的书架</span>
            <span class="entry-desc">管理收藏的书籍</span>
          </div>
          <div class="entry-card glass-card" @click="$router.push('/library')">
            <span class="entry-icon">&#128214;</span>
            <span class="entry-label">书库</span>
            <span class="entry-desc">发现更多好书</span>
          </div>
          <div class="entry-card glass-card" @click="$router.push('/highlights')">
            <span class="entry-icon">&#10024;</span>
            <span class="entry-label">好句</span>
            <span class="entry-desc">收藏的精彩句子</span>
          </div>
          <div class="entry-card glass-card" @click="$router.push('/annotations')">
            <span class="entry-icon">&#128221;</span>
            <span class="entry-label">批注</span>
            <span class="entry-desc">阅读笔记与思考</span>
          </div>
          <div class="entry-card glass-card" @click="$router.push('/reading-report')">
            <span class="entry-icon">&#128202;</span>
            <span class="entry-label">阅读报告</span>
            <span class="entry-desc">年度阅读数据</span>
          </div>
          <div class="entry-card glass-card" @click="$router.push('/library/upload')">
            <span class="entry-icon">&#128228;</span>
            <span class="entry-label">导入书籍</span>
            <span class="entry-desc">上传 TXT 入库</span>
          </div>
        </div>
      </section>

      <!-- 为你推荐 -->
      <section v-if="recommendations.length" class="section-recommend">
        <h3 class="section-title">为你推荐</h3>
        <p v-if="preference" class="recommend-hint">根据你的阅读偏好：{{ preference.map(p => typeLabel(p.type)).join('、') }}</p>
        <div class="recommend-grid">
          <div v-for="book in recommendations" :key="book.book_id"
               class="recommend-item glass-card" @click="$router.push(`/library/${book.source}/${book.book_id}`)">
            <div class="recommend-cover" :class="book.type"></div>
            <div class="recommend-info">
              <h4>{{ book.title }}</h4>
              <p class="recommend-meta">{{ book.author }}</p>
              <div class="recommend-rating" v-if="book.rating_avg > 0">
                <span class="rating-stars">★</span>
                <span>{{ book.rating_avg }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 未登录提示 -->
      <div v-if="!userStore.isLoggedIn" class="login-hint glass-card">
        <p>登录后可同步阅读进度、管理书架</p>
        <router-link to="/login" class="btn btn-primary btn-sm">登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../../api/index.js'
import { useUserStore } from '../../stores/user.js'
import ReadingNav from '../../components/ReadingNav.vue'

const router = useRouter()
const userStore = useUserStore()
const recentBooks = ref([])
const recommendations = ref([])
const preference = ref(null)

onMounted(async () => {
  if (!userStore.isLoggedIn) return
  const res = await api.get('/api/reading/history?limit=3')
  if (res.code === 0) recentBooks.value = res.data.items
  // 加载推荐
  loadRecommendations()
})

async function loadRecommendations() {
  const res = await api.get('/api/library/recommend?limit=6')
  if (res.code === 0) {
    recommendations.value = res.data.items
    preference.value = res.data.preference
  }
}

function goRead(book) {
  router.push(`/reader/${book.book_type}/${book.book_id}`)
}

function coverClass(t) {
  return t || 'default'
}

function typeLabel(t) {
  return { novel: '小说', poetry: '诗歌', essay: '散文', webfiction: '网文', script: '剧本' }[t] || t || '其他'
}
</script>

<style scoped>
.reading-hub {
  min-height: 100vh;
  background: var(--bg-primary);
}

/* ====== 内容区 ====== */
.hub-content {
  max-width: 800px;
  margin: 0 auto;
  padding: 80px var(--space-xl) var(--space-2xl);
}

/* ====== 头部 ====== */
.hub-header {
  text-align: center; margin-bottom: var(--space-2xl);
  padding: var(--space-xl) 0;
}
.hub-header h2 {
  font-family: var(--font-serif); font-size: 2.2rem; font-weight: 700;
  background: linear-gradient(135deg, #e8e6f0, #c4a35a);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text; margin-bottom: var(--space-sm);
}
.header-sub { font-size: 0.9rem; color: var(--text-muted); letter-spacing: 0.04em; }

/* ====== 继续阅读 ====== */
.section-recent { margin-bottom: var(--space-2xl); }
.section-title {
  font-family: var(--font-serif); font-size: 1.15rem; font-weight: 600;
  color: var(--text-primary); margin-bottom: var(--space-lg);
  padding-left: var(--space-md);
  border-left: 3px solid var(--accent-primary);
}
.recent-list { display: flex; flex-direction: column; gap: var(--space-md); }
.recent-item {
  display: flex; gap: var(--space-lg); padding: var(--space-lg);
  cursor: pointer; transition: all 0.3s ease;
  border-left: 3px solid transparent;
}
.recent-item:hover { border-left-color: var(--accent-primary); transform: translateY(-2px); }
.recent-cover {
  width: 48px; height: 64px; flex-shrink: 0; border-radius: var(--radius-sm);
  background: linear-gradient(135deg, rgba(196,163,90,0.12), rgba(196,163,90,0.04));
  position: relative; overflow: hidden;
}
.recent-cover::after {
  content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 2px;
  background: linear-gradient(90deg, var(--accent-primary), transparent);
}
.recent-info { flex: 1; min-width: 0; }
.recent-info h4 { font-size: 0.95rem; margin-bottom: 4px; }
.recent-meta { font-size: 0.78rem; color: var(--text-muted); margin-bottom: var(--space-sm); }
.recent-progress { display: flex; align-items: center; gap: var(--space-sm); }
.progress-track { flex: 1; height: 3px; background: rgba(255,255,255,0.06); border-radius: 2px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--accent-primary); border-radius: 2px; }

/* ====== 功能入口 ====== */
.entries-grid {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-lg);
}
.entry-card {
  display: flex; flex-direction: column; align-items: center;
  padding: var(--space-xl) var(--space-lg); text-align: center;
  cursor: pointer; transition: all 0.3s ease;
  border-top: 3px solid transparent;
}
.entry-card:hover { border-top-color: var(--accent-primary); transform: translateY(-3px); }
.entry-icon { font-size: 2rem; margin-bottom: var(--space-sm); }
.entry-label { font-size: 1rem; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.entry-desc { font-size: 0.78rem; color: var(--text-muted); }

/* ====== 为你推荐 ====== */
.section-recommend { margin-bottom: var(--space-2xl); }
.recommend-hint { font-size: 0.78rem; color: var(--text-muted); margin-bottom: var(--space-lg); }
.recommend-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--space-md); }
.recommend-item {
  display: flex; gap: var(--space-md); padding: var(--space-md);
  cursor: pointer; transition: all 0.3s ease;
  border-left: 3px solid transparent;
}
.recommend-item:hover { border-left-color: var(--accent-primary); transform: translateY(-2px); }
.recommend-cover {
  width: 40px; height: 54px; flex-shrink: 0; border-radius: var(--radius-sm);
  background: linear-gradient(135deg, rgba(196,163,90,0.12), rgba(196,163,90,0.04));
}
.recommend-cover.poetry { background: linear-gradient(135deg, rgba(167,139,250,0.12), rgba(167,139,250,0.04)); }
.recommend-cover.essay { background: linear-gradient(135deg, rgba(126,200,227,0.12), rgba(126,200,227,0.04)); }
.recommend-cover.webfiction { background: linear-gradient(135deg, rgba(244,132,95,0.12), rgba(244,132,95,0.04)); }
.recommend-info { flex: 1; min-width: 0; }
.recommend-info h4 { font-size: 0.85rem; margin-bottom: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.recommend-meta { font-size: 0.72rem; color: var(--text-muted); margin-bottom: 4px; }
.recommend-rating { font-size: 0.72rem; color: var(--accent-primary); display: flex; align-items: center; gap: 4px; }
.rating-stars { letter-spacing: 1px; }

/* ====== 未登录 ====== */
.login-hint {
  text-align: center; padding: var(--space-xl);
  margin-top: var(--space-2xl);
}
.login-hint p { font-size: 0.9rem; color: var(--text-muted); margin-bottom: var(--space-md); }

/* ====== 响应式 ====== */
@media (max-width: 768px) {
  .entries-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
