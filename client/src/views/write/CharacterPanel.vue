<template>
  <div class="panel">
    <!-- 未选作品提示 -->
    <p class="hint" v-if="!workId">保存作品后，这里可生成并维护角色卡（AI 按主线生成，可手改）。</p>

    <template v-else>
      <!-- AI 生成区 -->
      <div class="panel-input-area">
        <label class="panel-label">按灵感生成角色卡</label>
        <textarea v-model="inspiration" rows="3" placeholder="粘贴主线或世界观，AI 生成 2-5 张角色卡并保存…" ref="inputRef"></textarea>
        <button class="btn btn-primary btn-full" @click="genCards" :disabled="generating">
          <span v-if="generating" class="loading-dots">AI 正在设计角色<span class="dots"></span></span>
          <span v-else>生成角色卡</span>
        </button>
      </div>

      <!-- 加载骨架屏 -->
      <div class="loading-card" v-if="generating">
        <div class="lc-header"></div>
        <div class="lc-body"><div class="lc-line"></div><div class="lc-line"></div><div class="lc-line"></div></div>
      </div>

      <!-- 角色卡列表 -->
      <div class="card-list" v-if="!generating">
        <p class="list-empty" v-if="cards.length === 0">还没有角色卡——写几句主线让 AI 生成，或手填一张</p>
        <div v-for="card in cards" :key="card.char_id" class="role-card">
          <!-- 阅读态 -->
          <template v-if="editingId !== card.char_id">
            <div class="rc-head">
              <span class="rc-name">{{ card.name }}</span>
              <span class="rc-actions">
                <button class="rc-btn" @click="startEdit(card)">改</button>
                <button class="rc-btn rc-danger" @click="removeCard(card)">删</button>
              </span>
            </div>
            <div class="rc-body">
              <p v-if="card.description"><b>形象</b>{{ card.description }}</p>
              <p v-if="card.personality"><b>性格</b>{{ card.personality }}</p>
              <p v-if="card.background"><b>背景</b>{{ card.background }}</p>
              <p v-if="card.speaking_style"><b>口癖</b>{{ card.speaking_style }}</p>
              <p v-if="!card.description && !card.personality && !card.background && !card.speaking_style" class="rc-empty">（空卡，点「改」补充设定）</p>
            </div>
          </template>

          <!-- 编辑态 -->
          <template v-else>
            <label class="f-label">名字</label>
            <input class="f-input" v-model="editForm.name" maxlength="12" />
            <label class="f-label">形象（一句话）</label>
            <textarea class="f-input f-area" v-model="editForm.description" maxlength="150" rows="2"></textarea>
            <label class="f-label">性格</label>
            <textarea class="f-input f-area" v-model="editForm.personality" maxlength="150" rows="2"></textarea>
            <label class="f-label">背景</label>
            <textarea class="f-input f-area" v-model="editForm.background" maxlength="150" rows="2"></textarea>
            <label class="f-label">说话风格/口头禅</label>
            <input class="f-input" v-model="editForm.speaking_style" maxlength="150" />
            <div class="rc-edit-actions">
              <button class="rc-btn rc-primary" @click="saveEdit" :disabled="savingEdit">保存</button>
              <button class="rc-btn" @click="editingId = null">取消</button>
            </div>
          </template>
        </div>

        <!-- 手填新卡 -->
        <button class="add-card-btn" @click="showAdd = !showAdd">{{ showAdd ? '收起' : '+ 手填一张角色卡' }}</button>
        <div v-if="showAdd" class="role-card add-form">
          <label class="f-label">名字</label>
          <input class="f-input" v-model="addForm.name" maxlength="12" placeholder="角色名" />
          <label class="f-label">形象</label>
          <textarea class="f-input f-area" v-model="addForm.description" maxlength="150" rows="2"></textarea>
          <label class="f-label">性格</label>
          <textarea class="f-input f-area" v-model="addForm.personality" maxlength="150" rows="2"></textarea>
          <label class="f-label">背景</label>
          <textarea class="f-input f-area" v-model="addForm.background" maxlength="150" rows="2"></textarea>
          <label class="f-label">说话风格/口头禅</label>
          <input class="f-input" v-model="addForm.speaking_style" maxlength="150" />
          <div class="rc-edit-actions">
            <button class="rc-btn rc-primary" @click="addCard" :disabled="savingEdit">保存</button>
            <button class="rc-btn" @click="showAdd = false">取消</button>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { api } from '../../api/index.js'
import { useWritingStore } from '../../stores/writing.js'
import { useToast } from '../../composables/useToast.js'

const props = defineProps({ tabKey: { type: String, default: '' } })
defineEmits(['insert'])

const writingStore = useWritingStore()
const toast = useToast()
const workId = ref(writingStore.currentWorkId)

const inspiration = ref('')
const generating = ref(false)
const cards = ref([])
const editingId = ref(null)
const savingEdit = ref(false)
const showAdd = ref(false)
const inputRef = ref(null)

const blank = () => ({ name: '', description: '', personality: '', background: '', speaking_style: '' })
const editForm = ref(blank())
const addForm = ref(blank())

watch(() => writingStore.currentWorkId, (v) => {
  workId.value = v
  if (v) loadCards()
  else cards.value = []
})

async function loadCards() {
  if (!workId.value) return
  const res = await api.get(`/api/rp/${workId.value}/characters`)
  if (res.code === 0) cards.value = res.data.characters || []
}

