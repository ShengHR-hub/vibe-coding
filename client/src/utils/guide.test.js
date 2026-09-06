import { describe, it, expect } from 'vitest'
import { GUIDE_KEY, localTodayStr, guideDismissedToday, shouldAutoOpen } from './guide.js'

function makeStorage(seed = {}) {
  const map = new Map(Object.entries(seed))
  return {
    getItem: (k) => (map.has(k) ? map.get(k) : null),
    setItem: (k, v) => map.set(k, String(v)),
    removeItem: (k) => map.delete(k),
  }
}

const aDay = new Date(2026, 8, 6, 12, 0, 0) // 2026-09-06 本地正午

describe('localTodayStr（本地时区日期，非 UTC）', () => {
  it('正午取当天', () => {
    expect(localTodayStr(aDay)).toBe('2026-09-06')
  })
  it('深夜本地日期仍是当天（UTC 会串天）', () => {
    // 本地 09-06 23:30 → UTC 已是 09-06 15:30，但若是 09-07 00:30 → UTC 09-06 16:30
    const late = new Date(2026, 8, 7, 0, 30, 0) // 本地 09-07 00:30
    expect(localTodayStr(late)).toBe('2026-09-07')
  })
  it('月份补零', () => {
    expect(localTodayStr(new Date(2026, 0, 5))).toBe('2026-01-05')
  })
})

describe('guideDismissedToday / shouldAutoOpen（今天不再弹）', () => {
  it('今天压掉→dismissed 为真', () => {
    const s = makeStorage({ [GUIDE_KEY]: '2026-09-06' })
    expect(guideDismissedToday(s, aDay)).toBe(true)
  })
  it('昨天压掉→今天不算', () => {
    const s = makeStorage({ [GUIDE_KEY]: '2026-09-05' })
    expect(guideDismissedToday(s, aDay)).toBe(false)
  })
  it('从未压掉→false', () => {
    expect(guideDismissedToday(makeStorage(), aDay)).toBe(false)
  })
  it('auto 通道 + 今天已压掉 → 不弹', () => {
    expect(shouldAutoOpen(true, true)).toBe(false)
  })
  it('auto 通道 + 今天没压 → 弹', () => {
    expect(shouldAutoOpen(true, false)).toBe(true)
  })
  it('手动打开（非 auto）始终弹，即使今天已压', () => {
    expect(shouldAutoOpen(false, true)).toBe(true)
  })
})