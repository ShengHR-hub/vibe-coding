<template>
  <div class="page-container">
    <ReadingNav v-if="from === 'reading'" />
    <NavBar v-else />
    <!-- 头部 -->
    <div class="upload-header">
      <div class="header-top">
        <button class="btn btn-ghost btn-sm" @click="$router.back()">&larr; 返回</button>
      </div>
      <h2>上传书籍</h2>
      <p class="header-sub">上传 TXT 文件，自动解析章节入库</p>
    </div>

    <!-- 上传区域 -->
    <div class="upload-area glass-card" :class="{ dragover }"
         @dragover.prevent="dragover = true"
         @dragleave="dragover = false"
         @drop.prevent="handleDrop"
         @click="fileInput.click()">
      <input ref="fileInput" type="file" accept=".txt" hidden @change="handleFileSelect" />
      <div v-if="!file" class="upload-prompt">
        <span class="upload-icon">&#128196;</span>
        <p class="upload-text">拖拽 TXT 文件到此处，或点击选择</p>
        <p class="upload-hint">支持 GBK / UTF-8 编码，自动检测章节</p>
      </div>
      <div v-else class="file-info">
        <span class="file-icon">&#128196;</span>
        <div class="file-detail">
          <p class="file-name">{{ file.name }}</p>
          <p class="file-size">{{ formatSize(file.size) }}</p>
        </div>
        <button class="btn btn-ghost btn-sm" @click.stop="clearFile">移除</button>
      </div>
    </div>

    <!-- 书籍信息表单 -->
    <div v-if="file" class="form-section glass-card">
      <h3 class="form-title">书籍信息</h3>
      <div class="form-grid">
        <div class="form-group">
          <label>书名</label>
          <input v-model="form.title" placeholder="留空则自动解析" />
        </div>
        <div class="form-group">
          <label>作者</label>
          <input v-model="form.author" placeholder="留空则自动解析" />
        </div>
        <div class="form-group">
          <label>类型</label>
          <select v-model="form.type">
            <option value="novel">小说</option>
            <option value="essay">散文</option>
            <option value="poetry">诗歌</option>
            <option value="webfiction">网文</option>
          </select>
        </div>
      </div>
    </div>

    <!-- 上传结果预览 -->
    <div v-if="result" class="result-section glass-card">
      <h3 class="result-title">上传成功</h3>
      <div class="result-info">
        <p><strong>{{ result.title }}</strong></p>
        <p>{{ result.chapters }} 个章节 · {{ formatWordCount(result.word_count) }} 字</p>
      </div>
      <div class="result-actions">
        <button class="btn btn-primary" @click="$router.push(`/library/library/${result.book_id}`)">查看书籍</button>
        <button class="btn btn-ghost" @click="resetForm">继续上传</button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="error-section glass-card">
      <p class="error-text">{{ error }}</p>
    </div>

    <!-- 提交按钮 -->
    <div v-if="file && !result && !uploading" class="submit-area">
      <button class="btn btn-primary" @click="doUpload" :disabled="uploading">
        {{ uploading ? '上传中...' : '确认上传' }}
      </button>
    </div>

    <!-- 上传进度 -->
    <div v-if="uploading" class="progress-area">
      <div class="progress-bar">
        <div class="progress-fill"></div>
      </div>
      <p class="progress-text">正在解析并上传...</p>
    </div>

    <!-- 分隔线 -->
    <div class="divider">
      <span class="divider-text">或</span>
    </div>

    <!-- 从URL导入 -->
    <div class="import-section glass-card">
      <h3 class="form-title">从网址导入</h3>
      <p class="import-desc">输入书籍页面URL，自动抓取内容入库</p>
      <div class="import-form">
        <input v-model="importUrl" placeholder="https://www.kxxs.top/book/..." class="import-input" />
        <button class="btn btn-primary" @click="importFromUrl" :disabled="importing || !importUrl">
          {{ importing ? '导入中...' : '导入' }}
        </button>
      </div>
      <div v-if="importResult" class="import-result">
        <p class="success-text">成功导入《{{ importResult.title }}》</p>
        <button class="btn btn-ghost btn-sm" @click="$router.push(`/library/library/${importResult.book_id}`)">查看书籍</button>
      </div>
      <div v-if="importError" class="error-text">{{ importError }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '../../api/index.js'
import NavBar from '../../components/NavBar.vue'
import ReadingNav from '../../components/ReadingNav.vue'

import { useToast } from '../../composables/useToast.js'
const route = useRoute()
const from = computed(() => route.query.from || 'write')
const toast = useToast()
const router = useRouter()
const fileInput = ref(null)
const file = ref(null)
const dragover = ref(false)
const importing = ref(false)
const uploading = ref(false)
const error = ref('')
const result = ref(null)

// URL导入相关
const importUrl = ref('')
const importResult = ref(null)
const importError = ref('')

const form = ref({
  title: '',
  author: '',
  type: 'novel',
})

function handleDrop(e) {
  dragover.value = false
  const dropped = e.dataTransfer.files[0]
  if (dropped && dropped.name.toLowerCase().endsWith('.txt')) {
    file.value = dropped
    error.value = ''
    result.value = null
  } else {
    error.value = '仅支持 TXT 格式文件'
  }
}

function handleFileSelect(e) {
  const selected = e.target.files[0]
  if (selected) {
    file.value = selected
    error.value = ''
    result.value = null
  }
}

function clearFile() {
  file.value = null
  error.value = ''
  result.value = null
  if (fileInput.value) fileInput.value.value = ''
}

async function doUpload() {
  if (!file.value) return
  uploading.value = true
  error.value = ''
  result.value = null

  const formData = new FormData()
  formData.append('file', file.value)
  if (form.value.title) formData.append('title', form.value.title)
  if (form.value.author) formData.append('author', form.value.author)
  formData.append('type', form.value.type)

  try {
    const resp = await fetch('/api/library/upload', {
      method: 'POST',
      credentials: 'include',
      body: formData,
    })
    const data = await resp.json()
    if (data.code === 0) {
      result.value = data.data
    } else {
      error.value = data.msg || '上传失败'
    }
  } catch {
    error.value = '网络错误，请检查连接'
  }
  uploading.value = false
}

function resetForm() {
  file.value = null
  result.value = null
  error.value = ''
  form.value = { title: '', author: '', type: 'novel' }
  if (fileInput.value) fileInput.value.value = ''
}

async function importFromUrl() {
  if (!importUrl.value) return
  importing.value = true
  importResult.value = null
  importError.value = ''

  try {
    const res = await api.post('/api/library/import', { url: importUrl.value })
    if (res.code === 0) {
      importResult.value = res.data
      toast.success('导入成功')
    } else {
      importError.value = res.msg || '导入失败'
    }
  } catch {
    importError.value = '网络错误'
  }
  importing.value = false
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}

function formatWordCount(wc) {
  if (!wc) return '0'
  if (wc >= 10000) return (wc / 10000).toFixed(1) + '万'
  return wc.toLocaleString()
}
</script>

<style scoped>
.page-container { }
/* ====== 头部 ====== */
.upload-header { margin-bottom: var(--space-xl); }
.header-top { margin-bottom: var(--space-md); }
.upload-header h2 {
  font-family: var(--font-serif); font-size: 1.5rem; font-weight: 700;
  margin: var(--space-md) 0 var(--space-sm);
}
.header-sub { font-size: 0.85rem; color: var(--text-muted); }

/* ====== 上传区域 ====== */
.upload-area {
  padding: var(--space-2xl); text-align: center;
  cursor: pointer; transition: all 0.3s ease;
  border: 2px dashed rgba(196,163,90,0.15);
  margin-bottom: var(--space-xl);
}
.upload-area:hover, .upload-area.dragover {
  border-color: rgba(196,163,90,0.4);
  background: rgba(196,163,90,0.02);
}
.upload-icon { font-size: 2.5rem; display: block; margin-bottom: var(--space-md); }
.upload-text { font-size: 0.95rem; color: var(--text-primary); margin-bottom: var(--space-sm); }
.upload-hint { font-size: 0.8rem; color: var(--text-muted); }

.file-info {
  display: flex; align-items: center; gap: var(--space-md);
  text-align: left; padding: 0 var(--space-md);
}
.file-icon { font-size: 1.8rem; flex-shrink: 0; }
.file-detail { flex: 1; }
.file-name { font-size: 0.95rem; font-weight: 500; }
.file-size { font-size: 0.8rem; color: var(--text-muted); }

/* ====== 表单 ====== */
.form-section { padding: var(--space-xl); margin-bottom: var(--space-xl); }
.form-title {
  font-family: var(--font-serif); font-size: 1.05rem; font-weight: 600;
  margin-bottom: var(--space-lg);
  padding-left: var(--space-md);
  border-left: 3px solid var(--accent-primary);
}
.form-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: var(--space-lg); }
.form-group label {
  display: block; font-size: 0.82rem; color: var(--text-muted);
  margin-bottom: var(--space-sm); letter-spacing: 0.03em;
}
.form-group input, .form-group select {
  width: 100%; padding: var(--space-sm) var(--space-md);
  background: var(--bg-glass); border: 1px solid var(--border-glass);
  border-radius: var(--radius-sm); color: var(--text-primary);
}

