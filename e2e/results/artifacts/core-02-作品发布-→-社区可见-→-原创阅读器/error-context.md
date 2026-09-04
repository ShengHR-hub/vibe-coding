# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: core.spec.js >> 02 作品发布 → 社区可见 → 原创阅读器
- Location: tests\core.spec.js:117:1

# Error details

```
Error: locator.fill: Error: strict mode violation: getByPlaceholder('密码') resolved to 2 elements:
    1) <input required="" type="password" placeholder="密码" data-v-f3e3d397="" autocomplete="new-password"/> aka getByRole('textbox', { name: '密码', exact: true })
    2) <input required="" type="password" data-v-f3e3d397="" placeholder="确认密码" autocomplete="new-password"/> aka getByRole('textbox', { name: '确认密码' })

Call log:
  - waiting for getByPlaceholder('密码')

```

# Page snapshot

```yaml
- generic [ref=f1e3]:
  - navigation [ref=f1e4]:
    - generic [ref=f1e7]:
      - link "写作" [ref=f1e8] [cursor=pointer]:
        - /url: /write
      - link "灵感馆" [ref=f1e9] [cursor=pointer]:
        - /url: /inspire
      - link "广场" [ref=f1e10] [cursor=pointer]:
        - /url: /explore
      - link "练习" [ref=f1e11] [cursor=pointer]:
        - /url: /daily
      - link "排行" [ref=f1e12] [cursor=pointer]:
        - /url: /rankings
      - link "挑战" [ref=f1e13] [cursor=pointer]:
        - /url: /challenges
  - generic [ref=f1e14]:
    - link "墨池" [ref=f1e15] [cursor=pointer]:
      - /url: /
    - link "灵感" [ref=f1e24] [cursor=pointer]:
      - /url: /inspire
  - link "登录" [ref=f1e26] [cursor=pointer]:
    - /url: /login
  - main [ref=f1e27]:
    - generic [ref=f1e28]:
      - generic:
        - generic: 墨
        - generic: 池
      - generic [ref=f1e32]:
        - generic [ref=f1e33]: ✽
        - heading "注册墨池" [level=2] [ref=f1e35]
        - paragraph [ref=f1e36]: 提笔入墨，自此为家
        - generic [ref=f1e37]:
          - generic [ref=f1e38]:
            - generic: ✎
            - textbox "用户名" [active] [ref=f1e39]: e2e_writer
          - generic [ref=f1e41]:
            - generic: ⚬
            - textbox "密码" [ref=f1e42]
          - generic [ref=f1e43]:
            - generic: ⚬
            - textbox "确认密码" [ref=f1e44]
          - button "注 册" [ref=f1e45] [cursor=pointer]
        - paragraph [ref=f1e47]:
          - text: 已有账号？
          - link "去登录" [ref=f1e48] [cursor=pointer]:
            - /url: /login
```

# Test source

