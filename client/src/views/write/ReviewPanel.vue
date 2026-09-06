<template>
  <div class="panel">
    <!-- P6-C4：结构审校 + 内容诊断 合并入口（两步走） -->
    <div class="review-tabs">
      <button class="rv-tab" :class="{ active: step === 'struct' }" @click="step = 'struct'">
        <span class="rv-ico">∞</span>结构审校
      </button>
      <button class="rv-tab" :class="{ active: step === 'diag' }" @click="step = 'diag'">
        <span class="rv-ico">♧</span>内容诊断
      </button>
      <p class="rv-hint">第{{ step === 'struct' ? '1' : '2' }}步 — {{ step === 'struct' ? '对照大纲查结构，再看正文逐章诊断' : '对当前章节文字做 AI 多维诊断' }}，两步都过再交付。</p>
    </div>

    <div v-show="step === 'struct'" class="rv-step">
      <StructurePanel />
    </div>
    <div v-show="step === 'diag'" class="rv-step">
      <DiagnosePanel :content="writingStore.content" />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useWritingStore } from '../../stores/writing.js'
import StructurePanel from './StructurePanel.vue'
import DiagnosePanel from './DiagnosePanel.vue'

const writingStore = useWritingStore()
const step = ref('struct')
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';

.review-tabs {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 6px;
}
.rv-tab {
  padding: 5px 14px;
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(196, 163, 90, 0.2);
  border-radius: 20px;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}
.rv-tab:hover { color: var(--accent-primary); border-color: var(--accent-primary); }
.rv-tab.active {
  color: var(--accent-primary);
  background: rgba(196, 163, 90, 0.1);
  border-color: var(--accent-primary);
}
.rv-ico { font-size: 0.85rem; }
.rv-hint {
  width: 100%;
  margin: 2px 0 8px;
  font-size: 0.72rem;
  color: var(--text-muted);
  line-height: 1.7;
}
.rv-step { margin-top: 4px; }
</style>