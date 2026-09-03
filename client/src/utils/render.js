/**
 * 文本安全渲染工具（M0.S6 统一转义）
 *
 * 约定：任何外部可见文本（用户/AI 内容）一律先转义再拼受控 HTML，禁止直接 v-html 原文。
 * 各函数输出与改造前对应调用点的行为逐字节一致（语义零漂移），便于后续整体加固。
 */

export function escHtml(value) {
  const s = String(value ?? '')
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

/** 转义 + 换行转 <br>（原 RolePlay.renderMsg） */
export function renderBr(text) {
  if (!text) return ''
  return escHtml(text).replace(/\n/g, '<br>')
}

/** 转义 + 空行分段 + 换行转 <br>，不包外层 <p>（原 WorkDetail.renderContent） */
export function renderParagraphs(text) {
  if (!text) return ''
  return escHtml(text).replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>')
}

/** 转义 + 分段 + 包一层 <p>（原 Reader.renderedContent） */
export function renderParagraphBlock(text) {
  if (!text) return ''
  return '<p>' + escHtml(text).replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>') + '</p>'
}

/** 聊天风格轻量 markdown：转义 + 加粗/斜体/分段（原 ChatPanel.renderMarkdown，不包外层 <p>） */
export function renderMarkdownChat(text) {
  if (!text) return ''
  return escHtml(text)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
}

/** 块级 markdown：转义 + 标题/粗斜/行内码 + 分段并包 <p>（原 MarkdownRenderer.renderedHtml） */
export function renderMarkdownBlock(content) {
  if (!content) return ''
  const html = escHtml(content)
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/`(.+?)`/g, '<code>$1</code>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
  return `<p>${html}</p>`
}

/**
 * 加粗 + 分段（W1d：AI 写面板统一安全渲染）。
 * 转义后仅支持 **加粗** 与空行分段/换行，其余 markdown 原样显示（原 DiagnosePanel 语义 + 转义）。
 */
export function renderParagraphBold(text) {
  if (!text) return ''
  const html = escHtml(text)
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>')
  return `<p>${html}</p>`
}
