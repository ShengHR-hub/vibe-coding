<template>
  <div class="page-container">
    <ReadingNav />

    <div class="compare-header">
      <h2>书籍对比</h2>
      <p class="header-sub">选择 2-5 本书籍进行参数对比</p>
    </div>

    <!-- 书籍选择 -->
    <div class="selector-section glass-card">
      <div class="selected-books">
        <div v-for="book in selectedBooks" :key="book.book_id" class="selected-book">
          <span class="book-title">{{ book.title }}</span>
          <button class="btn-remove" @click="removeBook(book)">&#10005;</button>
        </div>
        <div v-if="selectedBooks.length < 5" class="add-book-btn" @click="showSearch = true">
          + 添加书籍
        </div>
      </div>
      <button class="btn btn-primary" @click="startCompare" :disabled="selectedBooks.length < 2">
        开始对比
      </button>
    </div>

    <!-- 搜索弹窗 -->
    <div v-if="showSearch" class="dialog-overlay" @click.self="showSearch = false">
      <div class="dialog glass-card">
        <h3>搜索书籍</h3>
        <input v-model="searchQuery" placeholder="输入书名搜索..." @input="searchBooks" />
        <div class="search-results">
          <div v-for="book in searchResults" :key="book.book_id" class="search-item"
               @click="addBook(book)">
            <span class="item-title">{{ book.title }}</span>
            <span class="item-author">{{ book.author }}</span>
          </div>
          <div v-if="searchQuery && searchResults.length === 0" class="no-results">
            未找到相关书籍
          </div>
        </div>
        <div class="dialog-actions">
          <button class="btn btn-ghost" @click="showSearch = false">关闭</button>
        </div>
      </div>
    </div>

    <!-- 对比结果 -->
    <div v-if="compareResult" class="compare-result">
      <div class="result-table glass-card">
        <table>
          <thead>
            <tr>
              <th>对比项</th>
              <th v-for="book in compareResult.books" :key="book.book_id">
                {{ book.title }}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>作者</td>
              <td v-for="book in compareResult.books" :key="book.book_id">
                {{ book.author }}
              </td>
            </tr>
            <tr>
              <td>类型</td>
              <td v-for="book in compareResult.books" :key="book.book_id">
                {{ typeLabel(book.type) }}
              </td>
            </tr>
            <tr>
              <td>字数</td>
              <td v-for="book in compareResult.books" :key="book.book_id">
                {{ formatWordCount(book.word_count) }}
              </td>
            </tr>
            <tr>
              <td>章节数</td>
              <td v-for="book in compareResult.books" :key="book.book_id">
                {{ book.chapter_count }} 章
              </td>
            </tr>
            <tr>
              <td>平均评分</td>
              <td v-for="book in compareResult.books" :key="book.book_id">
                <span class="rating">{{ book.rating_avg > 0 ? book.rating_avg.toFixed(1) : '暂无' }}</span>
              </td>
            </tr>
            <tr>
              <td>评分人数</td>
              <td v-for="book in compareResult.books" :key="book.book_id">
                {{ book.rating_count }} 人
              </td>
            </tr>
            <tr>
              <td>浏览量</td>
              <td v-for="book in compareResult.books" :key="book.book_id">
                {{ book.views }}
              </td>
            </tr>
            <tr>
              <td>收藏数</td>
              <td v-for="book in compareResult.books" :key="book.book_id">
                {{ book.favorites_count }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../api/index.js'
import ReadingNav from '../../components/ReadingNav.vue'

import { useToast } from '../../composables/useToast.js'
const toast = useToast()
const route = useRoute()

const selectedBooks = ref([])
const showSearch = ref(false)
const searchQuery = ref('')
const searchResults = ref([])
const compareResult = ref(null)

onMounted(async () => {
  // 从 URL 参数中获取初始书籍
  const ids = route.query.ids
  if (ids) {
    const idList = ids.split(',').filter(id => id.trim())
    for (const id of idList.slice(0, 5)) {
      const res = await api.get(`/api/library/${id}?source=library`)
      if (res.code === 0 && res.data.book) {
        selectedBooks.value.push({
          book_id: res.data.book.book_id,
          title: res.data.book.title,
          author: res.data.book.author
        })
      }
    }
    if (selectedBooks.value.length >= 2) {
      startCompare()
    }
  }
})

let searchTimer = null
function searchBooks() {
  clearTimeout(searchTimer)
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }
  searchTimer = setTimeout(async () => {
    const res = await api.get(`/api/library/search?q=${encodeURIComponent(searchQuery.value)}`)
    if (res.code === 0) {
      searchResults.value = res.data.items || []
    }
  }, 300)
}

