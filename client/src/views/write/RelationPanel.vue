<template>
  <div class="panel rel-panel">
    <p class="hint" v-if="!workId">保存作品后，这里可手动维护角色关系图（谁 与 谁 是什么关系），3D 蛛网自动生成。</p>

    <template v-else>
      <!-- 操作栏：添加 / 关系边列表折叠 -->
      <div class="rel-actions">
        <button class="rl-btn" :class="{ active: formOpen }" @click="formOpen = !formOpen">
          {{ formOpen ? '收起添加' : '+ 添加关系' }}
        </button>
        <button class="rl-btn" :class="{ active: listOpen }" @click="listOpen = !listOpen; formOpen = false">
          关系边（{{ items.length }}）
        </button>
      </div>

      <!-- 手填关系 -->
      <div v-if="formOpen" class="rel-form">
        <div class="rel-row">
          <input class="f-input" v-model.trim="form.source" maxlength="30" placeholder="角色 A" />
          <span class="rel-arrow">→</span>
          <input class="f-input f-rel" v-model.trim="form.relation" maxlength="30" placeholder="关系（师傅/仇人/恋人…）" />
          <span class="rel-arrow">→</span>
          <input class="f-input" v-model.trim="form.target" maxlength="30" placeholder="角色 B" />
        </div>
        <button class="btn btn-primary btn-full" @click="addRel" :disabled="adding">添加关系边</button>
      </div>

      <!-- 3D 蛛网 -->
      <div class="rel-graph-wrap" :class="{ 'has-relations': items.length }">
        <RelationGraph3D
          v-if="items.length"
          :relations="items"
          :characters="cards"
          @select-node="onSelectNode"
        />
        <div v-else class="rg-empty">
          <p>还没有关系边<br /><span>点「+ 添加关系」填一条：A → 关系 → B，蛛网会自动长出来</span></p>
        </div>
        <p class="rg-tip" v-if="items.length">按住拖动旋转 · 滚轮缩放 · 点角色查看细节</p>
      </div>

      <!-- 节点详情（点击蛛网角色弹出） -->
      <transition name="fade-up">
        <div v-if="selected" class="rel-detail">
          <div class="rel-detail-head">
            <span class="rel-detail-name">{{ selected.name }}</span>
            <div class="rel-detail-head-actions">
              <button v-if="!editing" class="rl-edit-btn" @click="startEdit" :title="selectedCard ? '修改这张角色卡' : '为这个角色创建角色卡'">
                {{ selectedCard ? '编辑角色卡' : '创建角色卡' }}
              </button>
              <button class="rel-detail-close" @click="closeDetail" title="关闭">✕</button>
            </div>
          </div>

          <!-- 阅读态：展示角色卡 -->
          <template v-if="!editing">
            <div v-if="selectedCard" class="rel-card">
              <p v-if="selectedCard.description" class="rc-line"><span class="rc-k">简介</span>{{ selectedCard.description }}</p>
              <p v-if="selectedCard.personality" class="rc-line"><span class="rc-k">性格</span>{{ selectedCard.personality }}</p>
              <p v-if="selectedCard.background" class="rc-line"><span class="rc-k">背景</span>{{ selectedCard.background }}</p>
              <p v-if="selectedCard.speaking_style" class="rc-line"><span class="rc-k">说话风格</span>{{ selectedCard.speaking_style }}</p>
              <p v-if="!hasCardFields(selectedCard)" class="rc-none">这张角色卡还没有写细节——点「编辑角色卡」补充吧。</p>
            </div>
            <p v-else class="rc-none">这个角色还没有角色卡。点「创建角色卡」生成一张，或去「角色设定」AI 生成。</p>

            <div class="rel-detail-rel" v-if="selected.relations.length">
              <p class="rdr-title">涉及的关系</p>
              <div v-for="(r, i) in selected.relations" :key="i" class="rdr-item">
                {{ r.source }} <span class="rdr-rel">{{ r.relation }}</span> {{ r.target }}
              </div>
            </div>
          </template>

          <!-- 编辑态：角色卡表单（与角色设定面板同构，保存后双向同步） -->
          <template v-else>
            <label class="f-label">名字</label>
            <input class="f-input" v-model.trim="editForm.name" maxlength="12" />
            <label class="f-label">形象（一句话）</label>
            <textarea class="f-input f-area" v-model.trim="editForm.description" maxlength="150" rows="2"></textarea>
            <label class="f-label">性格</label>
            <textarea class="f-input f-area" v-model.trim="editForm.personality" maxlength="150" rows="2"></textarea>
            <label class="f-label">背景</label>
            <textarea class="f-input f-area" v-model.trim="editForm.background" maxlength="150" rows="2"></textarea>
            <label class="f-label">说话风格/口头禅</label>
            <input class="f-input" v-model.trim="editForm.speaking_style" maxlength="150" />
            <div class="rc-edit-actions">
              <button class="rc-btn rc-primary" @click="saveEdit" :disabled="savingEdit">保存角色卡</button>
              <button class="rc-btn" @click="editing = false">取消</button>
            </div>
          </template>
        </div>
      </transition>

      <!-- 关系边列表管理 -->
      <div v-if="listOpen && items.length" class="rel-list">
        <div v-for="it in items" :key="it.relation_id" class="rel-item">
          <span class="rel-source">{{ it.source }}</span>
          <span class="rel-type">{{ it.relation }}</span>
          <span class="rel-target">{{ it.target }}</span>
          <button class="rel-del" title="删除这条关系" @click="removeRel(it)">×</button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, defineAsyncComponent } from 'vue'