```ts
  1   | // 墨池 E2E 冒烟：注册/登录 → 写作台（AI 流式 Mock/设定/会话/引用 chips）→
  2   | // 作品发布 → 社区 → 原创阅读器 → 灵感馆（浏览/收藏/收录/引用）→ 个人主页
  3   | import { test, expect } from '@playwright/test'
  4   | 
  5   | const REAL_AI = process.env.E2E_REAL_AI === '1'
  6   | const U1 = 'e2e_writer'
  7   | const PW = 'e2e123456'
  8   | 
  9   | // ---------- 工具 ----------
  10  | 
  11  | function sseBody(chunks) {
  12  |   return chunks.map(c => `data: ${JSON.stringify(c)}\n\n`).join('') + 'data: [DONE]\n\n'
  13  | }
  14  | 
  15  | /** 默认 Mock AI：拦截续写/对话流式接口，返回假 SSE（零 token）。 */
  16  | async function installAiMock(context) {
  17  |   if (REAL_AI) return
  18  |   await context.route('**/api/write/continue', route =>
  19  |     route.fulfill({
  20  |       status: 200,
  21  |       contentType: 'text/event-stream; charset=utf-8',
  22  |       body: sseBody([{ chunk: '【模拟AI】月光铺满旧城的石阶，他想起外婆说过，故事要从一盏灯讲起。' }]),
  23  |     }),
  24  |   )
  25  |   await context.route('**/api/write/chat', route =>
  26  |     route.fulfill({
  27  |       status: 200,
  28  |       contentType: 'text/event-stream; charset=utf-8',
  29  |       body: sseBody([{ chunk: '（模拟AI回复）这个设定很有张力，可以让“灯的来源”成为第一集悬念。', session_key: 'e2e-mock' }]),
  30  |     }),
  31  |   )
  32  | }
  33  | 
  34  | function watchErrors(page) {
  35  |   const errors = []
  36  |   page.on('pageerror', e => errors.push('pageerror: ' + e.message))
  37  |   page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()) })
  38  |   return errors
  39  | }
  40  | 
  41  | async function ensureUser(page) {
  42  |   await page.goto('/login')
  43  |   await page.getByPlaceholder('用户名').fill(U1)
  44  |   await page.getByPlaceholder('密码').fill(PW)
  45  |   await page.getByRole('button', { name: /登\s*录/ }).click()
  46  |   try {
  47  |     await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 6000 })
  48  |     return
  49  |   } catch {
  50  |     /* 用户不存在 → 注册后再登录 */
  51  |   }
  52  |   await page.goto('/register')
  53  |   await page.getByPlaceholder('用户名').fill(U1)
> 54  |   await page.getByPlaceholder('密码').fill(PW)
      |                                     ^ Error: locator.fill: Error: strict mode violation: getByPlaceholder('密码') resolved to 2 elements:
  55  |   await page.getByPlaceholder('确认密码').fill(PW)
  56  |   await page.getByRole('button', { name: /注\s*册/ }).click()
  57  |   await page.waitForURL(url => !url.pathname.includes('/register'), { timeout: 10000 })
  58  |   await page.goto('/login')
  59  |   await page.getByPlaceholder('用户名').fill(U1)
  60  |   await page.getByPlaceholder('密码').fill(PW)
  61  |   await page.getByRole('button', { name: /登\s*录/ }).click()
  62  |   await page.waitForURL(url => !url.pathname.includes('/login'), { timeout: 8000 })
  63  | }
  64  | 
  65  | async function openTab(page, labelRe) {
  66  |   const tabs = page.locator('.ai-tabs button')
  67  |   const n = await tabs.count()
  68  |   for (let i = 0; i < n; i++) {
  69  |     const t = await tabs.nth(i).innerText()
  70  |     if (labelRe.test(t)) { await tabs.nth(i).click(); return }
  71  |   }
  72  |   throw new Error('tab not found: ' + labelRe)
  73  | }
  74  | 
  75  | // ---------- 用例 ----------
  76  | 
  77  | test('01 注册/登录与写作台闭环（AI 流式+设定+会话）', async ({ page, context }) => {
  78  |   const errors = watchErrors(page)
  79  |   await installAiMock(context)
  80  |   await ensureUser(page)
  81  | 
  82  |   // 写作台：标题 + 内容 + 保存
  83  |   await page.goto('/write')
  84  |   await page.locator('.work-title').fill('E2E 测试之书')
  85  |   await page.locator('.editor-area').fill('雨夜，他推开老宅的门，一股陈旧的墨香扑面而来。')
  86  |   await page.getByRole('button', { name: '保存' }).click()
  87  |   await page.waitForTimeout(1200)
  88  | 
  89  |   // 续写（Mock SSE 流式）→ 结果出现
  90  |   await openTab(page, /续写/)
  91  |   await page.getByRole('button', { name: /开始续写/ }).click()
  92  |   await expect(page.getByText('【模拟AI】月光铺满旧城的石阶', { exact: false })).toBeVisible({ timeout: 15000 })
  93  | 
  94  |   // 结果插入编辑器
  95  |   await page.getByRole('button', { name: /插入编辑器/ }).first().click()
  96  |   const editorValue = await page.locator('.editor-area').inputValue()
  97  |   expect(editorValue).toContain('模拟AI')
  98  | 
  99  |   // 设定（work_lore）页签
  100 |   await openTab(page, /^设定$/)
  101 |   await page.getByPlaceholder(/设定标题/).fill('世界观')
  102 |   await page.getByPlaceholder(/设定内容/).fill('蒸汽与龙脉共生的东方大陆。')
  103 |   await page.getByRole('button', { name: /保存设定/ }).click()
  104 |   await expect(page.locator('.lore-item')).toContainText('蒸汽与龙脉共生的东方大陆')
  105 | 
  106 |   // 对话（Mock）→ 历史会话列表出现并可展开
  107 |   await openTab(page, /^对话$/)
  108 |   await page.getByPlaceholder('聊聊你的故事想法...').fill('帮我设计一个悬念开头')
  109 |   await page.getByRole('button', { name: '发送' }).click()
  110 |   await expect(page.getByText('（模拟AI回复）这个设定很有张力', { exact: false })).toBeVisible({ timeout: 15000 })
  111 |   await page.getByRole('button', { name: /历史会话/ }).click()
  112 |   await expect(page.locator('.chat-history')).toBeVisible()
  113 | 
  114 |   expect(errors, '存在 console/pageerror 异常').toEqual([])
  115 | })
  116 | 
  117 | test('02 作品发布 → 社区可见 → 原创阅读器', async ({ page, context }) => {
  118 |   const errors = watchErrors(page)
  119 |   await installAiMock(context)
  120 |   await ensureUser(page)
  121 | 
  122 |   await page.goto('/works')
  123 |   await expect(page.getByText('E2E 测试之书', { exact: false })).toBeVisible({ timeout: 15000 })
  124 |   await page.getByText('E2E 测试之书', { exact: false }).click()
  125 | 
  126 |   // 详情页 → 发布（经共享会话的 API）
  127 |   const m = page.url().match(/\/works\/(\d+)/)
  128 |   expect(m, '应处于作品详情页').toBeTruthy()
  129 |   const workId = Number(m[1])
  130 |   const pub = await context.request.put(`/api/works/${workId}/status`, { data: { status: 'published' } })
  131 |   expect((await pub.json()).code).toBe(0)
  132 | 
  133 |   // 原创阅读器：打开章节正文
  134 |   await page.getByRole('button', { name: /阅读/ }).click()
  135 |   await page.waitForURL(/\/read\//, { timeout: 15000 })
  136 |   await expect(page.getByText('雨夜，他推开老宅的门', { exact: false })).toBeVisible({ timeout: 15000 })
  137 | 
  138 |   // 社区广场能看到已发布作品
  139 |   await page.goto('/explore')
  140 |   await expect(page.getByText('E2E 测试之书', { exact: false })).toBeVisible({ timeout: 20000 })
  141 | 
  142 |   expect(errors, '存在 console/pageerror 异常').toEqual([])
  143 | })
  144 | 
  145 | test('03 灵感馆：翻阅/收藏/收录句子/引用到创作', async ({ page, context }) => {
  146 |   const errors = watchErrors(page)
  147 |   await installAiMock(context)
  148 |   await ensureUser(page)
  149 | 
  150 |   // 浏览：今日灵感 + 诗词卡片
  151 |   await page.goto('/inspire')
  152 |   await expect(page.locator('.hero-quote p')).not.toBeEmpty({ timeout: 15000 })
  153 |   await expect(page.locator('.inspire-card').first()).toBeVisible()
  154 | 
```