/* ====== 结果 ====== */
.result-section { padding: var(--space-xl); margin-bottom: var(--space-xl); text-align: center; }
.result-title {
  font-family: var(--font-serif); font-size: 1.1rem; font-weight: 600;
  color: var(--accent-green, #4ade80); margin-bottom: var(--space-md);
}
.result-info { margin-bottom: var(--space-lg); }
.result-info p { margin-bottom: var(--space-sm); }
.result-info strong { font-size: 1.1rem; }
.result-actions { display: flex; gap: var(--space-md); justify-content: center; }

/* ====== 错误 ====== */
.error-section {
  padding: var(--space-md) var(--space-lg); margin-bottom: var(--space-xl);
  border-left: 3px solid #ef4444;
}
.error-text { color: #ef4444; font-size: 0.9rem; }

/* ====== 提交 ====== */
.submit-area { text-align: center; margin-bottom: var(--space-lg); }
.submit-area .btn { padding: var(--space-sm) var(--space-2xl); }

/* ====== 进度 ====== */
.progress-area { text-align: center; margin-bottom: var(--space-lg); }
.progress-bar {
  height: 4px; background: rgba(196,163,90,0.1); border-radius: 2px;
  overflow: hidden; margin-bottom: var(--space-sm);
}
.progress-fill {
  height: 100%; width: 100%;
  background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary));
  animation: progress-pulse 1.5s ease-in-out infinite;
}
@keyframes progress-pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 1; }
}
.progress-text { font-size: 0.85rem; color: var(--text-muted); }

/* ====== 分隔线 ====== */
.divider {
  display: flex; align-items: center; gap: var(--space-lg);
  margin: var(--space-2xl) 0;
}
.divider::before, .divider::after {
  content: ''; flex: 1; height: 1px; background: var(--border-glass);
}
.divider-text {
  font-size: 0.82rem; color: var(--text-muted); letter-spacing: 0.1em;
}

/* ====== 导入 ====== */
.import-section { padding: var(--space-xl); margin-bottom: var(--space-xl); }
.import-desc { font-size: 0.85rem; color: var(--text-muted); margin-bottom: var(--space-lg); }
.import-form { display: flex; gap: var(--space-md); }
.import-input {
  flex: 1; padding: var(--space-sm) var(--space-md);
  background: var(--bg-glass); border: 1px solid var(--border-glass);
  border-radius: var(--radius-sm); color: var(--text-primary);
}
.import-result { margin-top: var(--space-md); }
.success-text { color: var(--accent-green, #4ade80); font-size: 0.9rem; margin-bottom: var(--space-sm); }
</style>
