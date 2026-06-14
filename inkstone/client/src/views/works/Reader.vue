<template>
  <div class="reader-container" v-if="work">
    <div class="reader-toolbar">
      <button class="btn btn-ghost btn-sm" @click="$router.back()">&larr; 返回</button>
      <div class="toolbar-actions">
        <button class="btn btn-ghost btn-sm" @click="toggleLike" :class="{ active: liked }">
          {{ liked ? '❤️' : '🤍' }} {{ work.likes_count || 0 }}
        </button>
        <button class="btn btn-ghost btn-sm" @click="toggleFavorite" :class="{ active: favorited }">
          {{ favorited ? '⭐' : '☆' }} 收藏
        </button>
        <select v-model.number="fontSize" class="font-select">
          <option :value="14">小字</option>
          <option :value="16">标准</option>
          <option :value="18">大字</option>
          <option :value="22">特大</option>
        </select>
        <span v-if="userStore.isLoggedIn" class="btn btn-ghost btn-sm" @click="goToGraph()">知识图谱</span>
        <span v-if="userStore.isLoggedIn" class="btn btn-ghost btn-sm" @click="goToReview()">AI 书评</span>
        <span class="btn btn-ghost btn-sm" @click="handleExport">导出</span>
      </div>
    </div>

    <div class="reader-content" :style="{ fontSize: fontSize + 'px' }">
      <div v-if="work.type === 'novel'" class="chapter-nav">
        <select v-model="activeChapterIdx" class="chapter-select">
          <option v-for="(ch, i) in chapters" :key="ch.chapter_id" :value="i">
            {{ ch.title || `第${ch.chapter_no}章` }}
          </option>
        </select>
      </div>

      <h1 class="work-title">{{ work.title }}</h1>
      <div class="work-info">
        <span>{{ work.username }}</span>
        <span>{{ typeLabel(work.type) }}</span>
        <span>{{ work.word_count || 0 }} 字</span>
      </div>

      <div class="chapter-content" v-html="renderedContent"></div>

      <hr />

      <!-- Comments -->
      <div class="comments-section">
        <h3>评论 ({{ comments.length }})</h3>
        <div v-if="userStore.isLoggedIn" class="comment-form">
          <textarea v-model="newComment" rows="2" placeholder="写下你的评论..."></textarea>
          <button class="btn btn-primary btn-sm" @click="submitComment(null)" :disabled="!newComment.trim() || submitting">发表</button>
        </div>
        <div v-else class="muted">请<router-link to="/login">登录</router-link>后发表评论</div>

        <div v-if="comments.length === 0" class="muted" style="margin-top:1rem">暂无评论</div>

        <div v-for="c in comments" :key="c.comment_id" class="comment">
          <div class="comment-header">
            <span class="comment-avatar">{{ c.username?.charAt(0) }}</span>
            <strong>{{ c.username }}</strong>
            <span class="muted">{{ fmt(c.created_at) }}</span>
          </div>
          <p>{{ c.content }}</p>
          <button v-if="userStore.isLoggedIn" class="btn btn-ghost btn-xs" @click="replyingTo = replyingTo === c.comment_id ? null : c.comment_id">回复</button>

          <div v-if="replyingTo === c.comment_id" class="comment-form reply-form">
            <textarea v-model="replyContent" rows="2" placeholder="写下回复..."></textarea>
            <button class="btn btn-primary btn-xs" @click="submitComment(c.comment_id)" :disabled="!replyContent.trim()">回复</button>
          </div>

          <div v-if="c.replies?.length" class="replies">
            <div v-for="r in c.replies" :key="r.comment_id" class="comment reply">
              <div class="comment-header">
                <span class="comment-avatar">{{ r.username?.charAt(0) }}</span>
                <strong>{{ r.username }}</strong>
                <span class="muted">{{ fmt(r.created_at) }}</span>
              </div>
              <p>{{ r.content }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-else-if="errorMsg" class="page-container center">{{ errorMsg }}</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api/index.js'
import { useUserStore } from '../../stores/user.js'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const work = ref(null)
const chapters = ref([])
const comments = ref([])
const errorMsg = ref('')
const liked = ref(false)
const favorited = ref(false)
const fontSize = ref(16)
const activeChapterIdx = ref(0)
const newComment = ref('')
const replyContent = ref('')
const replyingTo = ref(null)
const submitting = ref(false)

const renderedContent = computed(() => {
  const ch = chapters.value[activeChapterIdx.value]
  if (!ch?.content) return '<p class="muted">暂无内容</p>'
  return ch.content
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
})

onMounted(async () => {
  const res = await api.get(`/api/works/public/${route.params.id}`)
  if (res.code === 0) {
    work.value = res.data.work
    chapters.value = res.data.chapters || []
    liked.value = res.data.liked || false
    favorited.value = res.data.favorited || false
    await loadComments()
  } else {
    errorMsg.value = res.msg
  }
})

async function loadComments() {
  const res = await api.get(`/api/interactions/comments/${route.params.id}`)
  if (res.code === 0) comments.value = res.data.comments
}

async function toggleLike() {
  if (!userStore.isLoggedIn) { alert('请先登录'); return }
  const res = await api.post('/api/interactions/like', { work_id: work.value.work_id })
  if (res.code === 0) {
    liked.value = res.data.liked
    work.value.likes_count += res.data.liked ? 1 : -1
  }
}

async function toggleFavorite() {
  if (!userStore.isLoggedIn) { alert('请先登录'); return }
  const res = await api.post('/api/interactions/favorite', { work_id: work.value.work_id })
  if (res.code === 0) favorited.value = res.data.favorited
}

async function submitComment(parentId) {
  const content = parentId ? replyContent.value.trim() : newComment.value.trim()
  if (!content) return
  submitting.value = true
  const res = await api.post('/api/interactions/comments', { work_id: work.value.work_id, content, parent_id: parentId })
  if (res.code === 0) {
    if (parentId) { replyContent.value = ''; replyingTo.value = null } else { newComment.value = '' }
    await loadComments()
    work.value.comments_count = (work.value.comments_count || 0) + 1
  } else {
    alert(res.msg)
  }
  submitting.value = false
}

function goToGraph() {
  console.log('[Reader] goToGraph clicked, work_id:', work.value?.work_id)
  if (work.value) router.push(`/graph/${work.value.work_id}`)
}
async function handleExport() {
  const res = await api.download(`/api/works/${work.value.work_id}/export`)
  if (res.code !== 0) alert(res.msg || '导出失败')
}
function goToReview() {
  console.log('[Reader] goToReview clicked, work_id:', work.value?.work_id)
  if (work.value) router.push(`/review/${work.value.work_id}`)
}
function typeLabel(t) {
  return { novel: '小说', poetry: '诗歌', essay: '散文', script: '剧本' }[t] || t
}
function fmt(d) { if (!d) return ''; return d.slice(0, 16).replace('T', ' ') }
</script>

<style scoped>
.reader-container { min-height: 100vh; }
.reader-toolbar {
  position: sticky; top: 80px; z-index: 50;
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.5rem 1.5rem;
  background: var(--glass-bg, rgba(255, 255, 255, 0.04));
  backdrop-filter: blur(var(--glass-blur, 16px));
  border-bottom: 1px solid var(--glass-border, rgba(255, 255, 255, 0.06));
}
.toolbar-actions { display: flex; gap: var(--space-sm); align-items: center; }
.toolbar-actions .active { color: var(--accent-warm); }
.font-select {
  padding: 4px 8px; font-size: 0.75rem;
  background: var(--bg-glass); color: var(--text-secondary);
  border: 1px solid var(--border-glass); border-radius: var(--radius-sm);
  outline: none;
}
.font-select:focus { border-color: var(--accent-primary); }
.reader-content {
  max-width: 720px; margin: 2rem auto; padding: 3rem 2.5rem;
  border-radius: var(--radius-lg); min-height: 60vh; line-height: 2;
  background: var(--glass-bg, rgba(255, 255, 255, 0.04));
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.06));
  backdrop-filter: blur(var(--glass-blur, 16px));
  box-shadow:
    0 0 2px 1px color-mix(in oklch, canvastext, #0000 90%) inset,
    0 0 10px 4px color-mix(in oklch, canvastext, #0000 95%) inset,
    0px 4px 16px rgba(17, 17, 26, 0.05),
    0px 8px 24px rgba(17, 17, 26, 0.05),
    0px 16px 56px rgba(17, 17, 26, 0.05);
}
.chapter-nav { margin-bottom: var(--space-xl); }
.chapter-select {
  padding: 8px 14px; font-size: 0.9rem; width: 100%;
  background: transparent; color: inherit;
  border: 1px solid var(--border-glass);
  border-radius: var(--radius-sm); outline: none;
}
.work-title { font-size: 2rem; margin-bottom: var(--space-md); font-family: var(--font-serif); letter-spacing: 0.05em; }
.work-info { display: flex; gap: var(--space-lg); font-size: 0.85rem; color: var(--text-muted); margin-bottom: var(--space-2xl); }
.chapter-content :deep(p) { margin-bottom: 1em; text-indent: 2em; }
hr { border: none; border-top: 1px solid var(--border-glass); margin: var(--space-2xl) 0; }

.comments-section h3 { margin-bottom: var(--space-lg); color: var(--accent-primary); }
.comment-form { display: flex; gap: var(--space-sm); margin-bottom: var(--space-lg); }
.comment-form textarea {
  flex: 1; padding: 10px; font-size: 0.9rem; resize: vertical;
  background: transparent; color: inherit;
  border: 1px solid var(--border-glass);
  border-radius: var(--radius-sm); outline: none;
}
.comment-form textarea:focus { border-color: var(--accent-primary); }
.reply-form { margin: var(--space-sm) 0 var(--space-sm) var(--space-xl); }
.comment { padding: var(--space-md) 0; border-bottom: 1px solid var(--border-glass); }
.comment.reply { margin-left: var(--space-xl); }
.comment-header { display: flex; align-items: center; gap: var(--space-sm); margin-bottom: var(--space-sm); font-size: 0.85rem; }
.comment-avatar { width: 26px; height: 26px; border-radius: 50%; background: var(--accent-purple); color: white; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; }
.comment p { font-size: 0.9rem; }
.replies { margin-top: var(--space-sm); }
.muted { color: var(--text-muted); font-size: 0.85rem; }
.center { text-align: center; padding: var(--space-2xl); color: var(--text-muted); }
.btn-xs { padding: 2px 8px; font-size: 0.7rem; }
.btn-sm { padding: 4px 12px; font-size: 0.85rem; }
</style>
