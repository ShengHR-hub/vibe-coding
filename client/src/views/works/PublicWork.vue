<template>
  <div class="page-container">
    <div v-if="loading" class="center muted" style="padding: 4rem 0">加载中…</div>
    <div v-else-if="error" class="center muted" style="padding: 4rem 0">{{ error }}</div>

    <template v-else-if="work">
      <!-- 顶栏 -->
      <div class="topbar">
        <button class="btn btn-ghost btn-sm" @click="goBack">&larr; 返回</button>
        <span class="type-badge">{{ typeLabel }}</span>
      </div>

      <!-- 作品信息 -->
      <section class="work-info glass-card">
        <h1 class="work-title">{{ work.title || '未命名作品' }}</h1>
        <div class="author-row">
          <img v-if="work.avatar" :src="work.avatar" class="author-avatar" />
          <span v-else class="author-avatar placeholder">{{ work.username?.charAt(0) }}</span>
          <router-link :to="`/profile/${work.user_id}`" class="author-name">{{ work.username }}</router-link>
        </div>
        <p v-if="work.summary" class="summary">{{ work.summary }}</p>

        <div class="meta-chips">
          <span class="meta-chip">字数 {{ work.word_count || 0 }}</span>
          <span class="meta-chip">章节 {{ work.chapter_count || chapters.length || 0 }}</span>
          <span class="meta-chip">浏览 {{ work.views || 0 }}</span>
          <span class="meta-chip">更新 {{ fmtDate(work.updated_at) }}</span>
        </div>
        <div v-if="tags" class="tags">
          <span v-for="t in tags" :key="t" class="tag-chip">#{{ t }}</span>
        </div>

        <!-- 互动 -->
        <div class="action-row">
          <button class="action-btn" :class="{ on: liked }" :disabled="liking" @click="toggleLike">
            {{ liked ? '♥ 已赞' : '♡ 点赞' }} {{ likesCount }}
          </button>
          <button class="action-btn" :class="{ on: favorited }" :disabled="favoriting" @click="toggleFavorite">
            {{ favorited ? '★ 已收藏' : '☆ 收藏' }} {{ favoritesCount }}
          </button>
        </div>
        <p v-if="!userStore.isLoggedIn" class="login-hint">
          <router-link to="/login">登录</router-link> 后可点赞、收藏与评论
        </p>
      </section>

      <!-- 章节目录（正文阅读未开放） -->
      <section class="chapters glass-card">
        <h2 class="sec-title">章节目录</h2>
        <p v-if="!chapters.length" class="muted empty">暂无章节</p>
        <ol v-else class="chapter-list">
          <li v-for="(ch, i) in chapters" :key="ch.chapter_id" class="chapter-row">
            <span class="ch-no">{{ i + 1 }}</span>
            <span class="ch-title">{{ ch.title || `第${ch.chapter_no || i + 1}章` }}</span>
            <span class="ch-wc">{{ ch.word_count || 0 }} 字</span>
          </li>
        </ol>
        <p class="muted lock-note">🔒 公开页暂不展示正文，作品内容请在作者创作管理页查看</p>
      </section>

      <!-- 评论 -->
      <section class="comments glass-card">
        <h2 class="sec-title">评论（{{ commentsTotal }}）</h2>
        <div v-if="userStore.isLoggedIn" class="comment-form">
          <textarea v-model="commentText" rows="2" placeholder="写下你的感受…"></textarea>
          <div class="form-foot">
            <button class="btn btn-primary btn-sm" :disabled="!commentText.trim() || posting" @click="postComment">
              {{ posting ? '发表中…' : '发表评论' }}
            </button>
          </div>
        </div>
        <div v-if="!comments.length" class="muted empty">还没有评论，来抢沙发~</div>
        <div v-else class="comment-list">
          <div v-for="c in comments" :key="c.comment_id" class="comment-item">
            <div class="c-head">
              <img v-if="c.avatar" :src="c.avatar" class="c-avatar" />
              <span v-else class="c-avatar placeholder">{{ c.username?.charAt(0) }}</span>
              <span class="c-name">{{ c.username }}</span>
              <span class="c-time">{{ c.created_at }}</span>
            </div>
            <p class="c-content">{{ c.content }}</p>
            <div v-if="c.replies?.length" class="c-replies">
              <div v-for="r in c.replies" :key="r.comment_id" class="comment-item reply">
                <div class="c-head">
                  <span class="c-name">{{ r.username }}</span>
                  <span class="c-time">{{ r.created_at }}</span>
                </div>
                <p class="c-content">回复：{{ r.content }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api/index.js'
import { useUserStore } from '../../stores/user.js'
import { useToast } from '../../composables/useToast.js'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const toast = useToast()

const work = ref(null)
const chapters = ref([])
const liked = ref(false)
const favorited = ref(false)
const likesCount = ref(0)
const favoritesCount = ref(0)
const loading = ref(true)
const error = ref('')
const liking = ref(false)
const favoriting = ref(false)

const comments = ref([])
const commentsTotal = ref(0)
const commentText = ref('')
const posting = ref(false)

const TYPE_NAMES = { novel: '小说', poetry: '诗歌', essay: '散文', script: '剧本' }
const typeLabel = computed(() => TYPE_NAMES[work.value?.type] || work.value?.type || '')
const tags = computed(() => (work.value?.tags || '').split(/[,，]/).map(s => s.trim()).filter(Boolean))

function fmtDate(v) {
  if (!v) return ''
  return String(v).slice(0, 10)
}

function goBack() {
  if (window.history.length > 1) router.back()
  else router.push('/explore')
}

async function load() {
  loading.value = true
  const res = await api.get(`/api/works/public/${route.params.id}`)
  if (res.code !== 0) {
    error.value = res.msg || '作品不存在或未发布'
    loading.value = false
    return
  }
  work.value = res.data.work
  chapters.value = res.data.chapters || []
  liked.value = !!res.data.liked
  favorited.value = !!res.data.favorited
  likesCount.value = work.value.likes_count || 0
  favoritesCount.value = work.value.favorites_count || 0
  loading.value = false
  loadComments()
}

async function toggleLike() {
  if (!userStore.isLoggedIn) { router.push('/login'); return }
  liking.value = true
  const res = await api.post('/api/interactions/like', { work_id: work.value.work_id })
  liking.value = false
  if (res.code === 0) {
    liked.value = !!res.data.liked
    likesCount.value += liked.value ? 1 : -1
    toast.success(res.msg)
  } else toast.error(res.msg)
}

async function toggleFavorite() {
  if (!userStore.isLoggedIn) { router.push('/login'); return }
  favoriting.value = true
  const res = await api.post('/api/interactions/favorite', { work_id: work.value.work_id })
  favoriting.value = false
  if (res.code === 0) {
    favorited.value = !!res.data.favorited
    favoritesCount.value += favorited.value ? 1 : -1
    toast.success(res.msg)
  } else toast.error(res.msg)
}

async function loadComments() {
  const res = await api.get(`/api/interactions/comments/${route.params.id}`)
  if (res.code === 0) {
    comments.value = res.data.comments || []
    commentsTotal.value = res.data.total || 0
  }
}

async function postComment() {
  const content = commentText.value.trim()
  if (!content) return
  posting.value = true
  const res = await api.post('/api/interactions/comments', { work_id: work.value.work_id, content })
  posting.value = false
  if (res.code === 0) {
    toast.success('评论已发表')
    commentText.value = ''
    loadComments()
  } else toast.error(res.msg)
}

onMounted(load)
</script>

<style scoped>
.page-container { max-width: 860px; margin: 0 auto; padding: 1.2rem 1rem 3rem; }
.topbar { display: flex; align-items: center; gap: 10px; margin-bottom: 1rem; }
.type-badge {
  font-size: 0.75rem; padding: 3px 12px; border-radius: var(--radius-full);
  background: rgba(196,163,90,0.12); color: var(--accent-primary);
}
.work-info { padding: 1.6rem 2rem; margin-bottom: 1.2rem; }
.work-title { font-family: var(--font-serif); font-size: 1.6rem; margin: 0 0 0.8rem; }
.author-row { display: flex; align-items: center; gap: 8px; margin-bottom: 0.9rem; }
.author-avatar { width: 28px; height: 28px; border-radius: 50%; object-fit: cover; }
.author-avatar.placeholder {
  display: inline-flex; align-items: center; justify-content: center;
  background: var(--accent-primary); color: var(--bg-primary); font-size: 0.8rem;
}
.author-name { font-size: 0.9rem; color: var(--accent-primary); text-decoration: none; }
.summary { color: var(--text-secondary); line-height: 1.9; margin: 0 0 1rem; white-space: pre-wrap; }
.meta-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 0.8rem; }
.meta-chip {
  font-size: 0.74rem; padding: 3px 10px; border-radius: var(--radius-sm);
  background: var(--bg-glass); border: 1px solid var(--border-glass); color: var(--text-muted);
}
.tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 1rem; }
.tag-chip { font-size: 0.75rem; color: var(--accent-primary); }
.action-row { display: flex; gap: 10px; }
.action-btn {
  font-size: 0.85rem; padding: 7px 16px; border-radius: var(--radius-md);
  background: rgba(196,163,90,0.06); border: 1px solid rgba(196,163,90,0.2);
  color: var(--text-secondary); cursor: pointer;
}
.action-btn.on { color: var(--accent-primary); border-color: rgba(196,163,90,0.5); background: rgba(196,163,90,0.12); }
.login-hint { font-size: 0.78rem; color: var(--text-muted); margin-top: 0.8rem; }