import { api } from '../../api/index.js'
import { useWritingStore } from '../../stores/writing.js'
import { useToast } from '../../composables/useToast.js'

// 异步加载 three.js 场景（仅打开关系图面板时拉取，避免全站都得下载 3D 引擎）
const RelationGraph3D = defineAsyncComponent(() => import('./RelationGraph3D.vue'))

const props = defineProps({ tabKey: { type: String, default: '' } })

const writingStore = useWritingStore()
const toast = useToast()
const workId = ref(writingStore.currentWorkId)

const items = ref([])
const cards = ref([])
const adding = ref(false)
const formOpen = ref(false)
const listOpen = ref(false)
const selected = ref(null)
const selectedCard = ref(null)
const editing = ref(false)
const savingEdit = ref(false)
const editForm = ref({ name: '', description: '', personality: '', background: '', speaking_style: '' })
const form = ref({ source: '', relation: '', target: '' })

watch(() => writingStore.currentWorkId, (v) => {
  workId.value = v
  if (v) load()
  else { items.value = []; cards.value = []; selected.value = null }
})

async function load() {
  if (!workId.value) return
  const [rel, ch] = await Promise.all([
    api.get(`/api/relations/${workId.value}`),
    api.get(`/api/rp/${workId.value}/characters`),
  ])
  if (rel.code === 0) items.value = rel.data.items || []
  if (ch.code === 0) {
    cards.value = ch.data.characters || []
    refreshSelectedCard()
  }
}

/** 重新匹配当前选中角色对应的角色卡（编辑保存/外部变更后调用） */
function refreshSelectedCard() {
  if (selected.value) {
    selectedCard.value = cards.value.find(c => c.name === selected.value.name) || null
  }
}

function onSelectNode({ name, relations }) {
  selected.value = { name, relations }
  editing.value = false
  selectedCard.value = cards.value.find(c => c.name === name) || null
}

function startEdit() {
  const c = selectedCard.value || {}
  editForm.value = {
    name: c.name ?? selected.value.name,
    description: c.description || '',
    personality: c.personality || '',
    background: c.background || '',
    speaking_style: c.speaking_style || '',
  }
  editing.value = true
}

async function saveEdit() {
  if (!editForm.value.name.trim()) { toast.info('名字不能为空'); return }
  if (savingEdit.value) return
  savingEdit.value = true
  let res
  if (selectedCard.value && selectedCard.value.char_id) {
    res = await api.put(`/api/rp/characters/${selectedCard.value.char_id}`, editForm.value)
  } else {
    res = await api.post(`/api/rp/${workId.value}/characters`, editForm.value)
  }
  savingEdit.value = false
  if (res.code === 0) {
    toast.success('角色卡已保存')
    editing.value = false
    await load()          // 重拉关系 + 角色卡
    broadcastChanged()    // 同步到「角色设定」面板
  } else toast.error(res.msg)
}

