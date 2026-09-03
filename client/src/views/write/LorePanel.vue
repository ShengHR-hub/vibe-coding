<template>
  <div class="panel">
    <div class="panel-input-area">
      <p v-if="!workId" class="lore-hint">
        💡 保存一次作品后，即可为作品添加"设定记忆"（世界观/能力/规则…），
        续写时 AI 会自动参考这些设定保持连贯。
      </p>
      <template v-else>
        <input
          v-model="formTitle"
          class="lore-title-input"
          placeholder="设定标题（如：世界观 / 主角能力 / 禁忌规则）"
          maxlength="100"
          @keydown.enter="addLore"
        />
        <textarea
          v-model="formContent"
          rows="3"
          class="lore-content-input"
          placeholder="设定内容描述…"
        ></textarea>
        <button class="btn btn-primary btn-full" @click="addLore" :disabled="saving">
          {{ saving ? '保存中…' : '＋ 保存设定' }}
        </button>
      </template>
    </div>

    <div class="lore-list" v-if="workId">
      <div class="empty-state" v-if="!loading && items.length === 0">
        <span class="empty-icon">&#10045;</span>
        <p class="empty-hint">还没有设定条目，先记下第一条吧</p>
      </div>
      <div v-for="l in items" :key="l.lore_id" class="lore-item">
        <div class="lore-head">
          <span class="lore-title">{{ l.title }}</span>
          <button class="card-btn" @click="removeLore(l)">删除</button>
        </div>
        <p class="lore-content">{{ l.content }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { api } from '../../api/index.js'
import { useWritingStore } from '../../stores/writing.js'
import { useToast } from '../../composables/useToast.js'

defineProps({ tabKey: { type: String, default: '' } })

const writingStore = useWritingStore()
const toast = useToast()

const workId = computed(() => writingStore.currentWorkId)
const items = ref([])
const loading = ref(false)
const saving = ref(false)
const formTitle = ref('')
const formContent = ref('')

async function load() {
  if (!workId.value) return
  loading.value = true
  const res = await api.get(`/api/works/${workId.value}/lore`)
  if (res.code === 0) items.value = res.data.items || []
  loading.value = false
}

async function addLore() {
  if (!workId.value) return
  const title = formTitle.value.trim()
  const content = formContent.value.trim()
  if (!title) { toast.info('请输入设定标题'); return }
  if (!content) { toast.info('请输入设定内容'); return }
  saving.value = true
  const res = await api.post(`/api/works/${workId.value}/lore`, { title, content })
  saving.value = false
  if (res.code === 0) {
    toast.success('设定已保存')
    formTitle.value = ''
    formContent.value = ''
    await load()
  } else {
    toast.error(res.msg)
  }
}

async function removeLore(l) {
  if (!window.confirm(`删除设定「${l.title}」？`)) return
  const res = await api.delete(`/api/works/${workId.value}/lore/${l.lore_id}`)
  if (res.code === 0) {
    toast.success('已删除')
    await load()
  } else {
    toast.error(res.msg)
  }
}

onMounted(load)
watch(workId, (v) => { if (v) load() })
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';

.lore-hint {
  color: var(--text-muted);
  font-size: 0.85rem;
  line-height: 1.8;
  padding: var(--space-sm) 0;
}
.lore-title-input,
.lore-content-input {
  width: 100%;
  box-sizing: border-box;
  padding: 8px 12px;
  font-size: 0.85rem;
  margin-bottom: var(--space-sm);
  border-radius: var(--radius-sm);
  background: var(--bg-glass);
  border: 1px solid var(--border-glass);
  color: var(--text-primary);
}
.lore-list { display: flex; flex-direction: column; gap: var(--space-sm); margin-top: var(--space-sm); }
.lore-item {
  padding: var(--space-md);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(196, 163, 90, 0.06);
}
.lore-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.lore-title { font-family: var(--font-serif); font-size: 0.95rem; font-weight: 600; color: var(--accent-primary); }
.lore-content { font-size: 0.85rem; line-height: 1.8; color: var(--text-secondary); margin: 0; }
.empty-state { text-align: center; padding: var(--space-xl) 0; }
.empty-icon { font-size: 1.6rem; display: block; margin-bottom: var(--space-sm); }
.empty-hint { color: var(--text-muted); font-size: 0.85rem; }
.card-btn {
  font-size: 0.75rem; padding: 3px 10px;
  border-radius: var(--radius-sm);
  background: rgba(196, 163, 90, 0.08);
  border: 1px solid rgba(196, 163, 90, 0.15);
  color: var(--accent-primary);
  cursor: pointer;
}
.card-btn:hover { background: rgba(196, 163, 90, 0.15); }
</style>
