/**
 * 使用说明弹窗「今天不再弹出」——纯函数（可单测）
 * P6-B7：本地时区日期（toISOString 是 UTC 会串天）；auto 通道查「今天不再弹」
 */

export const GUIDE_KEY = 'inkstone_guide_dismiss'

/** 本地时区日期 YYYY-MM-DD（非 UTC） */
export function localTodayStr(date = new Date()) {
  const mm = String(date.getMonth() + 1).padStart(2, '0')
  const dd = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${mm}-${dd}`
}

/** 今天是否已被「不再弹出」压掉 */
export function guideDismissedToday(storage = localStorage, date = new Date()) {
  return storage.getItem(GUIDE_KEY) === localTodayStr(date)
}

/**
 * 自动弹出通道：auto=true 且今天已压掉 → 不弹（返回 false）；
 * 手动打开（头像菜单）始终弹
 */
export function shouldAutoOpen(auto, dismissedToday) {
  return !(auto && dismissedToday)
}