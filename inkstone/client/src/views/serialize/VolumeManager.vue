<template>
  <div class="page-container">
    <div class="vm-header">
      <button class="btn btn-ghost" @click="$router.back()">&larr; 返回</button>
      <h2>{{ workTitle }} — 卷管理</h2>
      <div class="header-right">
        <span class="status-badge" :class="serStatus" @click="cycleStatus">{{ statusLabel }}</span>
      </div>
    </div>

    <div class="vm-body">
      <!-- 左：卷列表 -->
      <aside class="vm-sidebar glass-card">
        <div class="sidebar-title">卷目录</div>
        <div
          v-for="vol in volumes" :key="vol.volume_id"
          class="vol-item" :class="{ active: activeVolId === vol.volume_id }"
          @click="activeVolId = vol.volume_id"
          @dragover.prevent
          @drop="onDropToVolume($event, vol.volume_id)"
        >
          <span class="vol-no">{{ vol.volume_no }}</span>
          <span class="vol-title" v-if="editingVolId !== vol.volume_id">{{ vol.title }}</span>
          <input v-else v-model="editingVolTitle" class="vol-edit-input" @blur="saveVolTitle(vol)" @keydown.enter="saveVolTitle(vol)" />
          <span class="vol-count">{{ vol.chapter_count }}章</span>
          <div class="vol-actions">
            <button class="vol-btn" @click.stop="startEditVol(vol)" title="重命名">&#9998;</button>
            <button class="vol-btn danger" @click.stop="deleteVol(vol)" title="删除">&times;</button>
          </div>
        </div>
        <div
          class="vol-item unassigned" :class="{ active: activeVolId === null }"
          @click="activeVolId = null"
          @dragover.prevent
          @drop="onDropToVolume($event, null)"
        >
          <span class="vol-no">?</span>
          <span class="vol-title">未分卷</span>
          <span class="vol-count">{{ unassigned.length }}章</span>
        </div>
        <button class="add-vol-btn" @click="createVol">+ 新建卷</button>
      </aside>

      <!-- 右：章节列表 -->
      <main class="vm-main">
        <div v-if="activeVolId !== null && activeVolume" class="vol-summary">
          <p v-if="activeVolume.summary">{{ activeVolume.summary }}</p>
          <p class="muted">共 {{ activeVolume.chapter_count }} 章，{{ activeVolume.total_words?.toLocaleString() }} 字</p>
        </div>
        <div v-else class="vol-summary">
          <p class="muted">以下章节尚未分配到任何卷</p>
        </div>

        <div class="ch-list">
          <div
            v-for="ch in currentChapters" :key="ch.chapter_id"
            class="ch-item"
            draggable="true"
            @dragstart="onDragStart($event, ch)"
          >
            <span class="ch-no">{{ ch.chapter_no }}</span>
            <span class="ch-title">{{ ch.title || `第${ch.chapter_no}章` }}</span>
            <span class="ch-wc">{{ ch.word_count || 0 }}字</span>
          </div>
          <div v-if="currentChapters.length === 0" class="empty-hint">暂无章节</div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../api/index.js'

const route = useRoute()
const workId = route.params.id
const workTitle = ref('')
const volumes = ref([])
const unassigned = ref([])
const serStatus = ref('serializing')
const activeVolId = ref(null)
const editingVolId = ref(null)
const editingVolTitle = ref('')

const statusLabel = computed(() => ({
  serializing: '连载中', completed: '已完结', paused: '已暂停'
}[serStatus.value] || serStatus.value))

const activeVolume = computed(() => volumes.value.find(v => v.volume_id === activeVolId.value))

const currentChapters = computed(() => {
  if (activeVolId.value === null) return unassigned.value
  const vol = volumes.value.find(v => v.volume_id === activeVolId.value)
  return vol?.chapters || []
})

async function load() {
  const [volRes, workRes] = await Promise.all([
    api.get(`/api/serialize/${workId}/volumes`),
    api.get(`/api/works/${workId}`),
  ])
  if (volRes.code === 0) {
    volumes.value = volRes.data.volumes || []
    unassigned.value = volRes.data.unassigned || []
    serStatus.value = volRes.data.serialization_status || 'serializing'
  }
  if (workRes.code === 0) {
    workTitle.value = workRes.data.work?.title || ''
  }
}

async function createVol() {
  const res = await api.post(`/api/serialize/${workId}/volumes`, {})
  if (res.code === 0) await load()
}

function startEditVol(vol) {
  editingVolId.value = vol.volume_id
  editingVolTitle.value = vol.title
}

async function saveVolTitle(vol) {
  if (!editingVolTitle.value.trim()) { editingVolId.value = null; return }
  await api.put(`/api/serialize/${workId}/volumes/${vol.volume_id}`, { title: editingVolTitle.value.trim() })
  editingVolId.value = null
  await load()
}

async function deleteVol(vol) {
  if (!confirm(`确定删除「${vol.title}」？章节将变为未分卷状态。`)) return
  await api.delete(`/api/serialize/${workId}/volumes/${vol.volume_id}`)
  if (activeVolId.value === vol.volume_id) activeVolId.value = null
  await load()
}

