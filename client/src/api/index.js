const BASE = ''

// Global 401 handler — redirect to login on session expiry
let _on401 = null
export function setUnauthorizedHandler(fn) {
  _on401 = fn
}

async function request(url, options = {}) {
  const config = {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    ...options,
  }
  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body)
  }
  try {
    const resp = await fetch(BASE + url, config)
    const data = await resp.json()
    if (!resp.ok) {
      if (resp.status === 401) {
        if (_on401) _on401()
      }
      return { code: resp.status, data: null, msg: data.msg || `请求失败 (${resp.status})` }
    }
    return data
  } catch (err) {
    console.error('[API Error]', url, err)
    return { code: -1, data: null, msg: '网络错误，请检查连接' }
  }
}

export const api = {
  get: (url) => request(url),
  post: (url, body) => request(url, { method: 'POST', body }),
  put: (url, body) => request(url, { method: 'PUT', body }),
  delete: (url) => request(url, { method: 'DELETE' }),

  async download(url, fallbackName) {
    try {
      const resp = await fetch(BASE + url, { credentials: 'include' })
      if (!resp.ok) return { code: resp.status, msg: '下载失败' }
      const blob = await resp.blob()
      const dispo = resp.headers.get('Content-Disposition') || ''
      const match = dispo.match(/filename\*=UTF-8''(.+?)(?:;|$)/)
      const filename = match ? decodeURIComponent(match[1]) : (fallbackName || 'download')
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(a.href)
      return { code: 0 }
    } catch (err) {
      console.error('[Download Error]', url, err)
      return { code: -1, msg: '网络错误，请检查连接' }
    }
  },

  async upload(file) {
    const formData = new FormData()
    formData.append('file', file)
    try {
      const resp = await fetch(BASE + '/api/users/upload', {
        method: 'POST',
        credentials: 'include',
        body: formData
      })
      return await resp.json()
    } catch (err) {
      console.error('[Upload Error]', err)
      return { code: -1, data: null, msg: '网络错误，请检查连接' }
    }
  },

  stream(url, body, onChunk, onDone, onError, { timeout = 120000 } = {}) {
    const controller = new AbortController()
    let timeoutId = null

    const resetTimeout = () => {
      if (timeoutId) clearTimeout(timeoutId)
      timeoutId = setTimeout(() => {
        controller.abort()
        if (onError) onError('请求超时，请稍后再试')
      }, timeout)
    }

    fetch(BASE + url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(body),
      signal: controller.signal,
    }).then(async resp => {
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ msg: `请求失败 (${resp.status})` }))
        if (onError) onError(err.msg || '服务器错误')
        return
      }
      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let finished = false
      resetTimeout()
      while (!finished) {
        const { done, value } = await reader.read()
        if (done) break
        resetTimeout()
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()
        for (const line of lines) {
          if (line.startsWith('data:')) {
            const chunk = line.slice(5).trim()
            if (chunk === '[DONE]') { finished = true; break }
            if (onChunk) onChunk(chunk)
          }
        }
      }
      if (timeoutId) clearTimeout(timeoutId)
      if (onDone) onDone()
    }).catch(err => {
      if (timeoutId) clearTimeout(timeoutId)
      if (err.name === 'AbortError') return
      if (onError) onError('网络错误，请检查连接')
    })
    return controller
  }
}
