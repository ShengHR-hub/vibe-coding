<template>
  <div class="rp-container">
    <!-- 顶部：作品信息 + 角色选择 -->
    <header class="rp-header">
      <button class="btn btn-ghost btn-sm" @click="$router.back()">&larr; 返回</button>
      <div class="rp-work-info">
        <span class="rp-work-title">{{ workTitle }}</span>
        <span class="rp-label">角色扮演</span>
      </div>
      <div class="rp-actions">
        <button class="btn btn-ghost btn-sm" @click="extractChars" :disabled="extracting">
          {{ extracting ? '提取中...' : 'AI 提取角色' }}
        </button>
      </div>
    </header>

    <div class="rp-body">
      <!-- 角色卡片 -->
      <div class="rp-char-bar">
        <div
          v-for="ch in characters" :key="ch.char_id"
          class="char-card" :class="{ active: activeChar?.char_id === ch.char_id }"
          @click="selectChar(ch)"
        >
          <div class="char-avatar">{{ ch.name?.charAt(0) }}</div>
          <span class="char-name">{{ ch.name }}</span>
          <button class="char-del" @click.stop="deleteChar(ch)">&times;</button>
        </div>
        <div class="char-card add-card" @click="showAddChar = true">
          <span>+</span>
        </div>
      </div>

      <!-- 聊天区 -->
      <div class="rp-chat-area" ref="chatArea">
        <div v-if="!activeChar" class="rp-empty">
          <p>选择一个角色开始对话</p>
          <p class="muted">点击上方角色卡片，或使用"AI 提取角色"自动生成</p>
        </div>
        <div v-else>
          <!-- 角色信息 -->
          <div class="char-info-banner" v-if="activeChar">
            <strong>{{ activeChar.name }}</strong>
            <span v-if="activeChar.personality"> — {{ activeChar.personality }}</span>
          </div>
          <!-- 消息列表 -->
          <div v-for="(msg, i) in messages" :key="i" class="rp-msg" :class="msg.role">
            <div class="msg-avatar" v-if="msg.role === 'char'">{{ activeChar?.name?.charAt(0) }}</div>
            <div class="msg-bubble">
              <div class="msg-name" v-if="msg.role === 'char'">{{ activeChar?.name }}</div>
              <div class="msg-text" v-html="renderMsg(msg.text)"></div>
            </div>
            <div class="msg-avatar user-avatar" v-if="msg.role === 'user'">{{ userStore.user?.username?.charAt(0) || '我' }}</div>
          </div>
          <!-- 加载中 -->
          <div v-if="streaming" class="rp-msg char">
            <div class="msg-avatar">{{ activeChar?.name?.charAt(0) }}</div>
            <div class="msg-bubble">
              <div class="msg-name">{{ activeChar?.name }}</div>
              <div class="msg-text">{{ streamText }}<span class="cursor">|</span></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <div class="rp-input-area" v-if="activeChar">
        <textarea
          v-model="inputText"
          placeholder="说点什么..."
          rows="2"
          @keydown.enter.ctrl="send"
          @keydown.enter.meta="send"
        ></textarea>
        <button class="btn btn-primary btn-sm" @click="send" :disabled="!inputText.trim() || streaming">
          发送
        </button>
      </div>
    </div>

    <!-- 添加角色弹窗 -->
    <div v-if="showAddChar" class="modal-overlay" @click.self="showAddChar = false">
      <div class="modal glass-card">
        <h3>添加角色</h3>
        <div class="form-group">
          <label>角色名 *</label>
          <input v-model="newChar.name" placeholder="如：陈平安" />
        </div>
        <div class="form-group">
          <label>外貌描述</label>
          <textarea v-model="newChar.description" rows="2" placeholder="外貌特征"></textarea>
        </div>
        <div class="form-group">
          <label>性格</label>
          <textarea v-model="newChar.personality" rows="2" placeholder="性格特点"></textarea>
        </div>
        <div class="form-group">
          <label>背景故事</label>
          <textarea v-model="newChar.background" rows="2" placeholder="角色背景"></textarea>
        </div>
        <div class="form-group">
          <label>说话风格</label>
          <input v-model="newChar.speaking_style" placeholder="如：沉默寡言，偶尔说出深刻的话" />
        </div>
        <div class="modal-actions">
          <button class="btn btn-ghost btn-sm" @click="showAddChar = false">取消</button>
          <button class="btn btn-primary btn-sm" @click="addChar" :disabled="!newChar.name.trim()">添加</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../../api/index.js'
