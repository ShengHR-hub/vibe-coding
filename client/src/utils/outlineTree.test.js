import { describe, it, expect } from 'vitest'
import { outlineToText, parseOutlineTree, hasVolumeMark } from './outlineTree.js'

describe('outlineToText（大纲树 → 可编辑文本）', () => {
  it('空树 → 空串', () => {
    expect(outlineToText([])).toBe('')
    expect(outlineToText(null)).toBe('')
  })

  it('卷 + 章 → 每卷一行标题，章为「标题：beats」子行', () => {
    const tree = [
      {
        kind: 'part', title: '第一卷 入玄门', children: [
          { kind: 'chapter', title: '第一章 上山', beats: '少年拜入师门', hook: '' },
          { kind: 'chapter', title: '第二章 遇险', beats: '遭遇山匪', hook: '' },
        ],
      },
      {
        kind: 'part', title: '第二卷 下山', children: [
          { kind: 'chapter', title: '第三章 江湖', beats: '初涉江湖', hook: '' },
        ],
      },
    ]
    const text = outlineToText(tree)
    expect(text).toBe('第一卷 入玄门\n第一章 上山：少年拜入师门\n第二章 遇险：遭遇山匪\n第二卷 下山\n第三章 江湖：初涉江湖')
  })

  it('无标题的章 → 只有 beats', () => {
    expect(outlineToText([
      { kind: 'part', title: '第一卷', children: [{ kind: 'chapter', title: '', beats: '只有剧情' }] },
    ])).toBe('第一卷\n只有剧情')
  })
})

describe('parseOutlineTree（可编辑文本 → 大纲树）', () => {
  it('空/空行 → 兜底「全卷」', () => {
    expect(parseOutlineTree('')).toEqual([{ kind: 'part', title: '全卷', children: [] }])
    expect(parseOutlineTree('   \n  ')).toEqual([{ kind: 'part', title: '全卷', children: [] }])
  })

  it('「第X卷 / 卷X」行起新 part，其下缩进行为章节', () => {
    const tree = parseOutlineTree('第一卷 入玄门\n第一章 上山：少年拜入师门\n第二章 遇险：遭遇山匪\n第二卷 下山')
    expect(tree).toEqual([
      {
        kind: 'part', title: '第一卷 入玄门', children: [
          { kind: 'chapter', title: '第一章 上山', beats: '少年拜入师门', hook: '' },
          { kind: 'chapter', title: '第二章 遇险', beats: '遭遇山匪', hook: '' },
        ],
      },
      { kind: 'part', title: '第二卷 下山', children: [] },
    ])
  })

  it('多行 beats 超过 200 字截断，标题超过 40 字截断', () => {
    const tree = parseOutlineTree('第一卷\n第一章：' + '很'.repeat(300))
    expect(tree[0].children[0].beats.length).toBe(200)
    const longTitle = parseOutlineTree('第一卷\n' + '章'.repeat(50) + '：正文')
    expect(longTitle[0].children[0].title.length).toBe(40)
  })

  it('无卷标记的普通行 → 直接成为 part', () => {
    const tree = parseOutlineTree('一个模糊的开局想法\n另一个')
    expect(tree).toEqual([
      { kind: 'part', title: '一个模糊的开局想法', children: [] },
      { kind: 'part', title: '另一个', children: [] },
    ])
  })

  it('互逆：树 → 文本 → 树 保持结构', () => {
    const original = [
      {
        kind: 'part', title: '第一卷 起点', children: [
          { kind: 'chapter', title: '第一章 开始', beats: '登场', hook: '' },
        ],
      },
    ]
    const text = outlineToText(original)
    expect(parseOutlineTree(text)).toEqual(original)
  })
})

describe('hasVolumeMark（卷标记提示）', () => {
  it('含卷标记 → true', () => {
    expect(hasVolumeMark('第一卷 入玄门\n随便')).toBe(true)
    expect(hasVolumeMark('卷三 风云')).toBe(true)
  })
  it('不含 → false', () => {
    expect(hasVolumeMark('就一句话')).toBe(false)
    expect(hasVolumeMark('')).toBe(false)
  })
})