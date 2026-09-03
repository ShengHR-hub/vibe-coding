import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { api } from '../api/index.js'

export const useWritingStore = defineStore('writing', () => {
  const title = ref('')
  const currentWorkId = ref(null)
  const aiHistory = ref([])

  // W4b：素材/诗词引用队列（references）——供 AI 请求注入，最多 6 条
  const pickedRefs = ref([])

  function pickRef(item) {
    const key = item.content || item.text || ''
    const idx = pickedRefs.value.findIndex(r => r.content === key)
    if (idx >= 0) {
      pickedRefs.value.splice(idx, 1)
      return
    }
    if (pickedRefs.value.length >= 6) pickedRefs.value.shift()
    pickedRefs.value.push({ type: item.type || item.category || '素材', content: key })
  }

  function clearRefs() {
    pickedRefs.value = []
  }

  // 章节管理 — 唯一数据源：chapters 数组
  const chapters = ref([])
  const activeChapterId = ref(null)

  // 当前章节内容（直接读写 chapters 数组中的对应项）
  const content = ref('')

  // 自动同步 content 变化到 chapters 数组（防止丢失）
  watch(content, (newVal) => {
    if (!activeChapterId.value) return
    const ch = chapters.value.find(c => c.chapter_id === activeChapterId.value)
    if (ch) ch.content = newVal
  })

  // 字数统计（基于 content）
  const wordCount = computed(() => content.value.replace(/\s/g, '').length)

  /** 同步当前 content 到 chapters 数组 */
  function _syncContentToChapters() {
    if (!activeChapterId.value) return
    const ch = chapters.value.find(c => c.chapter_id === activeChapterId.value)
    if (ch) ch.content = content.value
  }

  /** 从 chapters 数组加载指定章节的 content */
  function _loadContentFromChapters(chapterId) {
    const ch = chapters.value.find(c => c.chapter_id === chapterId)
    content.value = ch?.content || ''
  }

  function setContent(text) {
    content.value = text
  }

  function addAiMessage(role, text) {
    aiHistory.value.push({ role, text, time: Date.now() })
  }

  async function loadChapters(workId) {
    if (!workId) return
    const res = await api.get(`/api/works/${workId}`)
    if (res.code === 0) {
      chapters.value = res.data.chapters || []
      title.value = res.data.work?.title || ''
      // 激活第一个章节
      if (chapters.value.length > 0 && !activeChapterId.value) {
        activeChapterId.value = chapters.value[0].chapter_id
        content.value = chapters.value[0].content || ''
      }
    }
  }

  async function switchChapter(chapterId) {
    if (chapterId === activeChapterId.value) return
    // 先把当前内容存回 chapters 数组
    _syncContentToChapters()
    // 切换
    activeChapterId.value = chapterId
    _loadContentFromChapters(chapterId)
  }

  async function addChapter() {
    if (!currentWorkId.value) return null
    const res = await api.post(`/api/works/${currentWorkId.value}/chapters`, {})
    if (res.code === 0) {
      const newCh = {
        chapter_id: res.data.chapter_id,
        chapter_no: res.data.chapter_no,
        title: res.data.title,
        word_count: 0,
        content: '',
      }
      chapters.value.push(newCh)
      await switchChapter(newCh.chapter_id)
      return newCh
    }
    return null
  }

  async function removeChapter(chapterId) {
    if (!currentWorkId.value) return
    if (chapters.value.length <= 1) return // 至少保留一章
    const res = await api.delete(`/api/works/${currentWorkId.value}/chapters/${chapterId}`)
    if (res.code === 0) {
      chapters.value = chapters.value.filter(c => c.chapter_id !== chapterId)
      // 重排 chapter_no
      chapters.value.forEach((ch, i) => { ch.chapter_no = i + 1 })
      // 如果删的是当前章节，切换到第一个
      if (activeChapterId.value === chapterId && chapters.value.length > 0) {
        activeChapterId.value = chapters.value[0].chapter_id
        content.value = chapters.value[0].content || ''
      }
    }
  }

  async function reorderChapters(newOrder) {
    if (!currentWorkId.value) return
    const res = await api.put(`/api/works/${currentWorkId.value}/chapters/reorder`, { order: newOrder })
    if (res.code === 0) {
      const ordered = []
      for (const id of newOrder) {
        const ch = chapters.value.find(c => c.chapter_id === id)
        if (ch) ordered.push(ch)
      }
      ordered.forEach((ch, i) => { ch.chapter_no = i + 1 })
      chapters.value = ordered
    }
  }

  function getActiveChapterTitle() {
    const ch = chapters.value.find(c => c.chapter_id === activeChapterId.value)
    return ch?.title || ''
  }

  function setActiveChapterTitle(newTitle) {
    const ch = chapters.value.find(c => c.chapter_id === activeChapterId.value)
    if (ch) ch.title = newTitle
  }

  function reset() {
    content.value = ''
    title.value = ''
    currentWorkId.value = null
    aiHistory.value = []
    chapters.value = []
    activeChapterId.value = null
  }

  return {
    content, title, wordCount, currentWorkId, aiHistory,
    chapters, activeChapterId,
    pickedRefs, pickRef, clearRefs,
    setContent, addAiMessage, reset,
    loadChapters, switchChapter, addChapter, removeChapter, reorderChapters,
    getActiveChapterTitle, setActiveChapterTitle,
  }
})
