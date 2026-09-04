<template>
  <div class="panel">
    <div class="panel-input-area">
      <p v-if="!workId" class="hint">💡 先在顶部「保存」一次作品（生成 work_id），即可为这本书立项。</p>
      <template v-else>
        <label class="field-label">一句话命题 Logline</label>
        <textarea v-model="logline" rows="2" placeholder="例：一个少年为解开祖屋「灯的秘密」踏上旅程，最终发现光来自每一个被遗忘的人。"></textarea>

        <label class="field-label">目标读者画像</label>
        <input v-model="audience" placeholder="例：喜欢悬疑与家庭温情的中青年读者" />

        <div class="row">
          <div class="col">
            <label class="field-label">目标字数</label>
            <input v-model.number="targetWords" type="number" min="0" placeholder="80000" />
          </div>
          <div class="col">
            <label class="field-label">交稿日</label>
            <input v-model="deadline" type="date" />
          </div>
        </div>

        <button class="btn btn-primary btn-full" @click="save" :disabled="saving">{{ saving ? '保存中…' : '保存立项蓝图' }}</button>
        <p class="hint small">之后到「三级大纲 / 设定库 / 角色设定」把骨架补全，大纲越具体，写作阶段 AI 越懂你想写什么。</p>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { api } from '../../api/index.js'
import { useWritingStore } from '../../stores/writing.js'
import { useToast } from '../../composables/useToast.js'

const writingStore = useWritingStore()
const toast = useToast()

const workId = computed(() => writingStore.currentWorkId)
const logline = ref('')
const audience = ref('')
const targetWords = ref(0)
const deadline = ref('')
const saving = ref(false)

async function load() {
  if (!workId.value) return
  const res = await api.get(`/api/plan/${workId.value}`)
  if (res.code !== 0) return
  const plan = res.data.plan
  if (plan) {
    logline.value = plan.logline || ''
    audience.value = plan.audience || ''
    targetWords.value = plan.target_words || 0
    deadline.value = (plan.deadline || '').slice(0, 10)
  }
}

async function save() {
  if (!workId.value) return
  const text = logline.value.trim()
  if (!text) { toast.info('先写一句话命题 Logline'); return }
  saving.value = true
  const res = await api.put(`/api/plan/${workId.value}`, {
    logline: text,
    audience: audience.value.trim(),
    target_words: targetWords.value || 0,
    deadline: deadline.value || null,
  })
  saving.value = false
  if (res.code === 0) toast.success('立项蓝图已保存')
  else toast.error(res.msg)
}

onMounted(load)
watch(workId, (v) => { if (v) load() })
</script>

<style scoped>
@import '../../assets/styles/panel-shared.css';

.hint { font-size: 0.8rem; color: var(--text-muted); line-height: 1.8; }
.hint.small { margin-top: 10px; }
.field-label { display: block; font-size: 0.78rem; color: var(--text-muted); margin: 8px 0 4px; }
.panel-input-area input, .panel-input-area textarea {
  width: 100%; box-sizing: border-box; padding: 8px 10px; font-size: 0.85rem;
  border-radius: var(--radius-sm); background: var(--bg-glass);
  border: 1px solid var(--border-glass); color: var(--text-primary);
}
.row { display: flex; gap: 10px; margin-top: 6px; }
.col { flex: 1; }
</style>