import { renderBr } from '../../utils/render.js'
import { useUserStore } from '../../stores/user.js'

import { useToast } from '../../composables/useToast.js'
const toast = useToast()
const route = useRoute()
const userStore = useUserStore()
const workId = route.params.work_id
const workTitle = ref('')
const characters = ref([])
const activeChar = ref(null)
const messages = ref([])
const inputText = ref('')
const streaming = ref(false)
const streamText = ref('')
const extracting = ref(false)
const showAddChar = ref(false)
const chatArea = ref(null)
const newChar = ref({ name: '', description: '', personality: '', background: '', speaking_style: '' })

function renderMsg(text) {
  return renderBr(text)
}

async function loadCharacters() {
  const res = await api.get(`/api/rp/${workId}/characters`)
  if (res.code === 0) characters.value = res.data.characters || []
}

async function loadWorkTitle() {
  const res = await api.get(`/api/works/public/${workId}`)
  if (res.code === 0) workTitle.value = res.data.work?.title || ''
  else {
    const res2 = await api.get(`/api/works/${workId}`)
    if (res2.code === 0) workTitle.value = res2.data.work?.title || ''
  }
}

function selectChar(ch) {
  activeChar.value = ch
  messages.value = []
}

async function deleteChar(ch) {
  if (!confirm(`确定删除角色「${ch.name}」？`)) return
  await api.delete(`/api/rp/characters/${ch.char_id}`)
  if (activeChar.value?.char_id === ch.char_id) {
    activeChar.value = null
    messages.value = []
  }
  await loadCharacters()
}

async function addChar() {
  if (!newChar.value.name.trim()) return
  const res = await api.post(`/api/rp/${workId}/characters`, newChar.value)
  if (res.code === 0) {
    showAddChar.value = false
    newChar.value = { name: '', description: '', personality: '', background: '', speaking_style: '' }
    await loadCharacters()
  }
}

async function extractChars() {
  extracting.value = true
  const res = await api.post(`/api/rp/${workId}/characters/extract`, {})
  extracting.value = false
  if (res.code === 0) {
    await loadCharacters()
    toast.success(`已提取 ${res.data.count} 个角色`)
  } else {
    toast.error(res.msg || '提取失败')
  }
}

async function send() {
  const text = inputText.value.trim()
  if (!text || streaming.value || !activeChar.value) return

  messages.value.push({ role: 'user', text })
  inputText.value = ''
  streaming.value = true
  streamText.value = ''

  await nextTick()
  scrollBottom()

  const history = messages.value.slice(0, -1).map(m => ({
    role: m.role === 'user' ? 'user' : 'assistant',
    content: m.text,
  }))

  try {
    await api.stream('/api/rp/chat', {
      char_id: activeChar.value.char_id,
      message: text,
      history,
    },
    (chunk) => {
      try {
        const data = JSON.parse(chunk)
        if (data.chunk) {
          streamText.value += data.chunk
          nextTick(scrollBottom)
        }
        if (data.error) {
          messages.value.push({ role: 'char', text: `[错误] ${data.error}` })
          streamText.value = ''
          streaming.value = false
        }
      } catch { /* ignore non-JSON */ }
    },
    () => {
      messages.value.push({ role: 'char', text: streamText.value })
      streamText.value = ''
      streaming.value = false
      nextTick(scrollBottom)
    },
    (err) => {
      messages.value.push({ role: 'char', text: `[错误] ${err}` })
      streamText.value = ''
      streaming.value = false
    })
  } catch {
    streaming.value = false
  }
}

function scrollBottom() {
  if (chatArea.value) {
    chatArea.value.scrollTop = chatArea.value.scrollHeight
  }
}

onMounted(() => {
  loadCharacters()
  loadWorkTitle()
})
</script>

<style scoped>
.rp-container { display: flex; flex-direction: column; height: calc(100vh - 80px); max-width: 900px; margin: 0 auto; padding: 0.75rem 1rem; }
.rp-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; flex-shrink: 0; }
.rp-work-info { flex: 1; }
.rp-work-title { font-family: var(--font-serif); font-size: 1.1rem; font-weight: 600; color: var(--text-primary); }
.rp-label { font-size: 0.75rem; color: var(--accent-primary); margin-left: 0.5rem; }
.rp-actions { display: flex; gap: 0.5rem; }

.rp-body { flex: 1; display: flex; flex-direction: column; min-height: 0; }

