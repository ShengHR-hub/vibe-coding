/**
 * Canvas 2D 分享海报生成器
 * 纯浏览器原生 API，无额外依赖
 */

const W = 750
const H = 1334

// ---- 绘制辅助函数 ----

function roundRect(ctx, x, y, w, h, r) {
  ctx.beginPath()
  ctx.moveTo(x + r, y)
  ctx.lineTo(x + w - r, y)
  ctx.quadraticCurveTo(x + w, y, x + w, y + r)
  ctx.lineTo(x + w, y + h - r)
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h)
  ctx.lineTo(x + r, y + h)
  ctx.quadraticCurveTo(x, y + h, x, y + h - r)
  ctx.lineTo(x, y + r)
  ctx.quadraticCurveTo(x, y, x + r, y)
  ctx.closePath()
}

function wrapText(ctx, text, x, y, maxWidth, lineHeight) {
  const lines = []
  let line = ''
  for (const char of text) {
    const test = line + char
    if (ctx.measureText(test).width > maxWidth && line) {
      lines.push(line)
      line = char
    } else {
      line = test
    }
  }
  if (line) lines.push(line)
  lines.forEach((l, i) => {
    ctx.fillText(l, x, y + i * lineHeight)
  })
  return lines.length
}

function drawGlow(ctx, x, y, r, color) {
  const grad = ctx.createRadialGradient(x, y, 0, x, y, r)
  grad.addColorStop(0, color)
  grad.addColorStop(1, 'transparent')
  ctx.fillStyle = grad
  ctx.fillRect(x - r, y - r, r * 2, r * 2)
}

// ---- 主函数 ----

/**
 * @param {Object} options
 * @param {string} options.title - 作品标题
 * @param {string} options.author - 作者名
 * @param {string} options.type - 类型 (novel/poetry/essay/script)
 * @param {string} options.summary - 简介
 * @param {string} options.content - 正文（取前几句）
 * @param {number} options.wordCount - 字数
 * @param {number} options.likes - 点赞数
 * @param {string} options.tags - 标签（逗号分隔）
 * @returns {Promise<Blob>} PNG blob
 */