function closeDetail() {
  selected.value = null
  selectedCard.value = null
  editing.value = false
}

function hasCardFields(c) {
  return c && (c.description || c.personality || c.background || c.speaking_style)
}

/** 角色卡变更广播：告知角色设定面板刷新 */
function broadcastChanged() {
  window.dispatchEvent(new CustomEvent('inkstone:rp-characters-changed'))
}

async function addRel() {
  const { source, relation, target } = form.value
  if (!source || !relation || !target) { toast.info('需要填 角色 A、关系、角色 B'); return }
  if (adding.value) return
  adding.value = true
  const res = await api.post(`/api/relations/${workId.value}`, { source, relation, target })
  adding.value = false
  if (res.code === 0) {
    form.value = { source: '', relation: '', target: '' }
    toast.success('已添加')
    await load()
  } else toast.error(res.msg)
}

async function removeRel(it) {
  const res = await api.delete(`/api/relations/${workId.value}/${it.relation_id}`)
  if (res.code === 0) { toast.success('已删除'); await load() }
  else toast.error(res.msg)
}

function onTrigger(e) { if (e.detail?.tab === props.tabKey) load() }
function onCardsChanged() { load() }
onMounted(() => {
  window.addEventListener('inkstone:trigger-ai', onTrigger)
  window.addEventListener('inkstone:rp-characters-changed', onCardsChanged)
  if (workId.value) load()
})
onUnmounted(() => {
  window.removeEventListener('inkstone:trigger-ai', onTrigger)
  window.removeEventListener('inkstone:rp-characters-changed', onCardsChanged)
})
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';

.hint { font-size: 0.8rem; color: var(--text-muted); line-height: 1.8; }

.rel-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.rl-btn {
  padding: 4px 12px; font-size: 0.74rem; font-weight: 600;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(196, 163, 90, 0.2);
  border-radius: 20px; cursor: pointer;
  transition: all 0.2s;
}
.rl-btn:hover { color: var(--accent-primary); border-color: var(--accent-primary); }
.rl-btn.active { color: var(--accent-primary); background: rgba(196, 163, 90, 0.1); border-color: var(--accent-primary); }

