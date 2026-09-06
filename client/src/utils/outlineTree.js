/**
 * 大纲树 ↔ 可编辑文本——纯函数（可单测）
 * 树结构：[{ kind:'part', title, children:[{ kind:'chapter', title, beats, hook }] }]，
 * 与 OutlineTreePanel / WorkshopPanel 同构（P6-B3）
 */

/** 卷标记：阿拉伯「第1卷/1卷」或汉字「第一卷/卷一/卷三」 */
const VOLUME_RE = /第?\s*(?:\d+|[一二三四五六七八九十百]+)\s*卷|卷[一二三四五六七八九十百]+/

/** 大纲树 → 可编辑文本（part.title 行 + 卷内子行） */
export function outlineToText(tree) {
  const lines = []
  for (const part of tree || []) {
    lines.push(part.title || '')
    for (const ch of part.children || []) {
      lines.push((ch.title ? ch.title + '：' : '') + (ch.beats || ch.hook || ''))
    }
  }
  return lines.join('\n').trim()
}

/** 可编辑文本 → 大纲树 */
export function parseOutlineTree(text) {
  const lines = (text || '').split('\n').map(l => l.trim()).filter(Boolean)
  const parts = []
  let cur = null
  for (const line of lines) {
    if (VOLUME_RE.test(line) && line.length <= 30) {
      cur = { kind: 'part', title: line.replace(/^[【\[]|[\】\]]$/g, '').slice(0, 60), children: [] }
      parts.push(cur)
    } else if (cur) {
      const sep = line.indexOf('：')
      const title = sep > 0 ? line.slice(0, sep).slice(0, 40) : ''
      const beats = sep > 0 ? line.slice(sep + 1) : line
      cur.children.push({ kind: 'chapter', title, beats: beats.slice(0, 200), hook: '' })
    } else {
      parts.push({ kind: 'part', title: line.slice(0, 60), children: [] })
    }
  }
  return parts.length ? parts : [{ kind: 'part', title: '全卷', children: [] }]
}

/** 文本里是否有卷标记（UI 提示用） */
export function hasVolumeMark(text) {
  return (text || '').split('\n').some(l => VOLUME_RE.test(l))
}