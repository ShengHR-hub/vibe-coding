import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useWritingStore = defineStore('writing', () => {
  const content = ref('')
  const title = ref('')
  const wordCount = ref(0)
  const currentWorkId = ref(null)
  const aiHistory = ref([])

  watch(content, (v) => {
    wordCount.value = v.replace(/\s/g, '').length
  })

  function setContent(text) {
    content.value = text
  }

  function addAiMessage(role, text) {
    aiHistory.value.push({ role, text, time: Date.now() })
  }

  function reset() {
    content.value = ''
    title.value = ''
    currentWorkId.value = null
    aiHistory.value = []
  }

  return { content, title, wordCount, currentWorkId, aiHistory, setContent, addAiMessage, reset }
})