async function genCards() {
  if (!inspiration.value.trim()) { toast.info('先写几句灵感/主线，AI 才好设计角色'); return }
  if (generating.value) return
  generating.value = true
  const res = await api.post(`/api/rp/${workId.value}/characters/generate`, { inspiration: inspiration.value.trim() })
  generating.value = false
  if (res.code === 0) {
    toast.success(res.msg || '角色卡已生成')
    await loadCards()
    broadcastChanged()
  } else toast.error(res.msg)
}

function startEdit(card) {
  editingId.value = card.char_id
  editForm.value = {
    name: card.name || '',
    description: card.description || '',
    personality: card.personality || '',
    background: card.background || '',
    speaking_style: card.speaking_style || '',
  }
}

async function saveEdit() {
  if (!editForm.value.name.trim()) { toast.info('名字不能为空'); return }
  savingEdit.value = true
  const res = await api.put(`/api/rp/characters/${editingId.value}`, editForm.value)
  savingEdit.value = false
  if (res.code === 0) {
    editingId.value = null
    toast.success('角色卡已更新')
    await loadCards()
    broadcastChanged()
  } else toast.error(res.msg)
}

async function addCard() {
  if (!addForm.value.name.trim()) { toast.info('名字不能为空'); return }
  savingEdit.value = true
  const res = await api.post(`/api/rp/${workId.value}/characters`, addForm.value)
  savingEdit.value = false
  if (res.code === 0) {
    addForm.value = blank()
    showAdd.value = false
    toast.success('角色卡已保存')
    await loadCards()
    broadcastChanged()
  } else toast.error(res.msg)
}

async function removeCard(card) {
  const res = await api.delete(`/api/rp/characters/${card.char_id}`)
  if (res.code === 0) {
    toast.success('已删除')
    await loadCards()
    broadcastChanged()
  } else toast.error(res.msg)
}

function onTrigger(e) { if (e.detail?.tab === props.tabKey) loadCards() }
/** 角色卡变化广播：关系图详情编辑 / 本面板增删改后通知对方刷新 */
function broadcastChanged() {
  window.dispatchEvent(new CustomEvent('inkstone:rp-characters-changed'))
}
function onCardsChanged() {
  loadCards()
}
onMounted(() => {
  window.addEventListener('inkstone:trigger-ai', onTrigger)
  window.addEventListener('inkstone:rp-characters-changed', onCardsChanged)
  if (workId.value) loadCards()
})
onUnmounted(() => {
  window.removeEventListener('inkstone:trigger-ai', onTrigger)
  window.removeEventListener('inkstone:rp-characters-changed', onCardsChanged)
})
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';

.hint { font-size: 0.8rem; color: var(--text-muted); line-height: 1.8; }

/* 角色卡列表 */
.card-list { margin-top: 4px; display: flex; flex-direction: column; gap: 8px; }
.list-empty { font-size: 0.78rem; color: var(--text-muted); line-height: 1.7; padding: 4px 0; }
.role-card {
  border: 1px solid rgba(196, 163, 90, 0.14);
  border-radius: 10px;
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.02);
}
.rc-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.rc-name { font-weight: 700; font-size: 0.9rem; color: var(--text-primary); }
.rc-actions { display: flex; gap: 6px; }
.rc-btn {
  font-size: 0.7rem; padding: 2px 10px;
  border-radius: 20px;
  border: 1px solid rgba(196, 163, 90, 0.25);
  background: none; color: var(--text-muted);
  cursor: pointer; transition: all 0.2s;
}
.rc-btn:hover { color: var(--accent-primary); border-color: var(--accent-primary); }
.rc-btn.rc-primary { color: var(--accent-green); border-color: rgba(107, 207, 127, 0.4); background: rgba(107, 207, 127, 0.06); }
.rc-btn.rc-danger:hover { color: var(--accent-red); border-color: rgba(224, 85, 106, 0.4); }
.rc-body { display: flex; flex-direction: column; gap: 3px; }
.rc-body p { font-size: 0.76rem; color: var(--text-secondary); line-height: 1.6; margin: 0; }
.rc-body b { color: var(--accent-primary); font-weight: 600; margin-right: 6px; }
.rc-empty { color: var(--text-muted); font-style: italic; }

/* 编辑/新增表单 */
.f-label { display: block; font-size: 0.7rem; color: var(--text-muted); margin: 6px 0 2px; }
.f-input {
  width: 100%; box-sizing: border-box;
  font-size: 0.8rem; color: var(--text-primary);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(196, 163, 90, 0.08);
  border-radius: var(--radius-md);
  padding: 5px 8px; outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.f-input:focus { border-color: rgba(196, 163, 90, 0.3); box-shadow: 0 0 0 3px rgba(196, 163, 90, 0.04); }
.f-area { resize: vertical; font-family: inherit; line-height: 1.5; }
.rc-edit-actions { display: flex; gap: 8px; margin-top: 8px; }
.add-card-btn {
  width: 100%; padding: 6px;
  font-size: 0.74rem; color: var(--text-muted);
  background: none; border: 1px dashed rgba(196, 163, 90, 0.2);
  border-radius: 8px; cursor: pointer; transition: all 0.2s;
}
.add-card-btn:hover { color: var(--accent-primary); border-color: rgba(196, 163, 90, 0.4); }
.add-form { border-style: dashed; }
</style>