/* 角色卡片栏 */
.rp-char-bar {
  display: flex; gap: 0.5rem; padding: 0.5rem 0;
  overflow-x: auto; flex-shrink: 0;
  border-bottom: 1px solid var(--border-glass);
}
.char-card {
  display: flex; align-items: center; gap: 0.4rem;
  padding: 0.4rem 0.75rem; border-radius: 20px;
  cursor: pointer; transition: all 0.2s; flex-shrink: 0;
  border: 1px solid transparent;
}
.char-card:hover { background: rgba(196, 163, 90, 0.06); }
.char-card.active { background: rgba(196, 163, 90, 0.12); border-color: rgba(196, 163, 90, 0.3); }
.char-avatar {
  width: 28px; height: 28px; border-radius: 50%;
  background: var(--accent-purple, #8b5cf6); color: white;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.75rem; font-weight: 700;
}
.char-name { font-size: 0.82rem; color: var(--text-secondary); }
.char-card.active .char-name { color: var(--text-primary); }
.char-del {
  background: none; border: none; color: var(--text-muted); cursor: pointer;
  font-size: 0.85rem; padding: 0 2px; opacity: 0;
  transition: opacity 0.2s;
}
.char-card:hover .char-del { opacity: 1; }
.char-del:hover { color: #e55; }
.add-card {
  border: 1px dashed rgba(196, 163, 90, 0.2);
  color: var(--text-muted); font-size: 1.1rem;
}
.add-card:hover { border-color: rgba(196, 163, 90, 0.4); color: var(--accent-primary); }

/* 聊天区 */
.rp-chat-area {
  flex: 1; overflow-y: auto; padding: 1rem 0;
  min-height: 0;
}
.rp-empty { text-align: center; padding: 3rem; color: var(--text-muted); }
.rp-empty p { margin: 0.3rem 0; }
.char-info-banner {
  text-align: center; padding: 0.5rem; margin-bottom: 1rem;
  font-size: 0.82rem; color: var(--text-muted);
  border-bottom: 1px solid var(--border-glass);
}

/* 消息 */
.rp-msg { display: flex; gap: 0.5rem; margin-bottom: 1rem; align-items: flex-start; }
.rp-msg.user { flex-direction: row-reverse; }
.msg-avatar {
  width: 32px; height: 32px; border-radius: 50%; flex-shrink: 0;
  background: var(--accent-purple, #8b5cf6); color: white;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.8rem; font-weight: 700;
}
.user-avatar { background: var(--accent-primary); }
.msg-bubble { max-width: 70%; }
.msg-name { font-size: 0.72rem; color: var(--accent-primary); margin-bottom: 2px; font-weight: 600; }
.msg-text {
  padding: 0.6rem 1rem; border-radius: 12px;
  font-size: 0.9rem; line-height: 1.6;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.rp-msg.user .msg-text {
  background: rgba(196, 163, 90, 0.12);
  border-color: rgba(196, 163, 90, 0.2);
}
.cursor { animation: blink 0.8s infinite; }
@keyframes blink { 50% { opacity: 0; } }

/* 输入区 */
.rp-input-area {
  display: flex; gap: 0.5rem; padding: 0.75rem 0;
  border-top: 1px solid var(--border-glass); flex-shrink: 0;
}
.rp-input-area textarea {
  flex: 1; resize: none; padding: 0.6rem;
  font-size: 0.9rem; line-height: 1.5;
  background: transparent; color: var(--text-primary);
  border: 1px solid var(--border-glass); border-radius: 8px;
  outline: none;
}
.rp-input-area textarea:focus { border-color: var(--accent-primary); }

/* 弹窗 */
.modal-overlay {
  position: fixed; inset: 0; z-index: 300;
  background: rgba(0, 0, 0, 0.5);
  display: flex; align-items: center; justify-content: center;
}
.modal {
  width: 450px; padding: 1.5rem;
  border-radius: 16px;
  background: rgba(20, 20, 35, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(196, 163, 90, 0.12);
}
.modal h3 { margin: 0 0 1rem; font-family: var(--font-serif); }
.form-group { margin-bottom: 0.75rem; }
.form-group label { display: block; font-size: 0.78rem; color: var(--text-muted); margin-bottom: 4px; }
.form-group input, .form-group textarea {
  width: 100%; padding: 0.5rem; font-size: 0.85rem;
  background: transparent; color: var(--text-primary);
  border: 1px solid var(--border-glass); border-radius: 6px;
  outline: none; box-sizing: border-box;
}
.form-group input:focus, .form-group textarea:focus { border-color: var(--accent-primary); }
.modal-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1rem; }
.muted { color: var(--text-muted); font-size: 0.82rem; }
</style>
