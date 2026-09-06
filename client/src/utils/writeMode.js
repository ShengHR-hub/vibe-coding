/**
 * 写作模式记忆 + 导航高亮——纯函数（可单测）
 * P6-B7：导航「写作」按用户最近使用的写作系统跳回；高亮按路径前缀映射
 */

/** 写出写作模式记忆（路由守卫进入写作页时调用） */
export function rememberWriteMode(path, storage = localStorage) {
  if (!path) return
  if (path === '/write') storage.setItem('inkstone_write_mode', 'pro')
  else if (path === '/write/new') storage.setItem('inkstone_write_mode', 'new')
  else if (path === '/write/plain') storage.setItem('inkstone_write_mode', 'plain')
}

/** 读写作模式记忆 */
export function readWriteMode(storage = localStorage) {
  return storage.getItem('inkstone_write_mode') || ''
}

/**
 * 导航「写作」的跳转目标：
 * 按最近使用的模式回对应系统；无记忆（新用户）回分流页 /start 自选
 */
export function resolveWriteTarget(mode) {
  if (mode === 'new') return '/write/new'
  if (mode === 'plain') return '/write/plain'
  if (mode === 'pro') return '/write'
  return '/start'
}

/**
 * 导航高亮映射：哪些路径点亮「写作」及其它导航项。
 * vue-router 的 router-link-active 只认嵌套路由，平级路由需手动映射（P6-B6）
 */
export function computeNavActive(path) {
  if (path === '/write' || path.startsWith('/write/') || path === '/start') return 'write'
  if (path.startsWith('/inspire')) return 'inspire'
  if (path.startsWith('/explore')) return 'explore'
  if (path.startsWith('/daily')) return 'daily'
  if (path.startsWith('/rankings')) return 'rankings'
  if (path.startsWith('/challenges')) return 'challenges'
  return ''
}