function addBook(book) {
  if (selectedBooks.value.length >= 5) {
    toast.info('最多对比5本书籍')
    return
  }
  if (selectedBooks.value.find(b => b.book_id === book.book_id)) {
    toast.info('已添加该书籍')
    return
  }
  selectedBooks.value.push({
    book_id: book.book_id,
    title: book.title,
    author: book.author
  })
  showSearch.value = false
  searchQuery.value = ''
  searchResults.value = []
}

function removeBook(book) {
  selectedBooks.value = selectedBooks.value.filter(b => b.book_id !== book.book_id)
  compareResult.value = null
}

async function startCompare() {
  if (selectedBooks.value.length < 2) return
  const ids = selectedBooks.value.map(b => b.book_id).join(',')
  const res = await api.get(`/api/compare?ids=${ids}&type=library`)
  if (res.code === 0) {
    compareResult.value = res.data
  } else {
    toast.error(res.msg)
  }
}

function typeLabel(t) {
  return { novel: '小说', poetry: '诗歌', essay: '散文', webfiction: '网文', script: '剧本' }[t] || t
}

function formatWordCount(wc) {
  if (!wc) return '0'
  if (wc >= 10000) return (wc / 10000).toFixed(1) + '万'
  return wc.toLocaleString()
}
</script>

<style scoped>
.page-container { padding-top: 80px; }

.compare-header {
  margin-bottom: var(--space-xl);
}

.compare-header h2 {
  font-family: var(--font-serif);
  font-size: 1.8rem;
  font-weight: 700;
  background: linear-gradient(135deg, #e8e6f0, #c4a35a);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.25rem;
}

.header-sub {
  font-size: 0.85rem;
  color: var(--text-muted);
}

/* 选择器区域 */
.selector-section {
  padding: var(--space-xl);
  margin-bottom: var(--space-xl);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-lg);
  flex-wrap: wrap;
}

.selected-books {
  display: flex;
  gap: var(--space-md);
  flex-wrap: wrap;
  align-items: center;
}

.selected-book {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 6px 12px;
  background: rgba(196, 163, 90, 0.1);
  border: 1px solid rgba(196, 163, 90, 0.2);
  border-radius: var(--radius-full);
}

.book-title {
  font-size: 0.85rem;
  color: var(--text-primary);
}

.btn-remove {
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.75rem;
  padding: 2px;
  transition: color 0.2s;
}

.btn-remove:hover {
  color: var(--accent-red);
}

.add-book-btn {
  padding: 6px 16px;
  font-size: 0.85rem;
  color: var(--accent-primary);
  border: 1px dashed rgba(196, 163, 90, 0.3);
  border-radius: var(--radius-full);
  cursor: pointer;
  transition: all 0.2s;
}

.add-book-btn:hover {
  background: rgba(196, 163, 90, 0.1);
  border-color: rgba(196, 163, 90, 0.5);
}

/* 搜索弹窗 */
.dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.dialog {
  padding: var(--space-xl);
  width: 500px;
  max-height: 80vh;
}

.dialog h3 {
  margin-bottom: var(--space-lg);
}

.dialog input {
  width: 100%;
  margin-bottom: var(--space-lg);
}

.search-results {
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: var(--space-lg);
}

.search-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: background 0.2s;
}

.search-item:hover {
  background: rgba(196, 163, 90, 0.1);
}

.item-title {
  font-size: 0.9rem;
  color: var(--text-primary);
}

.item-author {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.no-results {
  text-align: center;
  padding: var(--space-xl);
  color: var(--text-muted);
  font-size: 0.85rem;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
}

/* 对比结果 */
.compare-result {
  margin-top: var(--space-xl);
}

.result-table {
  padding: var(--space-xl);
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: var(--space-md) var(--space-lg);
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 0.85rem;
}

th {
  color: var(--accent-primary);
  font-weight: 600;
  white-space: nowrap;
}

td {
  color: var(--text-secondary);
}

tr:hover td {
  background: rgba(255, 255, 255, 0.02);
}

.rating {
  color: var(--accent-primary);
  font-weight: 600;
}

/* 响应式 */
@media (max-width: 768px) {
  .selector-section {
    flex-direction: column;
    align-items: stretch;
  }

  .dialog {
    width: 95%;
  }

  th, td {
    padding: var(--space-sm);
    font-size: 0.75rem;
  }
}
</style>
