<template>
  <div class="panel chat-panel">
    <!-- 会话工具栏 + 历史列表 -->
    <div class="chat-toolbar">
      <button class="tb-btn" @click="toggleHistory" :disabled="streaming">
        {{ historyOpen ? '收起历史 ▾' : `历史会话${sessions.length ? ` (${sessions.length})` : ''}` }}
      </button>
      <button class="tb-btn tb-new" @click="newConversation" :disabled="streaming">＋ 新会话</button>
    </div>
    <div class="chat-history" v-if="historyOpen">
      <div class="empty-state" v-if="sessions.length === 0">
        <p class="empty-hint">暂无历史会话</p>
      </div>
      <div v-for="s in sessions" :key="s.session_key" class="history-item">
        <div class="history-main" @click="loadConversation(s.session_key)">
          <span class="history-preview">{{ s.preview || '（空会话）' }}</span>
          <span class="history-meta">{{ s.msg_count }} 条 · {{ s.updated_at }}</span>
        </div>
        <button class="tb-btn tb-del" @click.stop="removeSession(s.session_key)">删除</button>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="chat-messages" ref="messagesRef">
      <div class="chat-welcome" v-if="messages.length === 0">
        <span class="welcome-icon"> </span>
        <p class="welcome-title">灵感对话</p>
        <p class="welcome-hint">和 AI 聊聊你的故事想法，获取灵感和建议</p>
        <div class="quick-starters">
          <button v-for="s in starters" :key="s" class="starter-btn" @click="sendMessage(s)">{{ s }}</button>
        </div>
      </div>

      <div v-for="(msg, idx) in messages" :key="idx" class="chat-msg" :class="msg.role">
        <div class="msg-avatar">{{ msg.role === 'user' ? '你' : 'AI' }}</div>
        <div class="msg-bubble">
          <div class="msg-text" v-if="msg.role === 'user'">{{ msg.content }}</div>
          <div class="msg-text markdown-body" v-else v-html="renderMarkdown(msg.content)"></div>
          <div class="msg-actions" v-if="msg.role === 'assistant' && msg.content && !msg.loading">
            <button class="action-btn" @click="$emit('insert', msg.content)">插入编辑器</button>
            <button class="action-btn" @click="copyText(msg.content)">复制</button>
          </div>
        </div>
      </div>

      <!-- 流式输出中的消息 -->
      <div v-if="streaming" class="chat-msg assistant">
        <div class="msg-avatar">AI</div>
        <div class="msg-bubble">
          <div class="msg-text markdown-body">{{ streamBuffer }}<span class="cursor-blink">|</span></div>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="chat-input-area">
      <textarea
        ref="inputRef"
        v-model="inputText"
        placeholder="聊聊你的故事想法..."
        rows="2"
        @keydown.enter.exact.prevent="onEnter"
        :disabled="streaming"
      ></textarea>
      <button class="send-btn" @click="sendMessage()" :disabled="!inputText.trim() || streaming">
        {{ streaming ? 'AI 思考中...' : '发送' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { api } from '../../api/index.js'
import { renderMarkdownChat } from '../../utils/render.js'

defineEmits(['insert'])

const messages = ref([])
const inputText = ref('')
const streaming = ref(false)
const streamBuffer = ref('')
const messagesRef = ref(null)
const inputRef = ref(null)
const sessionKey = ref('')
const sessions = ref([])
const historyOpen = ref(false)

function genSessionKey() {
  return 'c' + Date.now().toString(36) + '-' + Math.random().toString(36).slice(2, 10)
}

async function loadSessions() {
  const res = await api.get('/api/write/conversations')
  if (res.code === 0) sessions.value = res.data.sessions || []
}

function toggleHistory() {
  historyOpen.value = !historyOpen.value
  if (historyOpen.value) loadSessions()
}

function newConversation() {
  if (streaming.value) return
  messages.value = []
  streamBuffer.value = ''
  sessionKey.value = genSessionKey()
  historyOpen.value = false
  scrollToBottom()
}

async function loadConversation(key) {
  if (streaming.value || !key) return
  const res = await api.get(`/api/write/conversations/${key}`)
  if (res.code === 0) {
    messages.value = (res.data.messages || []).map(m => ({ role: m.role, content: m.content }))
    sessionKey.value = key
    historyOpen.value = false
    scrollToBottom()
  }
}

async function removeSession(key) {
  if (streaming.value) return
  if (!window.confirm('删除该历史会话？')) return
  const res = await api.delete(`/api/write/conversations/${key}`)
  if (res.code === 0) {
    sessions.value = sessions.value.filter(s => s.session_key !== key)
    if (key === sessionKey.value) newConversation()
  }
}

const starters = [
  '帮我构思一个奇幻故事',
  '我想写一个爱情故事',
  '如何塑造一个反派角色',
  '故事开头怎么写吸引人',
]

function renderMarkdown(text) {
  return renderMarkdownChat(text)
}

function scrollToBottom() {
  nextTick(() => {
    const el = messagesRef.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function onEnter(e) {
  if (e.shiftKey) return // Allow shift+enter for newline
  sendMessage()
}

async function sendMessage(text) {
  const content = (text || inputText.value).trim()
  if (!content || streaming.value) return

  // 首次发言生成客户端会话 key，保证同一次对话落库在同一 session 下
  if (!sessionKey.value) sessionKey.value = genSessionKey()

  // Add user message
  messages.value.push({ role: 'user', content })
  inputText.value = ''
  scrollToBottom()

  // Build history for API
  const history = messages.value
    .slice(0, -1) // Exclude the just-added message
    .filter(m => m.content)
    .map(m => ({ role: m.role, content: m.content }))

  streaming.value = true
  streamBuffer.value = ''

  const currentSessionKey = sessionKey.value

  api.stream('/api/write/chat',
    { message: content, history, session_key: currentSessionKey },
    (chunk) => {
      try {
        const data = JSON.parse(chunk)
        if (data.session_key) sessionKey.value = data.session_key
        if (data.chunk) {
          streamBuffer.value += data.chunk
          scrollToBottom()
        }
      } catch {}
    },
    () => {
      streaming.value = false
      if (streamBuffer.value) {
        messages.value.push({ role: 'assistant', content: streamBuffer.value })
        streamBuffer.value = ''
        scrollToBottom()
      }
    },
    (err) => {
      streaming.value = false
      messages.value.push({ role: 'assistant', content: ` ${err}` })
      streamBuffer.value = ''
      scrollToBottom()
    }
  )
}

async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text)
  } catch {}
}

onMounted(() => { loadSessions() })
</script>

<style scoped>
.chat-panel {
  display: flex; flex-direction: column; height: 100%;
  padding: 0; gap: 0;
}

/* 会话工具栏与历史 */
.chat-toolbar {
  display: flex; gap: 6px; padding: 0.5rem 0.75rem 0;
  flex-shrink: 0;
}
.tb-btn {
  font-size: 0.72rem; padding: 3px 10px;
  border-radius: var(--radius-sm);
  background: rgba(196, 163, 90, 0.06);
  border: 1px solid rgba(196, 163, 90, 0.12);
  color: var(--text-muted);
  cursor: pointer; transition: all 0.2s;
}
.tb-btn:hover:not(:disabled) { color: var(--accent-primary); border-color: rgba(196,163,90,0.3); }
.tb-btn:disabled { opacity: 0.45; cursor: not-allowed; }
.tb-new { color: var(--accent-primary); }
.tb-del { color: #e0716b; }
.chat-history {
  margin: 0.4rem 0.75rem 0; padding: 0.4rem;
  border: 1px solid rgba(196, 163, 90, 0.12);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.02);
  max-height: 180px; overflow-y: auto;
  flex-shrink: 0;
}
.history-item {
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px; padding: 6px 8px; border-radius: 6px;
}
.history-item:hover { background: rgba(196, 163, 90, 0.06); }
.history-main { flex: 1; min-width: 0; cursor: pointer; }
.history-preview {
  display: block; font-size: 0.8rem; color: var(--text-primary);
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.history-meta { display: block; font-size: 0.68rem; color: var(--text-muted); margin-top: 1px; }
.chat-history .empty-state { padding: 0.6rem 0; text-align: center; }
.chat-history .empty-hint { font-size: 0.75rem; color: var(--text-muted); }

/* 消息列表 */
.chat-messages {
  flex: 1; overflow-y: auto; padding: 0.75rem;
  display: flex; flex-direction: column; gap: 0.75rem;
}

/* 欢迎页 */
.chat-welcome {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; text-align: center;
  padding: 2rem 1rem; flex: 1;
}
.welcome-icon { font-size: 2.5rem; margin-bottom: 0.75rem; }
.welcome-title {
  font-family: var(--font-serif); font-size: 1.1rem;
  color: var(--text-primary); margin-bottom: 0.4rem;
}
.welcome-hint {
  font-size: 0.82rem; color: var(--text-muted);
  margin-bottom: 1.2rem; line-height: 1.5;
}
.quick-starters {
  display: flex; flex-wrap: wrap; gap: 6px; justify-content: center;
}
.starter-btn {
  font-size: 0.75rem; padding: 5px 12px;
  border-radius: var(--radius-full);
  background: rgba(196, 163, 90, 0.06);
  border: 1px solid rgba(196, 163, 90, 0.12);
  color: var(--text-secondary);
  cursor: pointer; transition: all 0.2s;
}
.starter-btn:hover {
  background: rgba(196, 163, 90, 0.12);
  border-color: rgba(196, 163, 90, 0.3);
  color: var(--accent-primary);
}

/* 消息气泡 */
.chat-msg {
  display: flex; gap: 8px;
  max-width: 100%;
}
.chat-msg.user { flex-direction: row-reverse; }

.msg-avatar {
  width: 28px; height: 28px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem; font-weight: 700; flex-shrink: 0;
}
.chat-msg.user .msg-avatar {
  background: var(--accent-primary); color: var(--bg-primary);
}
.chat-msg.assistant .msg-avatar {
  background: rgba(100, 180, 255, 0.15); color: #6eb4ff;
}

.msg-bubble {
  max-width: 85%; min-width: 0;
}
.chat-msg.user .msg-bubble {
  text-align: right;
}

.msg-text {
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 0.85rem; line-height: 1.6;
  word-break: break-word;
}
.chat-msg.user .msg-text {
  background: rgba(196, 163, 90, 0.12);
  border: 1px solid rgba(196, 163, 90, 0.15);
  color: var(--text-primary);
  border-top-right-radius: 4px;
}
.chat-msg.assistant .msg-text {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(196, 163, 90, 0.06);
  color: var(--text-secondary);
  border-top-left-radius: 4px;
}

.msg-actions {
  display: flex; gap: 6px; margin-top: 4px;
}
.chat-msg.user .msg-actions { justify-content: flex-end; }
.action-btn {
  font-size: 0.7rem; padding: 2px 8px;
  border-radius: var(--radius-sm);
  background: rgba(196, 163, 90, 0.06);
  border: 1px solid rgba(196, 163, 90, 0.1);
  color: var(--text-muted);
  cursor: pointer; transition: all 0.2s;
}
.action-btn:hover {
  color: var(--accent-primary);
  border-color: rgba(196, 163, 90, 0.3);
}

.cursor-blink {
  animation: blink 0.8s infinite;
  color: var(--accent-primary);
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* 输入区域 */
.chat-input-area {
  padding: 0.5rem; border-top: 1px solid rgba(196, 163, 90, 0.08);
  display: flex; gap: 0.5rem; align-items: flex-end;
  background: rgba(255, 255, 255, 0.02);
}
.chat-input-area textarea {
  flex: 1; resize: none; padding: 8px 10px;
  font-size: 0.85rem; line-height: 1.5;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(196, 163, 90, 0.08);
  color: var(--text-primary);
}
.chat-input-area textarea:focus {
  border-color: rgba(196, 163, 90, 0.2);
  outline: none;
}
.chat-input-area textarea::placeholder { color: var(--text-muted); }

.send-btn {
  padding: 8px 16px; font-size: 0.82rem; font-weight: 600;
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(196,163,90,0.2), rgba(196,163,90,0.1));
  border: 1px solid rgba(196,163,90,0.2);
  color: var(--accent-primary);
  cursor: pointer; transition: all 0.25s;
  white-space: nowrap;
}
.send-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, rgba(196,163,90,0.3), rgba(196,163,90,0.15));
  box-shadow: 0 0 12px rgba(196,163,90,0.15);
}
.send-btn:disabled {
  opacity: 0.5; cursor: not-allowed;
}
</style>
