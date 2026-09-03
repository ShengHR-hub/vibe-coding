import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  escHtml,
  renderBr,
  renderParagraphs,
  renderParagraphBlock,
  renderMarkdownChat,
  renderMarkdownBlock,
  renderParagraphBold,
} from './render.js'

test('escHtml 转义 & < >（保留引号，与旧实现一致）', () => {
  assert.equal(escHtml('<b>&</b>'), '&lt;b&gt;&amp;&lt;/b&gt;')
  assert.equal(escHtml(`a"b'c`), `a"b'c`)
  assert.equal(escHtml(null), '')
  assert.equal(escHtml(undefined), '')
})

test('renderBr：换行转 <br>，无 <p> 包裹', () => {
  assert.equal(renderBr('一\n二'), '一<br>二')
  assert.equal(renderBr(''), '')
})

test('renderParagraphs：空行分段，不包外层 <p>', () => {
  assert.equal(renderParagraphs('a\n\nb\nc'), 'a</p><p>b<br>c')
  assert.equal(renderParagraphs(''), '')
})

test('renderParagraphBlock：分段并包一层 <p>', () => {
  assert.equal(renderParagraphBlock('a\n\nb\nc'), '<p>a</p><p>b<br>c</p>')
})

test('renderMarkdownChat：粗体/斜体/分段（不包外层 <p>）', () => {
  assert.equal(
    renderMarkdownChat('**粗** *斜*\n\nx'),
    '<strong>粗</strong> <em>斜</em></p><p>x'
  )
})

test('renderMarkdownBlock：标题/粗斜/行内码/分段并包 <p>', () => {
  assert.equal(
    renderMarkdownBlock('# 标题\n\n`code` **b**'),
    '<p><h1>标题</h1></p><p><code>code</code> <strong>b</strong></p>'
  )
})

test('XSS 向量：所有渲染函数都不输出裸标签', () => {
  const payload = '<img src=x onerror=alert(1)><script>evil()</script>'
  const outputs = [
    escHtml(payload),
    renderBr(payload),
    renderParagraphs(payload),
    renderParagraphBlock(payload),
    renderMarkdownChat(payload),
    renderMarkdownBlock(payload),
  ]
  for (const out of outputs) {
    assert.ok(!/<img|<script/.test(out), `裸标签泄漏: ${out}`)
    assert.ok(out.includes('&lt;img'), '应保留转义后的 <img')
  }
})

test('renderParagraphBold：转义 + 加粗 + 分段包 <p>（W1d AI 面板渲染）', () => {
  assert.equal(
    renderParagraphBold('**粗**\n\n第二段\n续行'),
    '<p><strong>粗</strong></p><p>第二段<br>续行</p>'
  )
  // XSS：HTML 被转义，仅 ** 加粗生效
  const out = renderParagraphBold('<img src=x onerror=alert(1)> **好**')
  assert.ok(!/<img/.test(out))
  assert.ok(out.includes('&lt;img'))
  assert.ok(out.includes('<strong>好</strong>'))
  assert.equal(renderParagraphBold(''), '')
})

test('非法输入不抛异常', () => {
  assert.equal(renderMarkdownBlock(), '')
  assert.equal(renderMarkdownChat(null), '')
  assert.equal(renderParagraphBlock(undefined), '')
})