async function cycleStatus() {
  const next = { serializing: 'completed', completed: 'paused', paused: 'serializing' }[serStatus.value]
  const res = await api.put(`/api/serialize/${workId}/status`, { serialization_status: next })
  if (res.code === 0) serStatus.value = next
}

function onDragStart(e, ch) {
  e.dataTransfer.setData('text/plain', JSON.stringify({ chapter_id: ch.chapter_id }))
}

async function onDropToVolume(e, volumeId) {
  const data = JSON.parse(e.dataTransfer.getData('text/plain'))
  if (!data?.chapter_id) return
  await api.put(`/api/serialize/${workId}/chapters/${data.chapter_id}/volume`, { volume_id: volumeId })
  await load()
}

onMounted(load)
</script>

<style scoped>
.vm-header {
  display: flex; align-items: center; gap: 1rem;
  margin-bottom: 1.5rem;
}
.vm-header h2 { flex: 1; font-family: var(--font-serif); font-size: 1.2rem; }
.header-right { display: flex; gap: 0.5rem; }
.status-badge {
  padding: 4px 14px; border-radius: 20px; font-size: 0.78rem; font-weight: 600;
  cursor: pointer; transition: all 0.2s;
}
.status-badge.serializing { background: rgba(76, 175, 80, 0.15); color: #4caf50; }
.status-badge.completed { background: rgba(196, 163, 90, 0.15); color: var(--accent-primary); }
.status-badge.paused { background: rgba(158, 158, 158, 0.15); color: #9e9e9e; }

.vm-body { display: flex; gap: 1rem; min-height: 60vh; }
.vm-sidebar {
  width: 240px; flex-shrink: 0; padding: 0.75rem;
  border-radius: var(--radius-lg);
  background: var(--glass-bg, rgba(255,255,255,0.04));
  border: 1px solid var(--glass-border, rgba(255,255,255,0.06));
  backdrop-filter: blur(16px);
}
.sidebar-title { font-size: 0.75rem; font-weight: 600; color: var(--text-muted); letter-spacing: 0.08em; margin-bottom: 0.5rem; }
.vol-item {
  display: flex; align-items: center; gap: 0.4rem;
  padding: 0.5rem 0.6rem; border-radius: 6px; cursor: pointer;
  margin-bottom: 2px; transition: all 0.2s;
}
.vol-item:hover { background: rgba(196, 163, 90, 0.06); }
.vol-item.active { background: rgba(196, 163, 90, 0.1); border-left: 2px solid var(--accent-primary); }
.vol-no { font-size: 0.7rem; font-weight: 700; color: var(--accent-primary); opacity: 0.6; min-width: 16px; }
.vol-item.active .vol-no { opacity: 1; }
.vol-title { flex: 1; font-size: 0.82rem; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.vol-item.active .vol-title { color: var(--text-primary); }
.vol-count { font-size: 0.65rem; color: var(--text-muted); }
.vol-actions { display: none; gap: 2px; }
.vol-item:hover .vol-actions { display: flex; }
.vol-btn {
  background: none; border: none; color: var(--text-muted); cursor: pointer;
  font-size: 0.75rem; padding: 2px 4px; border-radius: 3px;
}
.vol-btn:hover { background: rgba(196, 163, 90, 0.1); color: var(--text-primary); }
.vol-btn.danger:hover { background: rgba(220, 60, 60, 0.12); color: #e55; }
.vol-edit-input {
  flex: 1; font-size: 0.82rem; background: transparent; border: 1px solid var(--accent-primary);
  border-radius: 4px; padding: 2px 6px; color: var(--text-primary); outline: none;
}
.add-vol-btn {
  width: 100%; padding: 0.5rem; font-size: 0.78rem; color: var(--text-muted);
  background: none; border: 1px dashed rgba(196, 163, 90, 0.2); border-radius: 6px;
  cursor: pointer; margin-top: 0.5rem; transition: all 0.2s;
}
.add-vol-btn:hover { color: var(--accent-primary); border-color: rgba(196, 163, 90, 0.4); }
.unassigned { opacity: 0.7; }

.vm-main {
  flex: 1; padding: 1rem;
  border-radius: var(--radius-lg);
  background: var(--glass-bg, rgba(255,255,255,0.04));
  border: 1px solid var(--glass-border, rgba(255,255,255,0.06));
  backdrop-filter: blur(16px);
}
.vol-summary { margin-bottom: 1rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--border-glass); }
.vol-summary p { font-size: 0.85rem; color: var(--text-secondary); margin: 0; }
.muted { color: var(--text-muted); font-size: 0.8rem; }
.ch-list { display: flex; flex-direction: column; gap: 2px; }
.ch-item {
  display: flex; align-items: center; gap: 0.5rem;
  padding: 0.6rem 0.75rem; border-radius: 6px;
  transition: background 0.15s; cursor: grab;
}
.ch-item:hover { background: rgba(196, 163, 90, 0.06); }
.ch-no { font-size: 0.7rem; font-weight: 700; color: var(--accent-primary); opacity: 0.5; min-width: 20px; }
.ch-title { flex: 1; font-size: 0.85rem; color: var(--text-secondary); }
.ch-wc { font-size: 0.65rem; color: var(--text-muted); }
.empty-hint { text-align: center; color: var(--text-muted); padding: 2rem; font-size: 0.85rem; }
</style>
