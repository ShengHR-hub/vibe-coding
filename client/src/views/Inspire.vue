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
        <template v-if="userStore.isLoggedIn">
          <button class="btn btn-ghost btn-sm" v-if="hero" @click="pickRef({ type: '诗词', content: hero.content })">
            {{ isPicked(hero.content) ? '✓ 已引用到创作' : '＋ 引用到创作' }}
          </button>
          <button class="btn btn-ghost btn-sm" v-if="hero" @click="toggleFav('poem', hero.poem_id)" :class="{ starred: isFav('poem', hero.poem_id) }">
            {{ isFav('poem', hero.poem_id) ? '♥ 已收藏' : '♡ 收藏' }}
          </button>
          <button class="btn btn-primary btn-sm" @click="openAdd">＋ 收录句子</button>
        </template>
      </div>
    </section>

    <!-- 内容区 -->
    <section class="inspire-main">
      <div class="seg-tabs">
        <button v-for="t in segs" :key="t.key" class="seg-tab" :class="{ active: activeTab === t.key }" @click="switchSeg(t.key)">
          {{ t.label }}
        </button>
        <span class="flex-spacer"></span>
        <template v-if="activeTab !== 'favorites' && activeTab !== 'intent' && activeTab !== 'my'">
          <input class="inspire-search" v-model="query" placeholder="搜索内容 / 作者…" @keydown.enter="doSearch" />
          <button class="btn btn-primary btn-sm" @click="doSearch">搜索</button>
          <button class="btn btn-ghost btn-sm" @click="refresh" :disabled="loading">{{ loading ? '…' : '换一批' }}</button>
        </template>
      </div>

      <div class="cat-chips" v-if="activeTab === 'poems' && cats.length">
        <span class="cat-chip" :class="{ active: activeCat === '' }" @click="pickCat('')">全部</span>
        <span v-for="c in cats" :key="c.category" class="cat-chip" :class="{ active: activeCat === c.category }" @click="pickCat(c.category)">
          {{ c.category }}<small> {{ c.count }}</small>
        </span>
      </div>

      <!-- 意境找句（F：按意思搜诗句 → 引用 / AI 原创） -->
      <div v-if="activeTab === 'intent'" class="intent-area">
        <FindLinesPanel />
      </div>

      <!-- 我的灵感：便签 / AI 主线 / 收藏 三区聚合（P6-B2） -->
      <div v-else-if="activeTab === 'my'" class="my-area">
        <div class="my-card glass-card">
          <div class="my-card-head">
            <span class="my-title">闪念便签</span>
            <span class="my-sub">写作中随手记下的点子（写作台右下角「记」也可记）</span>
          </div>
          <div class="my-list">
            <p v-if="!notes.length" class="muted my-empty">还没有便签，去写作台点「记」记一个闪念吧</p>
            <div v-for="n in notes" :key="'n' + n.note_id" class="my-item">
              <p class="my-text">{{ n.content }}</p>
              <div class="my-item-foot">
                <span class="my-time">{{ (n.updated_at || '').slice(5, 16) }}</span>
                <button class="ic-btn" @click="deleteNote(n.note_id)">✕</button>
              </div>
            </div>
            <div class="my-add-row">
              <input v-model="noteDraft" class="my-input" placeholder="记一个闪念…（回车保存）" @keydown.enter="addNote" />
              <button class="btn btn-primary btn-sm" @click="addNote" :disabled="!noteDraft.trim()">记下</button>
            </div>
          </div>
        </div>

        <div class="my-card glass-card">
          <div class="my-card-head">
            <span class="my-title">AI 主线</span>
            <span class="my-sub">让 AI 从灵感里帮你定整体大方向，随时生成/重新生成</span>
          </div>
          <textarea v-model="mainlineInput" class="my-input my-textarea" rows="2" placeholder="贴几条灵感/闪念，或直接描述你脑海里的故事…"></textarea>
          <button class="btn btn-primary btn-sm" @click="genMainline" :disabled="mainlineLoading || !mainlineInput.trim()">
            {{ mainlineLoading ? '生成中…' : '生成整体主线' }}
          </button>
          <div v-if="mainlineResult" class="my-result">
            <p class="my-result-text">{{ mainlineResult }}</p>
            <div class="my-item-foot">
              <span class="my-time">AI 生成</span>
              <button class="ic-btn" @click="saveMainline">保存到我的灵感</button>
              <button class="ic-btn" @click="mainlineResult = ''">放弃</button>
            </div>
          </div>
          <div v-if="mainlines.length" class="my-list">
            <p class="muted my-empty" style="text-align:left">已保存的主线：</p>
            <div v-for="m in mainlines" :key="'m' + m.note_id" class="my-item">
              <p class="my-text">{{ m.content }}</p>
              <div class="my-item-foot">
                <span class="my-time">{{ (m.updated_at || '').slice(5, 16) }}</span>
                <button class="ic-btn" @click="deleteNote(m.note_id)">✕</button>
              </div>
            </div>
          </div>
        </div>

        <div class="my-card glass-card">
          <div class="my-card-head">
            <span class="my-title">我的收藏</span>
            <span class="my-sub">在诗词/素材里点 ♡ 收藏的内容</span>
          </div>
          <div class="my-list">
            <p v-if="!favItems.length" class="muted my-empty">还没有收藏，去诗词/素材里点 ♡ 吧</p>
            <div v-for="f in favItems" :key="'f' + f.fav_id" class="my-item">
              <p class="my-text">{{ f.content }}</p>
              <div class="my-item-foot">
                <span class="my-time">{{ f.item_type === 'poem' ? `《${f.title}》${f.author}` : (f.title || '素材') }}</span>
                <button class="ic-btn" @click="removeFav(f)">✕</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template v-else>
      <div v-if="loading" class="center muted" style="padding: 3rem 0">灵感加载中…</div>
      <div v-else-if="items.length === 0" class="center muted" style="padding: 3rem 0">
        {{ activeTab === 'favorites' ? '还没有收藏，去诗词/素材里点 ♡ 收藏吧' : '暂无内容，换个分类或关键词试试' }}
      </div>

      <!-- 收藏列表 -->
      <div v-else-if="activeTab === 'favorites'" class="inspire-grid">
        <div v-for="it in items" :key="'fav-' + it.fav_id" class="inspire-card glass-card">
          <p class="ic-content" :class="{ poem: it.item_type === 'poem' }">{{ it.content }}</p>
          <div class="ic-meta">
            <span class="ic-source">{{ it.item_type === 'poem' ? `《${it.title}》${it.author}` : (it.title || '素材') }}</span>
            <button class="ic-btn" @click="removeFav(it)">✕ 取消收藏</button>
          </div>
        </div>
      </div>

      <!-- 诗词 / 素材列表 -->
      <div v-else class="inspire-grid">
        <div v-for="(it, i) in items" :key="activeTab + '-' + (it.poem_id || it.material_id || i)" class="inspire-card glass-card">
          <p class="ic-content" :class="{ poem: activeTab === 'poems' }">{{ it.content }}</p>
          <div class="ic-meta">
            <span class="ic-source">
              <template v-if="activeTab === 'poems'">《{{ it.title }}》{{ it.author }}<template v-if="it.dynasty">〔{{ it.dynasty }}〕</template></template>
              <template v-else>{{ it.category }}</template>
            </span>
            <div class="ic-actions">
              <button v-if="userStore.isLoggedIn" class="ic-btn" :class="{ starred: isFav(kindKey, kindId(it)) }" @click="toggleFav(kindKey, kindId(it))">
                {{ isFav(kindKey, kindId(it)) ? '♥' : '♡' }}
              </button>
              <button class="ic-btn" @click="pickRef(activeTab === 'poems' ? { type: '诗词', content: it.content } : { type: it.category || '素材', content: it.content })">
                {{ isPicked(it.content) ? '✓ 已引用' : '＋ 引用' }}
              </button>
            </div>
          </div>
        </div>
      </div>
      </template>
    </section>

    <!-- 收录句子弹窗 -->
    <div v-if="addOpen" class="modal-overlay" @click.self="closeAdd">
      <div class="modal glass-card">
        <h3>收录一句灵感</h3>
        <input v-model="addCategory" placeholder="分类（如：景物描写 / 名言金句）" maxlength="20" />
        <textarea v-model="addContent" rows="3" placeholder="把喜欢的句子抄进来，之后写续写/润色时可以直接引用…"></textarea>
        <p class="modal-hint">收录后进入共享素材库，灵感馆与写作素材区都会出现，写作时可一键引用。</p>
        <div class="modal-actions">
          <button class="btn btn-ghost" @click="closeAdd">取消</button>
          <button class="btn btn-primary" @click="submitAdd" :disabled="adding">{{ adding ? '保存中…' : '收录' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api } from '../api/index.js'
import { useWritingStore } from '../stores/writing.js'
import { useUserStore } from '../stores/user.js'
import { useToast } from '../composables/useToast.js'
import FindLinesPanel from '../components/FindLinesPanel.vue'

const writingStore = useWritingStore()
const userStore = useUserStore()
const toast = useToast()

const activeTab = ref('poems')
const items = ref([])
const cats = ref([])
const activeCat = ref('')
const query = ref('')
const loading = ref(false)
const hero = ref(null)
const heroLoading = ref(false)
const favSet = ref(new Set())

const BASE_SEGS = [
  { key: 'intent', label: '意境找句' },
  { key: 'my', label: '我的灵感' },
  { key: 'poems', label: '诗词' },
  { key: 'materials', label: '句子素材' },
]
const segs = computed(() => {
  const base = [...BASE_SEGS]
  if (userStore.isLoggedIn) base.push({ key: 'favorites', label: `收藏${favsCount.value ? ` (${favsCount.value})` : ''}` })
  // 「我的灵感」是个人数据，未登录不显示
  const all = base.filter(s => s.key !== 'my' || userStore.isLoggedIn)
  return all
})
const favsCount = computed(() => favSet.value.size)

const kindKey = computed(() => (activeTab.value === 'poems' ? 'poem' : 'material'))

function kindId(it) {
  return activeTab.value === 'poems' ? it.poem_id : it.material_id
}
function favKey(kind, id) {
  return kind + ':' + id
}
function isFav(kind, id) {
  return !!id && favSet.value.has(favKey(kind, id))
}
function isPicked(content) {
  return writingStore.pickedRefs.some(r => r.content === content)
}
function pickRef(item) {
  writingStore.pickRef(item)
}

// ---- 收录句子（F3）----
const addOpen = ref(false)
const addCategory = ref('')
const addContent = ref('')
const adding = ref(false)

function openAdd() {
  addCategory.value = ''
  addContent.value = ''
  addOpen.value = true
}
function closeAdd() {
  if (adding.value) return
  addOpen.value = false
}
async function submitAdd() {
  const content = addContent.value.trim()
  if (!content) { toast.info('请先写一句内容'); return }
  adding.value = true
  const res = await api.post('/api/materials', {
    category: addCategory.value.trim() || '随想',
    content,
  })
  adding.value = false
  if (res.code === 0) {
    toast.success('已收录到素材库')
    addOpen.value = false
    addCategory.value = ''
    addContent.value = ''
    loadCats()
    if (activeTab.value === 'materials') {
      activeCat.value = ''
      query.value = ''
      loadItems()
    }
  } else {
    toast.error(res.msg)
  }
}

async function refreshFavs() {
  if (!userStore.isLoggedIn) return
  const res = await api.get('/api/inspire/favorites')
  if (res.code === 0) {
    const next = new Set()
    for (const f of res.data.items || []) next.add(favKey(f.item_type, f.ref_id))
    favSet.value = next
  }
}

async function toggleFav(kind, id) {
  if (!kind || !id) return
  const key = favKey(kind, id)
  let res
  if (favSet.value.has(key)) {
    res = await api.delete(`/api/inspire/favorites/${kind}/${id}`)
    if (res.code === 0) {
      favSet.value = new Set([...favSet.value].filter(k => k !== key))
      if (activeTab.value === 'favorites') items.value = items.value.filter(i => !(i.item_type === kind && i.ref_id === id))
    }
  } else {
    res = await api.post('/api/inspire/favorites', { item_type: kind, ref_id: id })
    if (res.code === 0) {
      favSet.value = new Set(favSet.value).add(key)
      if (activeTab.value === 'favorites') await loadItems()
    }
  }
}

async function removeFav(it) {
  await toggleFav(it.item_type, it.ref_id)
}

async function loadHero() {
  heroLoading.value = true
  const res = await api.get('/api/poems/featured?count=1')
  if (res.code === 0 && res.data.poems?.length) hero.value = res.data.poems[0]
  heroLoading.value = false
}

async function loadCats() {
  if (activeTab.value === 'favorites') { cats.value = []; return }
  const url = activeTab.value === 'poems' ? '/api/poems/categories' : '/api/materials/categories'
  const r = await api.get(url)
  if (r.code === 0) cats.value = r.data.categories || []
}

async function loadItems() {
  loading.value = true
  if (activeTab.value === 'favorites') {
    const res = await api.get('/api/inspire/favorites')
    if (res.code === 0) items.value = (res.data.items || []).map(f => ({
      fav_id: f.fav_id, item_type: f.item_type, ref_id: f.ref_id,
      title: f.title, author: f.author, content: f.content,
    }))
    else items.value = []
    loading.value = false
    return
  }
  const poems = activeTab.value === 'poems'
  const q = query.value.trim()
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
  // 意境找句页不加载素材列表
  if (key === 'intent') return
  // 我的灵感页加载三区数据
  if (key === 'my') {
    if (userStore.isLoggedIn) {
      loadMyNotes()
      loadMyFavs()
    }
    return
  }
  loadCats()
  if (key === 'favorites' && userStore.isLoggedIn) refreshFavs()
  loadItems()
}

// ---- 我的灵感（P6-B2）：便签 / AI 主线 / 收藏 三区聚合 ----
const notes = ref([])
const mainlines = ref([])
const favItems = ref([])
const noteDraft = ref('')
const mainlineInput = ref('')
const mainlineResult = ref('')
const mainlineLoading = ref(false)

async function loadMyNotes() {
  if (!userStore.isLoggedIn) return
  const res = await api.get('/api/notes')
  if (res.code === 0) {
    const all = res.data.items || []
    notes.value = all.filter(i => i.kind === 'note')
    mainlines.value = all.filter(i => i.kind === 'mainline')
  }
}

async function loadMyFavs() {
  if (!userStore.isLoggedIn) return
  const res = await api.get('/api/inspire/favorites')
  if (res.code === 0) favItems.value = res.data.items || []
}

async function addNote() {
  const text = noteDraft.value.trim()
  if (!text) return
  const res = await api.post('/api/notes', { content: text })
  if (res.code === 0) { noteDraft.value = ''; loadMyNotes() }
}

async function deleteNote(noteId) {
  await api.delete(`/api/notes/${noteId}`)
  loadMyNotes()
}

async function genMainline() {
  const inspiration = mainlineInput.value.trim()
  if (!inspiration || mainlineLoading.value) return
  mainlineLoading.value = true
  const res = await api.post('/api/write/mainline', { inspiration })
  mainlineLoading.value = false
  if (res.code === 0) mainlineResult.value = res.data.mainline
  else toast.error(res.msg)
}

async function saveMainline() {
  const text = mainlineResult.value.trim()
  if (!text) return
  const res = await api.post('/api/notes', { content: text, kind: 'mainline' })
  if (res.code === 0) { mainlineResult.value = ''; mainlineInput.value = ''; loadMyNotes() }
}

onMounted(async () => {
  if (activeTab.value === 'intent') {
    await Promise.all([loadHero(), refreshFavs()])
    return
  }
  await Promise.all([loadHero(), refreshFavs(), loadCats(), loadItems()])
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
.hero-actions { display: flex; gap: 8px; margin-top: 1rem; flex-wrap: wrap; }
.hero-actions .starred { color: #e0716b; }

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

.intent-area { padding: 0.4rem 0 1rem; }

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
.ic-actions { display: flex; gap: 6px; flex-shrink: 0; }
.ic-btn {
  font-size: 0.72rem; padding: 3px 10px; border-radius: var(--radius-sm);
  background: rgba(196,163,90,0.08); border: 1px solid rgba(196,163,90,0.2);
  color: var(--accent-primary); cursor: pointer;
}
.ic-btn:hover { background: rgba(196,163,90,0.18); }
.ic-btn.starred { color: #e0716b; border-color: rgba(224,113,107,0.4); background: rgba(224,113,107,0.08); }

/* 我的灵感（P6-B2） */
.my-area { display: flex; flex-direction: column; gap: 18px; }
.my-card { padding: 16px 18px; }
.my-card-head { display: flex; align-items: baseline; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
.my-title { font-family: var(--font-serif); font-weight: 600; font-size: 0.98rem; color: var(--text-primary); }
.my-sub { color: var(--text-muted); font-size: 0.75rem; }
.my-list { display: flex; flex-direction: column; gap: 6px; }
.my-item { padding: 8px 10px; border-radius: 8px; background: var(--bg-glass); border: 1px solid rgba(196,163,90,0.1); }
.my-text { margin: 0; font-size: 0.85rem; line-height: 1.7; white-space: pre-wrap; word-break: break-word; color: var(--text-primary); }
.my-item-foot { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; gap: 8px; }
.my-time { color: var(--text-muted); font-size: 0.7rem; }
.my-empty { font-size: 0.8rem; margin: 0; }
.my-add-row { display: flex; gap: 8px; margin-top: 8px; }
.my-input { flex: 1; background: var(--bg-glass); color: var(--text-primary); border: 1px solid rgba(196,163,90,0.2); border-radius: 8px; padding: 7px 10px; font-size: 0.85rem; }
.my-textarea { resize: none; width: 100%; box-sizing: border-box; margin-bottom: 8px; }
.my-result { margin-top: 10px; padding: 10px 12px; border-radius: 10px; background: rgba(196,163,90,0.08); border: 1px solid rgba(196,163,90,0.25); }
.my-result-text { margin: 0 0 8px; font-size: 0.85rem; line-height: 1.8; white-space: pre-wrap; color: var(--text-primary); }

.center { text-align: center; }
.muted { color: var(--text-muted); font-size: 0.9rem; }

/* 收录弹窗 */
.modal-overlay {
  position: fixed; inset: 0; z-index: 300;
  background: rgba(0, 0, 0, 0.45);
  display: flex; align-items: center; justify-content: center;
  padding: 1rem;
}
.modal { width: min(460px, 92vw); padding: 1.4rem 1.6rem; border-radius: var(--radius-lg); }
.modal h3 { font-family: var(--font-serif); margin-bottom: 0.9rem; }
.modal input, .modal textarea {
  width: 100%; box-sizing: border-box; padding: 8px 12px; font-size: 0.88rem;
  border-radius: var(--radius-sm); background: var(--bg-glass);
  border: 1px solid var(--border-glass); color: var(--text-primary);
  margin-bottom: 0.7rem;
}
.modal-hint { font-size: 0.76rem; color: var(--text-muted); margin: 0 0 0.8rem; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; }
</style>
