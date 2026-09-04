<template>
  <div class="panel">
    <p class="hint" v-if="!workId">💡 保存作品后，扫描全书章节中的 [TODO: 内容] / [待补：内容] 标注，集中处理收尾。</p>
    <template v-else>
      <div class="toolbar">
        <button class="btn btn-ghost btn-sm" @click="scan">重新扫描</button>
        <span class="count" v-if="items.length">共 {{ items.length }} 处</span>
      </div>
      <div v-if="!items.length" class="empty">🎉 全书没有遗留 [TODO] 标注</div>
      <div v-else class="todo-list">
        <div v-for="(it, i) in items" :key="i" class="todo-item" @click="jump(it)">
          <span class="t-ch">{{ it.chapterTitle }}</span>
          <span class="t-text">{{ it.text }}</span>
        </div>
      </div>
      <p class="hint small">写初稿时遇到暂时缺的资料，可直接在正文里写 [TODO: 补充xxx]，收尾阶段来这里统一补齐，支持点击跳转章节。</p>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useWritingStore } from '../../stores/writing.js'

const writingStore = useWritingStore()
const workId = computed(() => writingStore.currentWorkId)
const items = ref([])

const TODO_RE = /\[(TODO|待补)\s*[:：]?([^\]]+)\]/g

function scan() {
  items.value = []
  for (const ch of writingStore.chapters) {
    const content = ch.content || ''
    TODO_RE.lastIndex = 0
    let m
    while ((m = TODO_RE.exec(content))) {
      items.value.push({ chapter_id: ch.chapter_id, chapterTitle: ch.title || `第${ch.chapter_no}章`, text: m[2].trim() || '(未写补充说明)' })
    }
  }
}

async function jump(it) {
  if (it.chapter_id === writingStore.activeChapterId) return
  await writingStore.switchChapter(it.chapter_id)
}

onMounted(scan)
watch([workId, () => writingStore.activeChapterId], () => scan())
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';

.hint { font-size: 0.8rem; color: var(--text-muted); line-height: 1.8; }
.hint.small { margin-top: 10px; }
.toolbar { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.count { font-size: 0.75rem; color: var(--text-muted); }
.empty { text-align: center; padding: 1.5rem 0; color: var(--text-secondary); font-size: 0.9rem; }
.todo-list { display: flex; flex-direction: column; gap: 6px; }
.todo-item {
  display: flex; flex-direction: column; gap: 2px; padding: 8px 10px;
  background: rgba(224, 113, 107, 0.06);
  border: 1px solid rgba(224, 113, 107, 0.18);
  border-radius: var(--radius-sm); cursor: pointer;
}
.todo-item:hover { background: rgba(224, 113, 107, 0.12); }
.t-ch { font-size: 0.72rem; color: #e0716b; }
.t-text { font-size: 0.85rem; color: var(--text-primary); }
</style>
