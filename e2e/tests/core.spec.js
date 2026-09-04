// 墨池 E2E —— P4 成书工作流冒烟（Mock AI，零 token）
import { test, expect } from '@playwright/test'

const REAL_AI = process.env.E2E_REAL_AI === '1'
const USER = 'e2e_book'
const PW = 'e2e123456'

function sseBody(chunks) {
  return chunks.map(c => `data: ${JSON.stringify(c)}\n\n`).join('') + 'data: [DONE]\n\n'
}

async function installAiMock(context) {
  if (REAL_AI) return
  await context.route('**/api/write/continue', route =>
    route.fulfill({
      status: 200,
      contentType: 'text/event-stream; charset=utf-8',
      body: sseBody([{ chunk: '【模拟AI】月光落在灯市的青石板上，守灯人缓缓抬头，认出了来人的眼睛。' }]),
    }),
  )
  await context.route('**/api/write/chat', route =>
    route.fulfill({
      status: 200,
      contentType: 'text/event-stream; charset=utf-8',
      body: sseBody([{ chunk: '（模拟AI回复）建议把“灯的来源”留作本章末尾的钩子。', session_key: 'e2e-mock' }]),
    }),
  )
  await context.route('**/api/write/struct', route =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ code: 0, data: { report: '【总体判断】结构平稳，节奏可用；【优先级】先补第一章的钩子。' }, msg: 'success' }),
    }),
  )
}

function watchErrors(page) {
  const errors = []
  page.on('pageerror', e => errors.push('pageerror: ' + e.message))
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()) })
  return errors
}

async function ensureUser(page) {
  await page.goto('/login')
  await page.getByPlaceholder('用户名', { exact: true }).fill(USER)
  await page.getByPlaceholder('密码', { exact: true }).fill(PW)
  await page.getByRole('button', { name: /登\s*录/ }).click()
  try {
    await page.waitForURL(u => !u.pathname.includes('/login'), { timeout: 6000 })
    return
  } catch { /* fallthrough */ }
  await page.goto('/register')
  await page.getByPlaceholder('用户名', { exact: true }).fill(USER)
  await page.getByPlaceholder('密码', { exact: true }).fill(PW)
  await page.getByPlaceholder('确认密码', { exact: true }).fill(PW)
  await page.getByRole('button', { name: /注\s*册/ }).click()
  await page.waitForURL(u => !u.pathname.includes('/register'), { timeout: 10000 })
  await page.goto('/login')
  await page.getByPlaceholder('用户名', { exact: true }).fill(USER)
  await page.getByPlaceholder('密码', { exact: true }).fill(PW)
  await page.getByRole('button', { name: /登\s*录/ }).click()
  await page.waitForURL(u => !u.pathname.includes('/login'), { timeout: 8000 })
}

async function gotoStage(page, label) {
  await page.locator('.wf-stage').filter({ hasText: label }).click()
}

async function gotoTool(page, label) {
  await page.locator('.wf-tool').filter({ hasText: label }).click()
}

