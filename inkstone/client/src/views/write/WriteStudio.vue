<template>
  <div class="studio-layout">
    <div class="editor-panel">
      <div class="editor-toolbar">
        <span class="word-count">{{ writingStore.wordCount }} 字</span>
        <button class="btn btn-outline btn-sm" @click="saveDraft">保存草稿</button>
      </div>
      <textarea
        class="editor-area"
        v-model="writingStore.content"
        placeholder="开始书写你的故事..."
      ></textarea>
    </div>

    <div class="ai-panel glass-card">
      <div class="ai-tabs">
        <button
          v-for="tab in tabs" :key="tab.key"
          class="ai-tab"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >{{ tab.label }}</button>
      </div>
      <div class="ai-content">
        <ContinuePanel v-if="activeTab === 'continue'" :content="writingStore.content" />
        <InspirePanel v-else-if="activeTab === 'inspire'" />
        <OutlinePanel v-else-if="activeTab === 'outline'" />
        <CharacterPanel v-else-if="activeTab === 'character'" />
        <PolishPanel v-else-if="activeTab === 'polish'" :content="writingStore.content" />
        <PromptPanel v-else-if="activeTab === 'prompt'" :content="writingStore.content" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useWritingStore } from '../../stores/writing.js'
import { api } from '../../api/index.js'
import ContinuePanel from './ContinuePanel.vue'
import InspirePanel from './InspirePanel.vue'
import OutlinePanel from './OutlinePanel.vue'
import CharacterPanel from './CharacterPanel.vue'
import PolishPanel from './PolishPanel.vue'
import PromptPanel from './PromptPanel.vue'

const writingStore = useWritingStore()
const activeTab = ref('continue')

const tabs = [
  { key: 'continue', label: '续写' },
  { key: 'inspire', label: '灵感' },
  { key: 'outline', label: '大纲' },
  { key: 'character', label: '角色' },
  { key: 'polish', label: '润色' },
  { key: 'prompt', label: '提示' },
]

function saveDraft() {
  alert('草稿保存功能即将上线')
}

let statsTimer = null
let lastSentCount = 0
onMounted(() => {
  lastSentCount = writingStore.wordCount
  statsTimer = setInterval(() => {
    const delta = writingStore.wordCount - lastSentCount
    lastSentCount = writingStore.wordCount
    if (delta > 0) {
      api.post('/api/stats/session', {
        work_id: writingStore.currentWorkId || null,
        word_count: delta,
        duration: 30
      }).catch(() => {})
    }
  }, 30000)
})
onUnmounted(() => {
  if (statsTimer) clearInterval(statsTimer)
})
</script>

<style scoped>
.studio-layout {
  display: flex;
  height: calc(100vh - 80px - 2rem);
  gap: 1rem;
  padding: 1rem;
  max-width: 1400px;
  margin: 0 auto;
}
.editor-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.editor-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0;
}
.word-count { font-size: 0.85rem; color: var(--text-muted); }
.editor-area {
  flex: 1;
  width: 100%;
  resize: none;
  padding: 1.5rem;
  font-family: var(--font-serif);
  font-size: 1.05rem;
  line-height: 1.9;
  border-radius: var(--radius-lg);
  background: var(--bg-glass);
  border: 1px solid var(--border-glass);
  color: var(--text-primary);
}
.editor-area::placeholder { color: var(--text-muted); }
.editor-area:focus { border-color: var(--accent-primary); }

.ai-panel {
  width: 440px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.ai-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-glass);
  padding: 0 0.5rem;
  flex-shrink: 0;
}
.ai-tab {
  padding: 10px 14px;
  font-size: 0.85rem;
  color: var(--text-muted);
  background: none;
  border-bottom: 2px solid transparent;
  transition: all var(--transition-fast);
}
.ai-tab:hover { color: var(--text-secondary); }
.ai-tab.active {
  color: var(--accent-primary);
  border-bottom-color: var(--accent-primary);
}
.ai-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}
</style>