.rel-form { margin-top: 10px; }
.rel-row { display: flex; align-items: center; gap: 4px; margin-bottom: 6px; }
.f-input {
  flex: 1; min-width: 0; box-sizing: border-box;
  font-size: 0.8rem; color: var(--text-primary);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(196, 163, 90, 0.08);
  border-radius: var(--radius-md);
  padding: 5px 8px; outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.f-input:focus { border-color: rgba(196, 163, 90, 0.3); box-shadow: 0 0 0 3px rgba(196, 163, 90, 0.04); }
.rel-arrow { color: var(--accent-primary); font-size: 0.8rem; flex-shrink: 0; }
.f-rel { flex: 1.4; }

/* 3D 蛛网容器 */
.rel-graph-wrap {
  position: relative;
  border: 1px solid rgba(196, 163, 90, 0.12);
  border-radius: var(--radius-lg);
  background:
    radial-gradient(ellipse at 50% 40%, rgba(196, 163, 90, 0.07), transparent 65%),
    rgba(255, 255, 255, 0.015);
  overflow: hidden;
  margin-top: 10px;
}
.rel-graph-wrap.has-relations { height: 430px; }
.rg-empty {
  height: 430px; display: flex; align-items: center; justify-content: center;
  text-align: center;
}
.rg-empty p { color: var(--text-muted); font-size: 0.82rem; line-height: 2.2; }
.rg-empty span { font-size: 0.74rem; opacity: 0.8; }
.rg-tip {
  position: absolute; left: 0; right: 0; bottom: 6px;
  text-align: center; font-size: 0.66rem; color: var(--text-muted);
  opacity: 0.65; pointer-events: none;
  letter-spacing: 0.06em;
}

/* 节点详情卡 */
.rel-detail {
  margin-top: 10px;
  border: 1px solid rgba(196, 163, 90, 0.22);
  border-radius: var(--radius-lg);
  background: rgba(196, 163, 90, 0.04);
  padding: 12px 14px;
}
.rel-detail-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.rel-detail-head-actions { display: flex; align-items: center; gap: 8px; }
.rel-detail-name { font-family: var(--font-serif); font-size: 1.05rem; font-weight: 700; color: var(--accent-primary); }
.rl-edit-btn {
  font-size: 0.72rem; font-weight: 600;
  padding: 3px 12px; border-radius: 20px;
  color: var(--accent-primary);
  background: rgba(196, 163, 90, 0.1);
  border: 1px solid rgba(196, 163, 90, 0.35);
  cursor: pointer; transition: all 0.2s;
}
.rl-edit-btn:hover { background: rgba(196, 163, 90, 0.2); border-color: var(--accent-primary); }
.rel-detail-close {
  width: 22px; height: 22px; border-radius: 50%; border: none; cursor: pointer;
  background: rgba(255, 255, 255, 0.05); color: var(--text-muted); font-size: 0.75rem;
  transition: all 0.2s;
}
.rel-detail-close:hover { color: #fff; background: rgba(224, 85, 106, 0.5); }
.rc-line { margin: 0 0 7px; font-size: 0.8rem; line-height: 1.75; color: var(--text-secondary); }
.rc-k {
  display: inline-block; min-width: 3.2em; margin-right: 6px;
  font-size: 0.7rem; font-weight: 600; color: var(--accent-primary);
  letter-spacing: 0.05em;
}
.rc-none { font-size: 0.78rem; color: var(--text-muted); line-height: 1.8; margin: 0; }
.rel-detail-rel { margin-top: 10px; padding-top: 8px; border-top: 1px dashed rgba(196, 163, 90, 0.2); }
.rdr-title { font-size: 0.7rem; font-weight: 600; letter-spacing: 0.08em; color: var(--text-muted); margin: 0 0 6px; }
.rdr-item { font-size: 0.76rem; color: var(--text-secondary); line-height: 1.9; }
.rdr-rel { color: var(--accent-primary); margin: 0 4px; }

/* 关系边列表（管理） */
.rel-list { display: flex; flex-direction: column; gap: 6px; margin-top: 10px; }
.rel-item {
  display: flex; align-items: center; gap: 8px;
  padding: 7px 10px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(196, 163, 90, 0.12);
  border-radius: 8px;
  font-size: 0.8rem;
}
.rel-source { color: var(--accent-primary); font-weight: 600; white-space: nowrap; }
.rel-type {
  color: var(--text-muted); font-size: 0.74rem;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  flex: 1;
}
.rel-target { color: var(--text-primary); font-weight: 600; white-space: nowrap; }
.rel-del {
  width: 20px; height: 20px; flex-shrink: 0;
  border-radius: 50%;
  border: none; cursor: pointer;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.05);
  font-size: 0.85rem; line-height: 1;
  transition: all 0.2s;
}
.rel-del:hover { color: var(--accent-red); background: rgba(224, 85, 106, 0.12); }

.fade-up-enter-active, .fade-up-leave-active { transition: all 0.25s ease; }
.fade-up-enter-from, .fade-up-leave-to { opacity: 0; transform: translateY(8px); }

/* 编辑角色卡表单（与角色设定面板同构） */
.f-label { display: block; font-size: 0.7rem; color: var(--text-muted); margin: 6px 0 2px; }
.f-area { resize: vertical; font-family: inherit; line-height: 1.5; }
.rc-edit-actions { display: flex; gap: 8px; margin-top: 8px; }
.rc-btn {
  font-size: 0.7rem; padding: 3px 12px;
  border-radius: 20px;
  border: 1px solid rgba(196, 163, 90, 0.25);
  background: none; color: var(--text-muted);
  cursor: pointer; transition: all 0.2s;
}
.rc-btn:hover { color: var(--accent-primary); border-color: var(--accent-primary); }
.rc-btn.rc-primary { color: var(--accent-green); border-color: rgba(107, 207, 127, 0.4); background: rgba(107, 207, 127, 0.06); }
</style>