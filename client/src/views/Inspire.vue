<template>
  <div class="page-container">
    <!-- 顶部：今日灵感 -->
    <section class="inspire-hero glass-card">
      <p class="hero-kicker">INSPIRE · 今日灵感</p>
      <blockquote v-if="hero" class="hero-quote">
        <p>{{ hero.content }}</p>
        <cite v-if="hero.title || hero.author">—— {{ hero.author || '' }}<template v-if="hero.dynasty"> · {{ hero.dynasty }}</template><template v-if="hero.title"> 《{{ hero.title }}》</template></cite>
      </blockquote>
      <div class="hero-actions">
        <button class="btn btn-ghost btn-sm" @click="loadHero" :disabled="heroLoading">{{ heroLoading ? '换一句…' : '换一句' }}</button>
        <button class="btn btn-ghost btn-sm" v-if="hero" @click="pickRef({ type: '诗词', content: hero.content })">
          {{ isPicked(hero.content) ? '✓ 已引用到创作' : '＋ 引用到创作' }}
        </button>
      </div>
    </section>

    <!-- 内容区：诗词 / 句子素材 -->
    <section class="inspire-main">
      <div class="seg-tabs">
        <button v-for="t in segs" :key="t.key" class="seg-tab" :class="{ active: activeTab === t.key }" @click="switchSeg(t.key)">
          {{ t.label }}
        </button>
        <span class="flex-spacer"></span>
        <input class="inspire-search" v-model="query" placeholder="搜索内容 / 作者…" @keydown.enter="doSearch" />
        <button class="btn btn-primary btn-sm" @click="doSearch">搜索</button>
        <button class="btn btn-ghost btn-sm" @click="refresh" :disabled="loading">{{ loading ? '…' : '换一批' }}</button>
      </div>

      <div class="cat-chips" v-if="cats.length">
        <span class="cat-chip" :class="{ active: activeCat === '' }" @click="pickCat('')">全部</span>
        <span v-for="c in cats" :key="c.category" class="cat-chip" :class="{ active: activeCat === c.category }" @click="pickCat(c.category)">
          {{ c.category }}<small> {{ c.count }}</small>
        </span>
      </div>

      <div v-if="loading" class="center muted" style="padding: 3rem 0">灵感加载中…</div>
      <div v-else-if="items.length === 0" class="center muted" style="padding: 3rem 0">暂无内容，换个分类或关键词试试</div>
      <div v-else class="inspire-grid">
        <div v-for="(it, i) in items" :key="activeTab + '-' + (it.poem_id || it.material_id || i)" class="inspire-card glass-card">
          <p class="ic-content" :class="{ poem: activeTab === 'poems' }">{{ it.content }}</p>
          <div class="ic-meta">
            <template v-if="activeTab === 'poems'">
              <span v-if="it.title || it.author" class="ic-source">《{{ it.title }}》{{ it.author }}<template v-if="it.dynasty">〔{{ it.dynasty }}〕</template></span>
            </template>
            <template v-else>
              <span class="ic-source">{{ it.category }}</span>
            </template>
            <div class="ic-actions">
              <button class="ic-btn" @click="pickRef(activeTab === 'poems' ? { type: '诗词', content: it.content } : { type: it.category || '素材', content: it.content })">
                {{ isPicked(it.content) ? '✓ 已引用' : '＋ 引用到创作' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api/index.js'
import { useWritingStore } from '../stores/writing.js'

const writingStore = useWritingStore()

const segs = [
  { key: 'poems', label: '诗词' },
  { key: 'materials', label: '句子素材' },
]
const activeTab = ref('poems')
const items = ref([])
const cats = ref([])
const activeCat = ref('')
const query = ref('')
const loading = ref(false)
const hero = ref(null)
const heroLoading = ref(false)

function isPicked(content) {
  return writingStore.pickedRefs.some(r => r.content === content)
}
function pickRef(item) {
  writingStore.pickRef(item)
}

async function loadHero() {
  heroLoading.value = true
  const res = await api.get('/api/poems/featured?count=1')
  if (res.code === 0 && res.data.poems?.length) hero.value = res.data.poems[0]
  heroLoading.value = false
}

async function loadCats() {
  if (activeTab.value === 'poems') {
    const r = await api.get('/api/poems/categories')
    if (r.code === 0) cats.value = r.data.categories || []
  } else {
    const r = await api.get('/api/materials/categories')
    if (r.code === 0) cats.value = r.data.categories || []
  }
}

async function loadItems() {
  loading.value = true
  const q = query.value.trim()
  const poems = activeTab.value === 'poems'
  let res
  if (q) {
    res = await api.get(`/api/${poems ? 'poems' : 'materials'}/search?q=${encodeURIComponent(q)}&page_size=12`)
  } else if (activeCat.value) {
    res = await api.get(`/api/${poems ? 'poems' : 'materials'}/?category=${encodeURIComponent(activeCat.value)}&page_size=12`)
  } else {
    res = await api.get(`/api/${poems ? 'poems' : 'materials'}/random?count=8`)
  }
  if (res.code === 0) {
    const key = poems ? 'poems' : 'materials'
    items.value = (res.data[key] || []).map(x => ({ ...x }))
  } else {
    items.value = []
  }
  loading.value = false
}

function refresh() { loadItems() }
function pickCat(cat) { activeCat.value = cat; query.value = ''; loadItems() }
function doSearch() { activeCat.value = ''; loadItems() }
function switchSeg(key) {
  if (activeTab.value === key) return
  activeTab.value = key
  activeCat.value = ''
  query.value = ''
  items.value = []
  cats.value = []
  loadCats()
  loadItems()
}

onMounted(async () => {
  await Promise.all([loadHero(), loadCats(), loadItems()])
})
</script>

<style scoped>
.page-container { max-width: 1080px; margin: 0 auto; padding: 1.5rem 1rem 3rem; }

.inspire-hero {
  padding: 2rem 2.2rem; margin-bottom: 1.4rem;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, rgba(196,163,90,0.10), rgba(196,163,90,0.02));
}
.hero-kicker { font-size: 0.75rem; letter-spacing: 0.3em; color: var(--accent-primary); margin-bottom: 0.8rem; }
.hero-quote p {
  font-family: var(--font-serif); font-size: 1.5rem; line-height: 1.9;
  color: var(--text-primary); margin: 0 0 0.8rem;
}
.hero-quote cite { font-style: normal; font-size: 0.85rem; color: var(--text-muted); }
.hero-actions { display: flex; gap: 8px; margin-top: 1rem; }

.seg-tabs {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 0.9rem;
}
.seg-tab {
  font-family: var(--font-serif); font-size: 1.05rem; font-weight: 600;
  padding: 6px 18px; border-radius: var(--radius-full);
  border: 1px solid var(--border-glass); background: var(--bg-glass);
  color: var(--text-secondary); cursor: pointer; transition: all 0.2s;
}
.seg-tab.active { color: var(--accent-primary); border-color: rgba(196,163,90,0.5); background: rgba(196,163,90,0.1); }
.flex-spacer { flex: 1; }
.inspire-search {
  padding: 7px 12px; font-size: 0.85rem; border-radius: var(--radius-sm);
  background: var(--bg-glass); border: 1px solid var(--border-glass); color: var(--text-primary);
  width: 220px; max-width: 60vw;
}

.cat-chips { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 1rem; }
.cat-chip {
  font-size: 0.78rem; padding: 4px 12px; border-radius: var(--radius-full);
  background: var(--bg-glass); border: 1px solid var(--border-glass); cursor: pointer; transition: all 0.2s;
}
.cat-chip:hover { border-color: var(--accent-primary); }
.cat-chip.active { background: rgba(196,163,90,0.15); border-color: var(--accent-primary); color: var(--accent-primary); }
.cat-chip small { opacity: 0.7; margin-left: 2px; }

.inspire-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1rem; }
.inspire-card { padding: 1.1rem 1.2rem; display: flex; flex-direction: column; gap: 0.6rem; transition: transform 0.2s; }
.inspire-card:hover { transform: translateY(-2px); }
.ic-content {
  font-family: var(--font-serif); font-size: 0.95rem; line-height: 1.95;
  color: var(--text-primary); margin: 0; white-space: pre-wrap; word-break: break-word;
}
.ic-content.poem { font-size: 1.05rem; }
.ic-meta { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-top: auto; }
.ic-source { font-size: 0.75rem; color: var(--accent-primary); }
.ic-btn {
  font-size: 0.72rem; padding: 3px 10px; border-radius: var(--radius-sm);
  background: rgba(196,163,90,0.08); border: 1px solid rgba(196,163,90,0.2);
  color: var(--accent-primary); cursor: pointer;
}
.ic-btn:hover { background: rgba(196,163,90,0.18); }

.center { text-align: center; }
.muted { color: var(--text-muted); font-size: 0.9rem; }
</style>
