<template>
  <Teleport to="body">
    <div v-if="visible" class="gd-overlay" @click.self="close">
      <div class="gd-card">
        <div class="gd-head">
          <h3 class="gd-title">墨池使用说明</h3>
          <button class="gd-close" @click="close">✕</button>
        </div>
        <div class="gd-body">
          <p class="gd-lead">墨池有两个写作系统 + 纯净写作，按你的习惯选一条路：</p>

          <section class="gd-sec">
            <h4 class="gd-sec-title">1. 新手系统（推荐第一次用）</h4>
            <p class="gd-txt">左边写作，右边跟着「灵感 → 主线 → 卷级大纲 → 主角」一步步把书立起来。AI 只在你点按钮时帮忙，不强制、不用也完全行。</p>
            <p class="gd-flow"><b>操作流程：</b>进入新手系统 → 创建/打开作品 → （可选）写灵感 → AI 或自己写主线 → 保存 → 生成/写卷级大纲 → 保存 → 写主角 → 直接开写</p>
            <p class="gd-pros"><b>优点：</b>有引导不容易懵，结构自然成型。<b>注意：</b>功能精简，深度加工请去老手系统。</p>
          </section>

          <section class="gd-sec">
            <h4 class="gd-sec-title">2. 老手系统（功能全）</h4>
            <p class="gd-txt">完整写作台：立项蓝图、三级大纲、设定库、角色、任务卡、续写、教练、审查、润色、交付，全部面板按「起·承·合」组织。</p>
            <p class="gd-flow"><b>操作流程：</b>进入写作台 → 保存作品生成 work_id → 「起」定目标（蓝图/大纲/设定）→ 「承」写作（任务卡/续写/教练）→ 「合」收尾（审校/润色/诊断/交付）</p>
            <p class="gd-pros"><b>优点：</b>功能最全。<b>注意：</b>面板多，新手初期可能无所适从。</p>
          </section>

          <section class="gd-sec">
            <h4 class="gd-sec-title">3. 纯净写作</h4>
            <p class="gd-txt">只有一个编辑区：选作品 → 写 → 保存 / 导出。没有面板、没有 AI 按钮。</p>
            <p class="gd-flow"><b>操作流程：</b>选/建作品 → 写作（Ctrl+S 保存）→ 导出 txt</p>
            <p class="gd-pros"><b>优点：</b>零干扰。<b>注意：</b>无 AI 辅助，进阶功能需回写作台。</p>
          </section>
        </div>
        <div class="gd-foot">
          <label class="gd-today">
            <input type="checkbox" v-model="todayOnly" /> 今天不再弹出
          </label>
          <button class="btn btn-primary" @click="close">知道了</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const visible = ref(false)
const todayOnly = ref(false)
const GUIDE_KEY = 'inkstone_guide_dismiss'

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}

function open(auto = false) {
  // 自动弹出时检查「今天不再弹」；手动打开（头像菜单）始终弹
  if (auto && localStorage.getItem(GUIDE_KEY) === todayStr()) return
  visible.value = true
}

function close() {
  visible.value = false
  if (todayOnly.value) localStorage.setItem(GUIDE_KEY, todayStr())
  todayOnly.value = false
}

function onOpenGuide() {
  open(false)
}

onMounted(() => window.addEventListener('inkstone:open-guide', onOpenGuide))
onUnmounted(() => window.removeEventListener('inkstone:open-guide', onOpenGuide))

defineExpose({ open })
</script>

<style scoped>
.gd-overlay {
  position: fixed; inset: 0; z-index: 950;
  display: flex; align-items: center; justify-content: center; padding: 1rem;
  background: rgba(0, 0, 0, 0.55);
}
.gd-card {
  width: min(560px, 94vw); max-height: 86vh; display: flex; flex-direction: column;
  padding: 20px 24px; border-radius: 16px; background: var(--bg-panel, #1a1c24);
  border: 1px solid rgba(196, 163, 90, 0.25); box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
}
.gd-head { display: flex; justify-content: space-between; align-items: center; }
.gd-title { font-family: var(--font-serif); margin: 0; font-size: 1.15rem; }
.gd-close { background: none; border: none; color: var(--text-muted); font-size: 1rem; cursor: pointer; }
.gd-body { overflow-y: auto; margin: 12px 0; padding-right: 4px; }
.gd-lead { font-size: 0.88rem; color: var(--text-secondary); margin: 0 0 12px; }
.gd-sec { margin-bottom: 14px; }
.gd-sec-title { font-size: 0.95rem; margin: 0 0 4px; color: var(--accent-primary); }
.gd-txt { font-size: 0.82rem; line-height: 1.8; color: var(--text-secondary); margin: 0 0 6px; }
.gd-flow { font-size: 0.78rem; line-height: 1.8; color: var(--text-muted); margin: 0 0 4px; }
.gd-pros { font-size: 0.78rem; line-height: 1.8; color: var(--text-muted); margin: 0; }
.gd-foot { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(196,163,90,0.15); padding-top: 10px; }
.gd-today { font-size: 0.78rem; color: var(--text-muted); display: flex; align-items: center; gap: 6px; }
</style>