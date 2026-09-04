<template>
  <div class="panel refs-panel">
    <div class="ref-toggle">
      <button class="rt-btn" :class="{ active: sub === 'poem' }" @click="sub = 'poem'">诗词</button>
      <button class="rt-btn" :class="{ active: sub === 'material' }" @click="sub = 'material'">句子素材</button>
    </div>
    <PoemPanel v-if="sub === 'poem'" />
    <MaterialPanel v-else />
    <p class="ref-note">在条目上点「＋ 引用」，内容会进入顶部引用条，续写 / 对话会自动携带这些素材。</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import PoemPanel from './PoemPanel.vue'
import MaterialPanel from './MaterialPanel.vue'

const sub = ref('poem')
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';

.refs-panel { display: flex; flex-direction: column; }
.ref-toggle { display: flex; gap: 6px; margin-bottom: 10px; }
.rt-btn {
  font-size: 0.8rem; padding: 4px 16px; border-radius: var(--radius-full);
  background: var(--bg-glass); border: 1px solid var(--border-glass);
  color: var(--text-secondary); cursor: pointer;
}
.rt-btn.active { color: var(--accent-primary); border-color: rgba(196,163,90,0.5); background: rgba(196,163,90,0.1); }
.ref-note { font-size: 0.74rem; color: var(--text-muted); margin: 10px 0 0; line-height: 1.7; }
</style>