export function generatePoster(options) {
  return new Promise((resolve, reject) => {
    const canvas = document.createElement('canvas')
    canvas.width = W
    canvas.height = H
    const ctx = canvas.getContext('2d')

    const {
      title = '未命名作品',
      author = '佚名',
      type = 'novel',
      summary = '',
      content = '',
      wordCount = 0,
      likes = 0,
      tags = '',
    } = options

    // === 背景 ===
    const bgGrad = ctx.createLinearGradient(0, 0, 0, H)
    bgGrad.addColorStop(0, '#0f0f1a')
    bgGrad.addColorStop(0.5, '#141420')
    bgGrad.addColorStop(1, '#1a1520')
    ctx.fillStyle = bgGrad
    ctx.fillRect(0, 0, W, H)

    // 装饰光晕
    drawGlow(ctx, W * 0.2, H * 0.15, 300, 'rgba(196, 163, 90, 0.04)')
    drawGlow(ctx, W * 0.8, H * 0.7, 400, 'rgba(196, 163, 90, 0.03)')
    drawGlow(ctx, W * 0.5, H * 0.45, 250, 'rgba(100, 80, 160, 0.03)')

    // === 顶部品牌 ===
    ctx.fillStyle = 'rgba(196, 163, 90, 0.8)'
    ctx.font = '600 28px "Playfair Display", "Noto Serif SC", serif'
    ctx.textAlign = 'center'
    ctx.fillText('INKSTONE', W / 2, 80)

    ctx.fillStyle = 'rgba(255, 255, 255, 0.3)'
    ctx.font = '14px "Noto Sans SC", sans-serif'
    ctx.fillText('墨  池  ·  AI 智 能 创 作 平 台', W / 2, 110)

    // 金色分割线
    ctx.strokeStyle = 'rgba(196, 163, 90, 0.2)'
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(200, 140)
    ctx.lineTo(W - 200, 140)
    ctx.stroke()

    // === 类型徽章 ===
    const typeMap = { novel: '小说', poetry: '诗歌', essay: '散文', script: '剧本' }
    const typeLabel = typeMap[type] || type
    ctx.font = '13px "Noto Sans SC", sans-serif'
    const badgeW = ctx.measureText(typeLabel).width + 32
    const badgeX = (W - badgeW) / 2
    roundRect(ctx, badgeX, 175, badgeW, 30, 15)
    ctx.fillStyle = 'rgba(196, 163, 90, 0.12)'
    ctx.fill()
    ctx.strokeStyle = 'rgba(196, 163, 90, 0.3)'
    ctx.lineWidth = 1
    ctx.stroke()
    ctx.fillStyle = 'rgba(196, 163, 90, 0.9)'
    ctx.textAlign = 'center'
    ctx.fillText(typeLabel, W / 2, 196)

    // === 标题 ===
    ctx.textAlign = 'center'
    ctx.fillStyle = '#f0ead8'
    ctx.font = '700 48px "STKaiti", "KaiTi", "Noto Serif SC", serif'
    // 长标题自动换行
    if (ctx.measureText(title).width > W - 120) {
      ctx.font = '700 40px "STKaiti", "KaiTi", "Noto Serif SC", serif'
    }
    wrapText(ctx, title, W / 2, 260, W - 120, 60)

    // === 作者 ===
    ctx.fillStyle = 'rgba(255, 255, 255, 0.5)'
    ctx.font = '16px "Noto Sans SC", sans-serif'
    ctx.fillText(`—  ${author}  —`, W / 2, 340)

    // === 简介/精选段落 ===
    const quoteText = summary || content.slice(0, 200)
    if (quoteText) {
      // 半透明卡片背景
      roundRect(ctx, 60, 390, W - 120, 380, 16)
      ctx.fillStyle = 'rgba(255, 255, 255, 0.025)'
      ctx.fill()
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)'
      ctx.lineWidth = 1
      ctx.stroke()

      // 左侧金色竖线
      ctx.fillStyle = 'rgba(196, 163, 90, 0.5)'
      roundRect(ctx, 80, 420, 3, 60, 1.5)
      ctx.fill()

      // 引号
      ctx.fillStyle = 'rgba(196, 163, 90, 0.25)'
      ctx.font = '700 60px "Playfair Display", serif'
      ctx.textAlign = 'left'
      ctx.fillText('"', 95, 460)

      // 正文
      ctx.fillStyle = 'rgba(255, 255, 255, 0.7)'
      ctx.font = '20px "STKaiti", "KaiTi", "Noto Serif SC", serif'
      ctx.textAlign = 'left'
      const lines = wrapText(ctx, quoteText.slice(0, 280), 100, 480, W - 200, 36)

      // 如果有更多内容，加省略号
      if (quoteText.length > 280) {
        ctx.fillStyle = 'rgba(255, 255, 255, 0.3)'
        ctx.fillText('……', 100, 480 + lines * 36)
      }
    }

    // === 标签 ===
    if (tags) {
      const tagList = tags.split(',').map(t => t.trim()).filter(Boolean).slice(0, 4)
      ctx.font = '13px "Noto Sans SC", sans-serif'
      let tagX = 80
      ctx.textAlign = 'left'
      for (const tag of tagList) {
        const tw = ctx.measureText(tag).width + 24
        if (tagX + tw > W - 60) break
        roundRect(ctx, tagX, 800, tw, 26, 13)
        ctx.fillStyle = 'rgba(196, 163, 90, 0.08)'
        ctx.fill()
        ctx.strokeStyle = 'rgba(196, 163, 90, 0.2)'
        ctx.lineWidth = 0.5
        ctx.stroke()
        ctx.fillStyle = 'rgba(196, 163, 90, 0.7)'
        ctx.fillText(tag, tagX + 12, 817)
        tagX += tw + 10
      }
    }

    // === 底部统计 ===
    // 分割线
    ctx.strokeStyle = 'rgba(196, 163, 90, 0.15)'
    ctx.lineWidth = 1
    ctx.beginPath()
    ctx.moveTo(100, 870)
    ctx.lineTo(W - 100, 870)
    ctx.stroke()

    // 统计数字
    ctx.textAlign = 'center'
    ctx.fillStyle = '#c4a35a'
    ctx.font = '700 36px "Playfair Display", serif'
    ctx.fillText(formatNum(wordCount), W / 2 - 120, 930)
    ctx.fillText(formatNum(likes), W / 2 + 120, 930)

    ctx.fillStyle = 'rgba(255, 255, 255, 0.4)'
    ctx.font = '13px "Noto Sans SC", sans-serif'
    ctx.fillText('总字数', W / 2 - 120, 955)
    ctx.fillText('获赞', W / 2 + 120, 955)

    // === 底部品牌条 ===
    roundRect(ctx, 0, H - 120, W, 120, 0)
    ctx.fillStyle = 'rgba(255, 255, 255, 0.02)'
    ctx.fill()

    ctx.fillStyle = 'rgba(255, 255, 255, 0.25)'
    ctx.font = '14px "Noto Sans SC", sans-serif'
    ctx.textAlign = 'center'
    ctx.fillText('长按识别二维码  ·  在墨池阅读完整作品', W / 2, H - 75)

    ctx.fillStyle = 'rgba(196, 163, 90, 0.6)'
    ctx.font = '600 18px "Playfair Display", serif'
    ctx.fillText('inkstone.ai', W / 2, H - 40)

    // === 装饰圆点 ===
    ctx.fillStyle = 'rgba(196, 163, 90, 0.15)'
    for (let i = 0; i < 5; i++) {
      ctx.beginPath()
      ctx.arc(W / 2 - 30 + i * 15, H - 100, 2, 0, Math.PI * 2)
      ctx.fill()
    }

    // 输出
    canvas.toBlob((blob) => {
      if (blob) resolve(blob)
      else reject(new Error('Canvas toBlob returned null'))
    }, 'image/png')
  })
}

function formatNum(n) {
  if (n >= 10000) return (n / 10000).toFixed(1) + 'w'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k'
  return String(n)
}