.chapters, .comments { padding: 1.3rem 1.6rem; margin-bottom: 1.2rem; }
.sec-title { font-family: var(--font-serif); font-size: 1.1rem; margin: 0 0 0.9rem; }
.chapter-list { list-style: none; margin: 0; padding: 0; }
.chapter-row {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 6px; border-bottom: 1px dashed rgba(196,163,90,0.1);
}
.ch-no {
  width: 22px; height: 22px; flex-shrink: 0; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  background: rgba(196,163,90,0.12); color: var(--accent-primary); font-size: 0.72rem;
}
.ch-title { flex: 1; font-size: 0.9rem; }
.ch-wc { font-size: 0.72rem; color: var(--text-muted); }
.lock-note { margin: 0.9rem 0 0; font-size: 0.78rem; }
.empty { padding: 0.8rem 0; }

.comment-form textarea {
  width: 100%; box-sizing: border-box; padding: 8px 12px; font-size: 0.86rem;
  border-radius: var(--radius-sm); background: var(--bg-glass);
  border: 1px solid var(--border-glass); color: var(--text-primary); resize: vertical;
}
.form-foot { display: flex; justify-content: flex-end; margin-top: 6px; }
.comment-list { margin-top: 0.8rem; display: flex; flex-direction: column; gap: 0.8rem; }
.comment-item { border: 1px solid rgba(196,163,90,0.08); border-radius: var(--radius-md); padding: 0.7rem 0.9rem; }
.c-head { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.c-avatar { width: 24px; height: 24px; border-radius: 50%; object-fit: cover; }
.c-avatar.placeholder {
  display: inline-flex; align-items: center; justify-content: center; font-size: 0.72rem;
  background: rgba(196,163,90,0.2); color: var(--accent-primary);
}
.c-name { font-size: 0.82rem; font-weight: 600; }
.c-time { font-size: 0.7rem; color: var(--text-muted); }
.c-content { margin: 0; font-size: 0.86rem; line-height: 1.7; color: var(--text-secondary); }
.c-replies { margin-top: 0.6rem; padding-left: 0.8rem; border-left: 2px solid rgba(196,163,90,0.15); display: flex; flex-direction: column; gap: 0.5rem; }
.comment-item.reply { border: none; padding: 0; }
.muted { color: var(--text-muted); }
</style>
