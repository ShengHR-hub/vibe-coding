import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { api } from '../api/index.js'

export const useWritingStore = defineStore('writing', () => {
  const content = ref('')
  const title = ref('')
  const wordCount = ref(0)
  const currentWorkId = ref(null)
  const aiHistory = ref([])

  // 章节管理
  const chapters = ref([])
  const activeChapterId = ref(null)
  const chapterContentCache = ref({}) // {chapter_id: content}

  watch(content, (v) => {
    wordCount.value = v.replace(/\s/g, '').length
  })

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
      // 缓存所有章节内容
      for (const ch of chapters.value) {
        chapterContentCache.value[ch.chapter_id] = ch.content || ''
      }
      // 激活第一个章节
      if (chapters.value.length > 0 && !activeChapterId.value) {
        const first = chapters.value[0]
        activeChapterId.value = first.chapter_id
        content.value = chapterContentCache.value[first.chapter_id] || ''
      }
    }
  }

  async function switchChapter(chapterId) {
    if (chapterId === activeChapterId.value) return
    // 缓存当前章节内容
    if (activeChapterId.value) {
      chapterContentCache.value[activeChapterId.value] = content.value
    }
    activeChapterId.value = chapterId
    // 从缓存读取，如果没有则从chapters列表取
    if (chapterContentCache.value[chapterId] !== undefined) {
      content.value = chapterContentCache.value[chapterId]
    } else {
      const ch = chapters.value.find(c => c.chapter_id === chapterId)
      content.value = ch?.content || ''
      chapterContentCache.value[chapterId] = content.value
    }
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
      chapterContentCache.value[newCh.chapter_id] = ''
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
      delete chapterContentCache.value[chapterId]
      // 重排 chapter_no
      chapters.value.forEach((ch, i) => { ch.chapter_no = i + 1 })
      // 如果删的是当前章节，切换到第一个
      if (activeChapterId.value === chapterId && chapters.value.length > 0) {
        const first = chapters.value[0]
        activeChapterId.value = first.chapter_id
        content.value = chapterContentCache.value[first.chapter_id] || ''
      }
    }
  }

  async function reorderChapters(newOrder) {
    if (!currentWorkId.value) return
    const res = await api.put(`/api/works/${currentWorkId.value}/chapters/reorder`, { order: newOrder })
    if (res.code === 0) {
      // 本地重排
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
    chapterContentCache.value = {}
  }

  return {
    content, title, wordCount, currentWorkId, aiHistory,
    chapters, activeChapterId, chapterContentCache,
    setContent, addAiMessage, reset,
    loadChapters, switchChapter, addChapter, removeChapter, reorderChapters,
    getActiveChapterTitle, setActiveChapterTitle,
  }
})
