const BASE = ''

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
      return { code: resp.status, data: null, msg: data.msg || `请求失败 (${resp.status})` }
    }
    return data
  } catch {
    return { code: -1, data: null, msg: '网络错误，请检查连接' }
  }
}

export const api = {
  get: (url) => request(url),
  post: (url, body) => request(url, { method: 'POST', body }),
  put: (url, body) => request(url, { method: 'PUT', body }),
  delete: (url) => request(url, { method: 'DELETE' }),

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
    } catch {
      return { code: -1, data: null, msg: '网络错误，请检查连接' }
    }
  },

  stream(url, body, onChunk, onDone, onError) {
    fetch(BASE + url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(body)
    }).then(async resp => {
      if (!resp.ok) {
        const err = await resp.json().catch(() => ({ msg: `请求失败 (${resp.status})` }))
        if (onError) onError(err.msg || '服务器错误')
        return
      }
      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()
        for (const line of lines) {
          if (line.startsWith('data:')) {
            const chunk = line.slice(5).trim()
            if (chunk === '[DONE]') break
            if (onChunk) onChunk(chunk)
          }
        }
      }
      if (onDone) onDone()
    }).catch(() => {
      if (onError) onError('网络错误，请检查连接')
    })
  }
}
