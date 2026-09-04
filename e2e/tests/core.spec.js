// 墨池 E2E 冒烟：注册/登录 → 写作台（AI 流式 Mock/设定/会话/引用 chips）→
// 作品发布 → 社区 → 原创阅读器 → 灵感馆（浏览/收藏/收录/引用）→ 个人主页
import { test, expect } from '@playwright/test'

const REAL_AI = process.env.E2E_REAL_AI === '1'
const U1 = 'e2e_writer'
const PW = 'e2e123456'

// ---------- 工具 ----------

function sseBody(chunks) {
  return chunks.map(c => `data: ${JSON.stringify(c)}\n\n`).join('') + 'data: [DONE]\n\n'
}

/** 默认 Mock AI：拦截续写/对话流式接口，返回假 SSE（零 token）。 */
async function installAiMock(context) {
  if (REAL_AI) return
  await context.route('**/api/write/continue', route =>
    route.fulfill({
      status: 200,
      contentType: 'text/event-stream; charset=utf-8',
      body: sseBody([{ chunk: '【模拟AI】月光铺满旧城的石阶，他想起外婆说过，故事要从一盏灯讲起。' }]),
    }),
  )
  await context.route('**/api/write/chat', route =>
    route.fulfill({
      status: 200,
      contentType: 'text/event-stream; charset=utf-8',
      body: sseBody([{ chunk: '（模拟AI回复）这个设定很有张力，可以让“灯的来源”成为第一集悬念。', session_key: 'e2e-mock' }]),
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
  await page.getByPlaceholder('用户名').fill(U1)
  await page.getByPlaceholder('密码').fill(PW)
  await page.getByRole('button', { name: /登\s*录/ }).click()
  try {
    await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 6000 })
    return
  } catch {
    /* 用户不存在 → 注册后再登录 */
  }
  await page.goto('/register')
  await page.getByPlaceholder('用户名').fill(U1)
  await page.getByPlaceholder('密码').fill(PW)
  await page.getByPlaceholder('确认密码').fill(PW)
  await page.getByRole('button', { name: /注\s*册/ }).click()
  await page.waitForURL(url => !url.pathname.includes('/register'), { timeout: 10000 })
  await page.goto('/login')
  await page.getByPlaceholder('用户名').fill(U1)
  await page.getByPlaceholder('密码').fill(PW)
  await page.getByRole('button', { name: /登\s*录/ }).click()
  await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 8000 })
}

async function openTab(page, labelRe) {
  const tabs = page.locator('.ai-tabs button')
  const n = await tabs.count()
  for (let i = 0; i < n; i++) {
    const t = await tabs.nth(i).innerText()
    if (labelRe.test(t)) { await tabs.nth(i).click(); return }
  }
  throw new Error('tab not found: ' + labelRe)
}

// ---------- 用例 ----------

test('01 注册/登录与写作台闭环（AI 流式+设定+会话）', async ({ page, context }) => {
  const errors = watchErrors(page)
  await installAiMock(context)
  await ensureUser(page)

  // 写作台：标题 + 内容 + 保存
  await page.goto('/write')
  await page.locator('.work-title').fill('E2E 测试之书')
  await page.locator('.editor-area').fill('雨夜，他推开老宅的门，一股陈旧的墨香扑面而来。')
  await page.getByRole('button', { name: '保存' }).click()
  await page.waitForTimeout(1200)

  // 续写（Mock SSE 流式）→ 结果出现
  await openTab(page, /续写/)
  await page.getByRole('button', { name: /开始续写/ }).click()
  await expect(page.getByText('【模拟AI】月光铺满旧城的石阶', { exact: false })).toBeVisible({ timeout: 15000 })

  // 结果插入编辑器
  await page.getByRole('button', { name: /插入编辑器/ }).first().click()
  const editorValue = await page.locator('.editor-area').inputValue()
  expect(editorValue).toContain('模拟AI')

  // 设定（work_lore）页签
  await openTab(page, /^设定$/)
  await page.getByPlaceholder(/设定标题/).fill('世界观')
  await page.getByPlaceholder(/设定内容/).fill('蒸汽与龙脉共生的东方大陆。')
  await page.getByRole('button', { name: /保存设定/ }).click()
  await expect(page.locator('.lore-item')).toContainText('蒸汽与龙脉共生的东方大陆')

  // 对话（Mock）→ 历史会话列表出现并可展开
  await openTab(page, /^对话$/)
  await page.getByPlaceholder('聊聊你的故事想法...').fill('帮我设计一个悬念开头')
  await page.getByRole('button', { name: '发送' }).click()
  await expect(page.getByText('（模拟AI回复）这个设定很有张力', { exact: false })).toBeVisible({ timeout: 15000 })
  await page.getByRole('button', { name: /历史会话/ }).click()
  await expect(page.locator('.chat-history')).toBeVisible()

  expect(errors, '存在 console/pageerror 异常').toEqual([])
})

