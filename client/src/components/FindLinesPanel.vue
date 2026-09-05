<template>
  <div class="fl-panel">
    <!-- 搜索区：一句话描述想写什么 -->
    <div class="fl-search">
      <input
        v-model="intent"
        class="fl-input"
        placeholder="想描写什么？比如：夕阳下离别的惆怅、深夜一个人的孤独…"
        maxlength="200"
        @keydown.enter="search"
      />
      <button class="fl-btn" @click="search" :disabled="loading || !intent.trim()">
        {{ loading ? '寻找中…' : '找句 ✦' }}
      </button>
    </div>
    <p class="fl-hint">支持按意境/意思找句：本地诗词素材库匹配 + AI 原创佳句，找到后可一键引用到创作。</p>

    <template v-if="loading">
      <div class="fl-loading">AI 正在品读你的意境…</div>
    </template>

    <template v-else-if="error">
      <div class="fl-error">{{ error }}</div>
    </template>

    <template v-else-if="results">
      <!-- 本地库命中 -->
      <section class="fl-section" v-if="results.local.length">
        <h4 class="fl-section-title">𝔖 本地库 · 最贴近意境的句子</h4>
        <div
          v-for="(it, i) in results.local"
          :key="'L' + i"
          class="fl-card"
          :class="{ picked: isPicked(it.content) }"
        >
          <p class="fl-card-content">{{ it.content }}</p>
          <p class="fl-card-reason" v-if="it.reason">✦ {{ it.reason }}</p>
          <div class="fl-card-meta">
            <span class="fl-card-source">
              <template v-if="it.kind === 'poem'">《{{ it.title }}》{{ it.author }}</template>
              <template v-else>{{ it.category || '素材' }}</template>
            </span>
            <div class="fl-card-actions">
              <button class="fl-mini" @click="fav(it)" :class="{ starred: isFav(it) }">
                {{ isFav(it) ? '♥' : '♡' }}
              </button>
              <button class="fl-mini" @click="pickRef(it.content, it.kind === 'poem' ? '诗词' : (it.category || '素材'))">
                {{ isPicked(it.content) ? '✓ 已引用' : '＋ 引用' }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- AI 原创 -->
      <section class="fl-section" v-if="results.created.length">
        <h4 class="fl-section-title">✎ AI 原创 · 替你先写几句</h4>
        <div
          v-for="(c, i) in results.created"
          :key="'C' + i"
          class="fl-card"
          :class="{ picked: isPicked(c) }"
        >
          <p class="fl-card-content">{{ c }}</p>
          <div class="fl-card-meta">
            <span class="fl-card-source">AI 创作</span>
            <div class="fl-card-actions">
              <button class="fl-mini" @click="pickRef(c, 'AI佳句')">
                {{ isPicked(c) ? '✓ 已引用' : '＋ 引用' }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <p class="fl-empty" v-if="!results.local.length && !results.created.length">
        没有找到合适的句子，换个说法试试？比如加上具体意象（秋雨/灯火/小巷…）。
      </p>

      <!-- 兜底：直达外部诗词网站 -->
      <section class="fl-section fl-external">
        <h4 class="fl-section-title">↗ 还想要更多？去这些老牌诗词库搜</h4>
        <div class="fl-external-links">
          <a href="https://www.gushiwen.cn/" target="_blank" rel="noopener">古诗文网 →</a>
          <a href="https://so.gushiwen.cn/" target="_blank" rel="noopener">古诗文网·搜索 →</a>
          <a href="https://www.shicimingju.com/" target="_blank" rel="noopener">诗词名句网 →</a>
          <a href="https://www.zhonghuadiancang.com/" target="_blank" rel="noopener">中华典藏 →</a>
        </div>
        <p class="fl-external-tip">从外站复制到的句子，可在灵感馆「收录句子」加入本地库，之后就能被意境搜索命中。</p>
      </section>
    </template>

    <!-- 初始态：示例意境 -->
    <template v-else>
      <div class="fl-examples">
        <span class="fl-example-label">不知道怎么写？点一个试试：</span>
        <button v-for="e in EXAMPLES" :key="e" class="fl-example-chip" @click="intent = e; search()">{{ e }}</button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '../api/index.js'
import { useWritingStore } from '../stores/writing.js'

const props = defineProps({
  initialIntent: { type: String, default: '' },
  autofocus: { type: Boolean, default: true },
})
defineEmits(['close'])

const writingStore = useWritingStore()

const intent = ref(props.initialIntent || '')
const loading = ref(false)
const error = ref('')
const results = ref(null)
const favSet = ref(new Set())

const EXAMPLES = [
  '夕阳下离别的惆怅',
  '深夜一个人的孤独',
  '春天田野的生机',
  '久别重逢的欣喜',
  '岁月流逝的感慨',
]

function isPicked(content) {
  return writingStore.pickedRefs.some(r => r.content === content)
}

function pickRef(content, type) {
  writingStore.pickRef({ type, content })
}

function favKey(it) {
  return (it.kind || 'poem') + ':' + it.id
}
function isFav(it) {
  return !!it.id && favSet.value.has(favKey(it))
}
function fav(it) {
  if (!it.id) return
  const kind = it.kind === 'poem' ? 'poem' : 'material'
  const key = favKey(it)
  const faved = favSet.value.has(key)
  const req = faved
    ? api.delete(`/api/inspire/favorites/${kind}/${it.id}`)
    : api.post('/api/inspire/favorites', { item_type: kind, ref_id: it.id })
  req.then(res => {
    if (res.code === 0) {
      const next = new Set(favSet.value)
      if (faved) next.delete(key); else next.add(key)
      favSet.value = next
    }
  })
}

async function loadFavs() {
  const res = await api.get('/api/inspire/favorites')
  if (res.code === 0) {
    favSet.value = new Set((res.data.items || []).map(f => f.item_type + ':' + f.ref_id))
  }
}

async function search() {
  const q = intent.value.trim()
  if (!q || loading.value) return
  loading.value = true
  error.value = ''
  results.value = null
  const res = await api.post('/api/write/find-lines', { intent: q })
  loading.value = false
  if (res.code === 0) {
    results.value = res.data
  } else {
    error.value = res.msg || '找句失败，请稍后再试'
  }
}

loadFavs()
</script>

<style scoped>
.fl-panel { display: flex; flex-direction: column; gap: 1rem; }

.fl-search { display: flex; gap: 8px; }
.fl-input {
  flex: 1; min-width: 0; padding: 10px 14px; font-size: 0.92rem;
  border-radius: var(--radius-md); background: var(--bg-glass);
  border: 1px solid var(--border-glass); color: var(--text-primary);
}
.fl-input:focus { border-color: var(--accent-primary); outline: none; }
.fl-btn {
  padding: 10px 18px; font-size: 0.9rem; border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  color: #1a1a2e; font-weight: 600; border: none; cursor: pointer; white-space: nowrap;
}
.fl-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.fl-hint { font-size: 0.78rem; color: var(--text-muted); margin: 0; }

.fl-loading { text-align: center; color: var(--accent-primary); padding: 1.5rem 0; font-size: 0.9rem; }
.fl-error { text-align: center; color: var(--accent-red); padding: 1rem 0; font-size: 0.88rem; }

.fl-section { display: flex; flex-direction: column; gap: 0.7rem; }
.fl-section-title {
  font-family: var(--font-serif); font-size: 0.9rem; color: var(--accent-secondary);
  margin: 0.4rem 0 0; letter-spacing: 0.05em;
}
.fl-card {
  padding: 0.9rem 1rem; border-radius: var(--radius-md);
  background: var(--bg-glass); border: 1px solid var(--border-glass);
  display: flex; flex-direction: column; gap: 0.45rem; transition: border-color 0.2s;
}
.fl-card:hover { border-color: rgba(196, 163, 90, 0.35); }
.fl-card.picked { border-color: var(--accent-primary); }
.fl-card-content {
  font-family: var(--font-serif); font-size: 0.95rem; line-height: 1.8;
  color: var(--text-primary); margin: 0; white-space: pre-wrap; word-break: break-word;
}
.fl-card-reason { font-size: 0.76rem; color: var(--accent-primary); margin: 0; }
.fl-card-meta { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
.fl-card-source { font-size: 0.72rem; color: var(--text-muted); }
.fl-card-actions { display: flex; gap: 6px; }
.fl-mini {
  font-size: 0.72rem; padding: 3px 10px; border-radius: var(--radius-sm);
  background: rgba(196, 163, 90, 0.08); border: 1px solid rgba(196, 163, 90, 0.2);
  color: var(--accent-primary); cursor: pointer;
}
.fl-mini:hover { background: rgba(196, 163, 90, 0.18); }
.fl-mini.starred { color: #e0716b; border-color: rgba(224, 113, 107, 0.4); background: rgba(224, 113, 107, 0.08); }

.fl-empty { text-align: center; color: var(--text-muted); font-size: 0.86rem; padding: 1rem 0; }

.fl-external { border-top: 1px dashed var(--border-glass); padding-top: 0.8rem; }
.fl-external-links { display: flex; flex-wrap: wrap; gap: 10px; }
.fl-external-links a {
  font-size: 0.8rem; color: var(--accent-cool); text-decoration: none;
  padding: 4px 12px; border-radius: var(--radius-full);
  background: rgba(126, 200, 227, 0.08); border: 1px solid rgba(126, 200, 227, 0.2);
}
.fl-external-links a:hover { background: rgba(126, 200, 227, 0.18); }
.fl-external-tip { font-size: 0.74rem; color: var(--text-muted); margin: 0.4rem 0 0; }

.fl-examples { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.fl-example-label { font-size: 0.8rem; color: var(--text-muted); }
.fl-example-chip {
  font-size: 0.78rem; padding: 5px 14px; border-radius: var(--radius-full);
  background: var(--bg-glass); border: 1px solid var(--border-glass);
  color: var(--text-secondary); cursor: pointer; transition: all 0.2s;
}
.fl-example-chip:hover { border-color: var(--accent-primary); color: var(--accent-primary); }
</style>