<template>
  <div class="page-container" v-if="work">
    <div class="editor-header">
      <button class="btn btn-ghost" @click="$router.push('/works')">&larr; 返回列表</button>
      <div class="header-info">
        <input class="title-input" v-model="work.title" placeholder="作品标题" @change="markDirty" />
        <span class="word-count">{{ wordCount }} 字</span>
        <select :value="work.status" @change="toggleStatus($event)" class="status-select">
          <option value="draft">草稿</option>
          <option value="published">发布</option>
          <option value="private">私密</option>
        </select>
        <span v-if="saving" class="save-hint">保存中...</span>
        <span v-else-if="dirty" class="save-hint dirty">未保存</span>
        <span v-else class="save-hint saved">已保存</span>
      </div>
    </div>

    <div class="editor-body">
      <div class="editor-main">
        <input v-model="currentChapter.title" placeholder="章节标题" class="chapter-title" @change="markDirty" />
        <textarea
          ref="editorRef"
          class="editor-area"
          v-model="currentChapter.content"
          placeholder="开始写作..."
          @input="markDirty"
        ></textarea>
      </div>

      <div class="editor-sidebar">
        <div class="sidebar-section">
          <h4>作品信息</h4>
          <label>标签</label>
          <input v-model="work.tags" placeholder="用逗号分隔" @change="markDirty" />
          <label>简介</label>
          <textarea v-model="work.summary" rows="3" placeholder="作品简介..." @change="markDirty"></textarea>
        </div>

        <div class="sidebar-section">
          <h4>历史版本</h4>
          <div v-if="versions.length === 0" class="muted">暂无版本记录</div>
          <div v-for="v in versions" :key="v.version_id" class="version-item">
            <span>{{ fmt(v.saved_at) }}</span>
            <span class="muted">{{ v.word_count }} 字</span>
            <button class="btn btn-ghost btn-xs" @click="rollback(v.version_id)" :disabled="rollingBack">回退</button>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div v-else-if="error" class="page-container center">{{ error }}</div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api/index.js'

import { useToast } from '../../composables/useToast.js'
const toast = useToast()
const route = useRoute()
const router = useRouter()
const work = ref(null)
const currentChapter = ref({ title: '', content: '' })
const versions = ref([])
const error = ref('')
const saving = ref(false)
const dirty = ref(false)
const rollingBack = ref(false)
let saveTimer = null

const wordCount = computed(() => {
  return (currentChapter.value.content || '').replace(/\s/g, '').length
})

onMounted(async () => {
  const res = await api.get(`/api/works/${route.params.id}`)
  if (res.code === 0) {
    work.value = res.data.work
    if (res.data.chapters && res.data.chapters.length > 0) {
      currentChapter.value = res.data.chapters[0]
    }
    loadVersions()
  } else {
    error.value = res.msg
  }
  saveTimer = setInterval(autoSave, 30000)
})

onUnmounted(() => {
  clearInterval(saveTimer)
})

async function loadVersions() {
  const res = await api.get(`/api/works/${route.params.id}/versions`)
  if (res.code === 0) versions.value = res.data.versions
}

function markDirty() {
  dirty.value = true
}

async function autoSave() {
  if (!dirty.value || !work.value) return
  await doSave()
}

async function doSave() {
  saving.value = true
  const res = await api.put(`/api/works/${work.value.work_id}`, {
    title: work.value.title,
    summary: work.value.summary,
    tags: work.value.tags,
    chapter_id: currentChapter.value.chapter_id,
    chapter_title: currentChapter.value.title,
    content: currentChapter.value.content
  })
  if (res.code === 0) {
    dirty.value = false
    loadVersions()
  }
  saving.value = false
}

async function toggleStatus(e) {
  const newStatus = e.target.value
  const oldStatus = work.value.status
  work.value.status = newStatus
  const res = await api.put(`/api/works/${work.value.work_id}/status`, { status: newStatus })
  if (res.code !== 0) {
    work.value.status = oldStatus
    toast.info(res.msg)
  }
}

async function rollback(versionId) {
  if (!confirm('回退将覆盖当前内容，确定继续？')) return
  rollingBack.value = true
  const res = await api.post(`/api/works/${work.value.work_id}/versions/${versionId}/rollback`)
  if (res.code === 0) {
    const reload = await api.get(`/api/works/${route.params.id}`)
    if (reload.code === 0) {
      work.value = reload.data.work
      if (reload.data.chapters && reload.data.chapters.length > 0) {
        currentChapter.value = reload.data.chapters[0]
      }
      loadVersions()
    }
  } else {
    toast.info(res.msg)
  }
  rollingBack.value = false
}

function fmt(d) {
  if (!d) return ''
  return d.slice(0, 16).replace('T', ' ')
}
</script>

<style scoped>
.editor-header {
  display: flex;
  align-items: center;
  gap: var(--space-lg);
  margin-bottom: var(--space-lg);
}
.header-info {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  flex: 1;
}
.title-input {
  font-size: 1.2rem;
  font-weight: 600;
  border: none;
  background: transparent;
  padding: 4px 0;
  flex: 1;
  max-width: 300px;
}
.title-input:focus { border-color: transparent; }
.word-count { font-size: 0.85rem; color: var(--text-muted); white-space: nowrap; }
.status-select { padding: 4px 8px; font-size: 0.8rem; }
.save-hint { font-size: 0.75rem; }
.save-hint.saved { color: var(--accent-green); }
.save-hint.dirty { color: var(--accent-warm); }

.editor-body { display: flex; gap: var(--space-lg); }
.editor-main { flex: 1; min-width: 0; }
.chapter-title {
  width: 100%;
  font-size: 1.1rem;
  padding: 8px 12px;
  margin-bottom: var(--space-md);
}
.editor-area {
  width: 100%;
  min-height: 60vh;
  resize: vertical;
  padding: 1.5rem;
  font-family: var(--font-serif);
  font-size: 1.05rem;
  line-height: 1.9;
  border-radius: var(--radius-lg);
  background: var(--bg-glass);
  border: 1px solid var(--border-glass);
  color: var(--text-primary);
}
.editor-area:focus { border-color: var(--accent-primary); }

.editor-sidebar { width: 280px; flex-shrink: 0; }
.sidebar-section {
  background: var(--bg-glass);
  border: 1px solid var(--border-glass);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  margin-bottom: var(--space-md);
}
.sidebar-section h4 { margin-bottom: var(--space-md); font-size: 0.9rem; color: var(--text-secondary); }
.sidebar-section label { display: block; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 4px; }
.sidebar-section input, .sidebar-section textarea {
  width: 100%;
  padding: 6px 10px;
  font-size: 0.85rem;
  margin-bottom: var(--space-sm);
}
.version-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 6px 0;
  font-size: 0.8rem;
  border-bottom: 1px solid var(--border-glass);
}
.version-item:last-child { border-bottom: none; }
.muted { color: var(--text-muted); font-size: 0.8rem; }
.btn-xs { padding: 2px 8px; font-size: 0.7rem; }
.center { text-align: center; padding: var(--space-2xl); color: var(--text-muted); }
</style>
