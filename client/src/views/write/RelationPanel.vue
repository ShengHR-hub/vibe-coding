<template>
  <div class="panel">
    <p class="hint" v-if="!workId">保存作品后，这里可手动维护角色关系图（谁 与 谁 是什么关系）。</p>

    <template v-else>
      <!-- 手填关系 -->
      <div class="rel-form">
        <div class="rel-row">
          <input class="f-input" v-model.trim="form.source" maxlength="30" placeholder="角色 A" />
          <span class="rel-arrow">→</span>
          <input class="f-input f-rel" v-model.trim="form.relation" maxlength="30" placeholder="关系（师傅/仇人/恋人…）" />
          <span class="rel-arrow">→</span>
          <input class="f-input" v-model.trim="form.target" maxlength="30" placeholder="角色 B" />
        </div>
        <button class="btn btn-primary btn-full" @click="addRel" :disabled="adding">添加关系边</button>
      </div>

      <!-- 关系列表 -->
      <div class="rel-list" v-if="items.length">
        <div v-for="it in items" :key="it.relation_id" class="rel-item">
          <span class="rel-source">{{ it.source }}</span>
          <span class="rel-type">{{ it.relation }}</span>
          <span class="rel-target">{{ it.target }}</span>
          <button class="rel-del" title="删除这条关系" @click="removeRel(it)">×</button>
        </div>
      </div>
      <p v-else class="list-empty">还没有关系——填好上面三个框点「添加关系边」。</p>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { api } from '../../api/index.js'
import { useWritingStore } from '../../stores/writing.js'
import { useToast } from '../../composables/useToast.js'

const props = defineProps({ tabKey: { type: String, default: '' } })

const writingStore = useWritingStore()
const toast = useToast()
const workId = ref(writingStore.currentWorkId)

const items = ref([])
const adding = ref(false)
const form = ref({ source: '', relation: '', target: '' })

watch(() => writingStore.currentWorkId, (v) => {
  workId.value = v
  if (v) load()
  else items.value = []
})

async function load() {
  if (!workId.value) return
  const res = await api.get(`/api/relations/${workId.value}`)
  if (res.code === 0) items.value = res.data.items || []
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
onMounted(() => {
  window.addEventListener('inkstone:trigger-ai', onTrigger)
  if (workId.value) load()
})
onUnmounted(() => window.removeEventListener('inkstone:trigger-ai', onTrigger))
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';

.hint { font-size: 0.8rem; color: var(--text-muted); line-height: 1.8; }

.rel-form { margin-bottom: 10px; }
.rel-row { display: flex; align-items: center; gap: 4px; margin-bottom: 6px; }
.f-input {
  flex: 1; min-width: 0; box-sizing: border-box;
  font-size: 0.8rem; color: var(--text-primary);
  background: rgba(0, 0, 0, 0.18);
  border: 1px solid rgba(196, 163, 90, 0.16);
  border-radius: 6px;
  padding: 5px 8px; outline: none;
}
.f-input:focus { border-color: rgba(196, 163, 90, 0.4); }
.rel-arrow { color: var(--accent-primary); font-size: 0.8rem; flex-shrink: 0; }
.f-rel { flex: 1.4; }

.rel-list { display: flex; flex-direction: column; gap: 6px; }
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
.rel-del:hover { color: #e0716b; background: rgba(224, 113, 107, 0.12); }
.list-empty { font-size: 0.78rem; color: var(--text-muted); line-height: 1.7; }
</style>