test('P4 全流程：立项→大纲→任务卡→续写→结构审校→交付→发布', async ({ page, context }) => {
  const errors = watchErrors(page)
  await installAiMock(context)
  await ensureUser(page)

  // ---- 建书 → 打开写作台（P4：/write?work=ID 打开已有作品） ----
  const body =
    '雨夜，他推开祖屋的门，一股陈旧的墨香扑面而来。' +
    '屋里只有一盏没有点亮的灯，灯芯却像是刚被人剪过。' +
    '他想起外婆说过，故事要从一盏灯讲起。'
  const created = await (await context.request.post('/api/works', { data: { title: 'E2E 成书之书', type: 'novel', summary: '灯与守灯人。', content: body } })).json()
  expect(created.code).toBe(0)
  const workId = created.data.work_id
  await page.goto(`/write?work=${workId}`)
  await expect(page.locator('.work-title')).toHaveValue('E2E 成书之书', { timeout: 20000 })
  await expect(page.getByPlaceholder(/一个少年为解开祖屋/)).toBeVisible({ timeout: 20000 })

  // ---- ① 立项蓝图 ----
  await expect(page.locator('.wf-stage.active')).toContainText('起：定目标')
  await expect(page.locator('.wf-tool.active')).toContainText('立项蓝图')
  await page.getByPlaceholder(/一个少年为解开祖屋/).fill('一个少年为解开祖屋灯的秘密踏上旅程，最终发现光来自每一个被遗忘的人。')
  await page.getByPlaceholder(/喜欢悬疑与家庭温情/).fill('喜欢悬疑与家庭温情的中青年读者')
  await page.locator('input[type=number]').fill('60000')
  await page.locator('input[type=date]').fill('2026-12-31')
  await page.getByRole('button', { name: /保存立项蓝图/ }).click()
  await expect(page.getByText('立项蓝图已保存', { exact: false })).toBeVisible({ timeout: 8000 })

  // ---- ① 大纲规划（卷/章 + beats/钩子） ----
  await gotoTool(page, '大纲规划')
  await page.getByRole('button', { name: '＋ 卷' }).click()
  await page.locator('input[placeholder*="卷 名称"]').fill('第一卷 灯')
  await page.locator('.part').first().getByRole('button', { name: '＋章' }).click()
  await page.locator('.chapter .ch-title').fill('第一章 归来')
  await page.locator('.chapter textarea').fill('主角回到祖屋，发现灯芯像刚被剪过，决定去灯市。')
  await page.locator('.chapter .ch-hook').fill('守灯人是谁？灯又为何在这里？')
  await page.getByRole('button', { name: /保存大纲/ }).click()
  await expect(page.getByText('大纲已保存', { exact: false })).toBeVisible({ timeout: 8000 })

  // ---- ② 本章任务卡 ----
  await gotoStage(page, '承：稳推进')
  await expect(page.locator('.wf-tool.active')).toContainText('本章任务卡')
  await expect(page.getByText('主角回到祖屋', { exact: false })).toBeVisible()
  await expect(page.getByText('守灯人是谁', { exact: false })).toBeVisible()

  // ---- ② 按蓝图续写（Mock） ----
  await page.getByRole('button', { name: /去续写本章/ }).click()
  await expect(page.locator('.wf-tool.active')).toContainText('按蓝图续写')
  await page.getByRole('button', { name: /开始续写/ }).click()
  await expect(page.getByText('【模拟AI】月光落在灯市的青石板上', { exact: false })).toBeVisible({ timeout: 15000 })

  // ---- ③ 结构审校（Mock）/ TODO / 交付 ----
  await gotoStage(page, '合：精收尾')
  await expect(page.locator('.wf-tool.active')).toContainText('结构审校')
  await page.getByRole('button', { name: /生成 AI 结构审校报告/ }).click()
  await expect(page.getByText('【总体判断】结构平稳', { exact: false })).toBeVisible({ timeout: 15000 })

  await gotoTool(page, '[TODO]清单')
  await expect(page.getByText('全书没有遗留', { exact: false })).toBeVisible({ timeout: 8000 })

  await gotoTool(page, '整书交付')
  const dl = page.waitForEvent('download', { timeout: 15000 })
  await page.getByRole('button', { name: /一键导出整书/ }).click()
  const download = await dl
  expect(download.suggestedFilename()).toContain('.txt')

  // ---- 发布（经共享会话 API），供广场详情测试 ----
  const pub = await (await context.request.put(`/api/works/${workId}/status`, { data: { status: 'published' } })).json()
  expect(pub.code).toBe(0)

  expect(errors, '存在 console/pageerror 异常').toEqual([])
})

test('广场 → 公开作品详情页（阅读器已下线）', async ({ page, context }) => {
  const errors = watchErrors(page)
  await installAiMock(context)
  await ensureUser(page)

  await page.goto('/explore')
  await expect(page.getByText('E2E 成书之书', { exact: false }).first()).toBeVisible({ timeout: 20000 })
  await page.getByText('E2E 成书之书', { exact: false }).first().click()
  await page.waitForURL(/\/work\/\d+/, { timeout: 15000 })
  expect(page.url()).not.toContain('/read')

  await expect(page.locator('.work-info')).toBeVisible()
  await expect(page.locator('.chapter-list')).toContainText('第一章')
  expect(await page.locator('.reader-container').count()).toBe(0)

  await page.getByRole('button', { name: /返回/ }).click()
  await page.waitForURL(/\/explore/, { timeout: 10000 })

  expect(errors, '存在 console/pageerror 异常').toEqual([])
})
