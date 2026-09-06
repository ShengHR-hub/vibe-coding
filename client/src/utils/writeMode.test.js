import { describe, it, expect, beforeEach } from 'vitest'
import {
  rememberWriteMode,
  readWriteMode,
  resolveWriteTarget,
  computeNavActive,
} from './writeMode.js'

/** 每次用例给独立 storage（内存版，仅实现 getItem/setItem） */
function makeStorage(seed = {}) {
  const map = new Map(Object.entries(seed))
  return {
    getItem: (k) => (map.has(k) ? map.get(k) : null),
    setItem: (k, v) => map.set(k, String(v)),
    removeItem: (k) => map.delete(k),
  }
}

describe('rememberWriteMode / readWriteMode（路由守卫记忆写作模式）', () => {
  let storage
  beforeEach(() => { storage = makeStorage() })

  it('进入老手台记 pro', () => {
    rememberWriteMode('/write', storage)
    expect(readWriteMode(storage)).toBe('pro')
  })
  it('进入新手页记 new', () => {
    rememberWriteMode('/write/new', storage)
    expect(readWriteMode(storage)).toBe('new')
  })
  it('进入纯净页记 plain', () => {
    rememberWriteMode('/write/plain', storage)
    expect(readWriteMode(storage)).toBe('plain')
  })
  it('非写作路径不写入', () => {
    rememberWriteMode('/inspire', storage)
    expect(readWriteMode(storage)).toBe('')
  })
  it('空路径不写入不报错', () => {
    rememberWriteMode('', storage)
    expect(readWriteMode(storage)).toBe('')
  })
})

describe('resolveWriteTarget（导航「写作」按记忆跳回）', () => {
  it('new → 新手页', () => expect(resolveWriteTarget('new')).toBe('/write/new'))
  it('plain → 纯净页', () => expect(resolveWriteTarget('plain')).toBe('/write/plain'))
  it('pro → 老手台', () => expect(resolveWriteTarget('pro')).toBe('/write'))
  it('无记忆 → 分流页自选', () => {
    expect(resolveWriteTarget('')).toBe('/start')
    expect(resolveWriteTarget(null)).toBe('/start')
  })
})

describe('computeNavActive（导航高亮路径映射）', () => {
  it('写作类路径全部点亮 write', () => {
    expect(computeNavActive('/write')).toBe('write')
    expect(computeNavActive('/write/new')).toBe('write')
    expect(computeNavActive('/write/plain')).toBe('write')
    expect(computeNavActive('/start')).toBe('write')
    // 带子路径也点亮（如 ?query 场景按 path 处理）
    expect(computeNavActive('/write')).toBe('write')
  })
  it('其它导航项各自点亮', () => {
    expect(computeNavActive('/inspire')).toBe('inspire')
    expect(computeNavActive('/explore')).toBe('explore')
    expect(computeNavActive('/daily')).toBe('daily')
    expect(computeNavActive('/rankings')).toBe('rankings')
    expect(computeNavActive('/challenges')).toBe('challenges')
  })
  it('无关路径不高亮', () => {
    expect(computeNavActive('/works')).toBe('')
    expect(computeNavActive('/')).toBe('')
  })
})