<template>
  <Teleport to="body">
    <div v-if="visible" class="ob-overlay" @click.self="close">
      <div class="ob-card">
        <div class="ob-head">
          <h3 class="ob-title">从哪开始？</h3>
          <button class="ob-close" @click="close">✕</button>
        </div>
        <p class="ob-desc">写书第一步：先接住你心里那个"想写的东西"。选一条路开始——以后随时可从右上角「说明」重新进入。</p>
        <div class="ob-options">
          <button class="ob-opt" @click="choose('guide')">
            <span class="ob-opt-ico">导</span>
            <span class="ob-opt-name">跟随引导（新手）</span>
            <span class="ob-opt-sub">在写作台右侧一步步完成灵感 → 主线 → 大纲 → 动笔</span>
          </button>
          <button class="ob-opt" @click="choose('pro')">
            <span class="ob-opt-ico">写</span>
            <span class="ob-opt-name">直接开始（老手）</span>
            <span class="ob-opt-sub">用完整写作台：面板 + AI + 素材引用</span>
          </button>
          <button class="ob-opt" @click="choose('plain')">
            <span class="ob-opt-ico">静</span>
            <span class="ob-opt-name">只想安静写</span>
            <span class="ob-opt-sub">纯净页面：只有写作、保存、导出</span>
          </button>
        </div>
        <p class="ob-foot">说明详文制作中 · 帮助文档占位</p>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '../composables/useToast.js'

const visible = ref(false)
const router = useRouter()
const toast = useToast()

const MODE_KEY = 'inkstone_mode'

function open() { visible.value = true }
function close() { visible.value = false }
defineExpose({ open })

function choose(mode) {
  localStorage.setItem(MODE_KEY, mode)
  visible.value = false
  if (mode === 'plain') {
    router.push('/write/plain')
  } else if (mode === 'guide') {
    router.push('/write?tool=workshop')
  }
  // pro：留在当前写作台
}
</script>

<style scoped>
.ob-overlay {
  position: fixed; inset: 0; z-index: 900;
  display: flex; align-items: center; justify-content: center;
  /* 纯色遮罩（跟项目其他 modal 惯例一致），不用 backdrop-filter——全屏模糊每帧合成会卡 GPU */
  background: rgba(0, 0, 0, 0.55);
}
.ob-card {
  width: min(480px, 92vw); padding: 22px 24px; border-radius: 16px;
  background: var(--bg-panel, #1a1c24); border: 1px solid rgba(196, 163, 90, 0.25);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
}
.ob-head { display: flex; justify-content: space-between; align-items: center; }
.ob-title { font-family: var(--font-serif); margin: 0; font-size: 1.2rem; }
.ob-close { background: none; border: none; color: var(--text-muted); font-size: 1rem; cursor: pointer; }
.ob-desc { color: var(--text-secondary); font-size: 0.85rem; line-height: 1.8; }
.ob-options { display: flex; flex-direction: column; gap: 10px; margin-top: 6px; }
.ob-opt {
  display: flex; align-items: center; gap: 12px; text-align: left;
  padding: 12px 14px; border-radius: 12px; cursor: pointer;
  background: var(--bg-glass); border: 1px solid transparent; color: var(--text-primary);
  transition: all 0.15s;
}
.ob-opt:hover { border-color: rgba(196, 163, 90, 0.5); background: rgba(196, 163, 90, 0.1); }
.ob-opt-ico { font-size: 1.3rem; }
.ob-opt-name { font-weight: 600; font-size: 0.92rem; }
.ob-opt-sub { display: block; color: var(--text-muted); font-size: 0.78rem; margin-top: 2px; }
.ob-foot { color: var(--text-muted); font-size: 0.75rem; margin: 14px 0 0; }
.ob-foot a { color: var(--accent-primary); }
</style>