test('02 作品发布 → 社区可见 → 原创阅读器', async ({ page, context }) => {
  const errors = watchErrors(page)
  await installAiMock(context)
  await ensureUser(page)

  await page.goto('/works')
  await expect(page.getByText('E2E 测试之书', { exact: false })).toBeVisible({ timeout: 15000 })
  await page.getByText('E2E 测试之书', { exact: false }).click()

  // 详情页 → 发布（经共享会话的 API）
  const m = page.url().match(/\/works\/(\d+)/)
  expect(m, '应处于作品详情页').toBeTruthy()
  const workId = Number(m[1])
  const pub = await context.request.put(`/api/works/${workId}/status`, { data: { status: 'published' } })
  expect((await pub.json()).code).toBe(0)

  // 原创阅读器：打开章节正文
  await page.getByRole('button', { name: /阅读/ }).click()
  await page.waitForURL(/\/read\//, { timeout: 15000 })
  await expect(page.getByText('雨夜，他推开老宅的门', { exact: false })).toBeVisible({ timeout: 15000 })

  // 社区广场能看到已发布作品
  await page.goto('/explore')
  await expect(page.getByText('E2E 测试之书', { exact: false })).toBeVisible({ timeout: 20000 })

  expect(errors, '存在 console/pageerror 异常').toEqual([])
})

test('03 灵感馆：翻阅/收藏/收录句子/引用到创作', async ({ page, context }) => {
  const errors = watchErrors(page)
  await installAiMock(context)
  await ensureUser(page)

  // 浏览：今日灵感 + 诗词卡片
  await page.goto('/inspire')
  await expect(page.locator('.hero-quote p')).not.toBeEmpty({ timeout: 15000 })
  await expect(page.locator('.inspire-card').first()).toBeVisible()

  // 句子素材 → 引用到创作（chips 写入 writing store）
  await page.getByRole('button', { name: /句子素材/ }).click()
  await expect(page.locator('.inspire-card').first()).toBeVisible({ timeout: 15000 })
  await page.locator('.inspire-card').first().getByRole('button', { name: /＋ 引用/ }).click()

  // 回到写作台续写面板 → 引用 chips 可见
  await page.goto('/write')
  await openTab(page, /续写/)
  await expect(page.locator('.ref-chips')).toBeVisible({ timeout: 10000 })
  const chipsText = await page.locator('.ref-chips').innerText()
  expect(chipsText.length).toBeGreaterThan(0)

  // 灵感馆收藏：诗词 ♡ → 收藏页签出现
  await page.goto('/inspire')
  await page.locator('.inspire-card').first().getByRole('button', { name: '♡' }).click()
  await page.getByRole('button', { name: /收藏/ }).click()
  await expect(page.locator('.inspire-card').first()).toBeVisible({ timeout: 15000 })

  // 收录句子
  await page.getByRole('button', { name: /＋ 收录句子/ }).click()
  await page.locator('.modal input').fill('随想')
  await page.locator('.modal textarea').fill('风吹过屋檐，把夏天吹得哗哗响。')
  await page.locator('.modal').getByRole('button', { name: /收录$/ }).click()
  await expect(page.getByText('已收录到素材库', { exact: false })).toBeVisible({ timeout: 8000 })

  // 句子素材搜索可检索到新收录内容
  await page.getByRole('button', { name: /句子素材/ }).click()
  await page.getByPlaceholder(/搜索内容/).fill('哗哗响')
  await page.getByRole('button', { name: '搜索', exact: true }).click()
  await expect(page.getByText('风吹过屋檐，把夏天吹得哗哗响', { exact: false })).toBeVisible({ timeout: 15000 })

  expect(errors, '存在 console/pageerror 异常').toEqual([])
})

test('04 个人主页：创作统计与页签', async ({ page, context }) => {
  const errors = watchErrors(page)
  await installAiMock(context)
  await ensureUser(page)

  // 从用户菜单进入个人主页
  await page.locator('.avatar-wrapper').click()
  await page.getByRole('link', { name: /我的主页/ }).click()
  await page.waitForURL(/\/profile\//, { timeout: 15000 })

  await expect(page.getByText('创作', { exact: true })).toBeVisible()
  await expect(page.getByText('作品', { exact: true })).toBeVisible()
  for (const tab of ['作品', '收藏', '成就', '粉丝', '关注']) {
    await expect(page.getByRole('button', { name: tab, exact: true }).first()).toBeVisible()
  }
  expect(errors, '存在 console/pageerror 异常').toEqual([])
})
