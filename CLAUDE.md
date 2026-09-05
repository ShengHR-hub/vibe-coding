# 墨池 Inkstone — AI 写作社交平台

## 项目概况

Vue3 + Flask + MySQL + 多供应商大模型网关（阿里云 qwen3.8-flash 主力 / 智谱 glm-4.7-flash 兜底，兼容 OpenAI 协议），面向写作爱好者的全品类创作平台。
当前规模：**19 个蓝图 / 114 个 API 端点 / 28 张表 / 39 个前端页面**。
当前阶段：**成书工作流（起·承·合）已发布，进入收敛加固期**（独立仓库与测试基线已就绪，进行中）。过程纪律见 `docs/改造守则.md`，分步进度见 `docs/改造进度.md`，老师讲解版见 `docs/项目详解文档.md`，**接手/恢复会话先读 `docs/交接文档.md`**。

## 启动命令

> **一键启动（双击，推荐给用户演示）**：`启动开发服务.bat` —— 弹出后端 :5000 / 前端 :5173 窗口并自动开浏览器；`停止开发服务.bat` 停止。
> **Agent/命令行静默拉起（本会话恢复后用这个）**：`powershell -ExecutionPolicy Bypass -File .\dev-up.ps1` —— 不开窗口、后端+前端先后台启动、并行等待就绪后打印地址与日志位置（日志：`server/logs/dev-*.log`，停止：`dev-down.ps1`）。等价于 `start-dev.ps1 -Headless -NoBrowser`。

```bash
# 初始化数据库（一次性）
mysql -u root -p123456 < server/database/schema.sql
cd server && python -m database.seed

# 后端（端口 5000）
cd server && python app.py

# 前端（端口 5173）
cd client && npm run dev

# 后端测试（隔离测试库 inkstone_test，不碰开发库）
cd server && python -m pytest tests -q
```

## 项目结构

```
inkstone/
├── client/                  # Vue3 + Vite 前端（39 页面）
│   └── src/
│       ├── api/index.js     # HTTP 封装（request + SSE stream）
│       ├── router/index.js  # 路由 + 全局守卫（auth/guest meta；standalone=全屏阅读态）
│       ├── stores/          # Pinia（user.js, writing.js）
│       ├── views/           # write/works/community/user/stats/...
│       └── components/      # 通用组件（含若干仅供展示的高保真动效组件）
└── server/                  # Flask 后端（19 蓝图，routes/__init__.py 统一注册）
    ├── app.py               # 应用工厂（蓝图 + 安全头 + uploads/静态托管）
    ├── config.py            # 环境变量配置（缺 SECRET_KEY/AI_API_KEY 拒绝启动）
    ├── routes/              # 19 蓝图：auth/write/works/community/interactions/users/stats/graph/
    │                        # challenges/notifications/review/poems/materials/daily/rankings/
    │                        # serialize/rp/inspire/plans（书/书库蓝图已下线；计划域 book_plans 承载成书工作流）
    ├── database/
    │   ├── schema.sql       # 28 张表 DDL（含 work_lore/book_plans/inspiration_favorites；书库/阅读表已下线）
    │   ├── db.py            # PyMySQL 连接池（query/execute/execute_many）
    │   └── seed.py          # 成就定义 + 预制数据
    ├── tests/               # pytest 96 用例（隔离测试库，见 conftest.py）
    └── utils/               # helpers/prompt_builder/logger/mimos（AI 多供应商网关）
```

## 技术约定

### API 响应格式
```json
{"code": 0, "data": {...}, "msg": "success"}
// code=0 成功，非0失败；401=未登录，404=不存在
```

### 认证
- Session-based（Flask session），`@login_required` 装饰器保护路由
- bcrypt 哈希；登录/注册有进程内 IP 限速（auth.py 模块级 dict）
- `client/src/stores/user.js` 用 `initialized` 标志防止路由守卫竞态
- 全局路由守卫：`auth` meta 需登录，`guest` meta 登录后重定向

### 数据库
- PyMySQL 连接池 + DictCursor，`database/db.py` 提供 `query()` / `execute()` / `execute_many()`
- 所有路由通过这三个函数操作数据库，不直接写 SQL 连接；SQL 一律参数化（f-string 只拼内部白名单）
- `execute()` 自动 commit/rollback，返回 lastrowid；点赞/关注用 toggle（SELECT→INSERT/DELETE）
- 计数器用 `GREATEST(x-1, 0)` 防负值
- **测试隔离**：pytest 走 inkstone_test（conftest.py 会话重建 + 每用例清表 + 清限速计数），禁止改回开发库

### AI 流式响应
- SSE `text/event-stream`，chunk `data: xxx\n\n`，结束 `data: [DONE]\n\n`
- 前端 `api.stream()` 解析，支持 onChunk/onDone/onError
- 对话历史按 `session_key` (UUID) 存入 `ai_conversations`；输入有字符上限（部分端点待补，见 M2）
- **安全提醒**：多数 AI 面板此前直接 `v-html` 模型输出——涉及渲染用户/AI 内容时先走统一转义（M2 专项收口，勿新增裸 v-html）

### 前端样式与渲染
- CSS 自定义属性体系（`--accent-primary` 等）+ 毛玻璃 `glass-card` + `<transition name="page">`
- 用户/AI 文本渲染：统一走转义后再拼受控 HTML；不要直接 `v-html` 外部内容

### 等级与成就
- 经验值 = 总字数 + 获赞×2 + 评论×3（注意：阅读时长尚未入经验，M1 计划项）
- 等级阈值后端下发（`/api/users/levels`），前端不得重复维护

### 作品版本快照
- 每次更新前序列化当前状态 → `work_versions`；回退前先建当前快照（可逆）
- 日期字段 `_fmt()` 转 ISO 字符串后再序列化

## 关键路由（节选，全量见 routes/）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/auth/me | 当前用户（无需 auth） |
| POST | /api/write/continue | AI 续写（SSE 流式） |
| GET | /api/works | 自己的作品列表（需 auth） |
| GET | /api/works/public/:id | 公开作品详情（无需 auth） |
| GET | /api/community/feed?sort=hot | 社区推荐流 |
| GET | /api/community/search?q= | 全文搜索 |
| GET | /api/works/:id/lore | 作品设定记忆（work_lore）CRUD |
| GET | /api/write/conversations | AI 会话历史（含剪枝） |
| POST | /api/interactions/like | 点赞 toggle |
| GET | /api/users/:id | 个人主页 |
| GET | /api/users/achievements | 成就列表（需 auth） |

## 红线

- **不要**在路由中直接创建数据库连接，用 `db.query()` / `db.execute()` / `execute_many()`
- **不要**在 `works/<id>` 端点返回非本人作品（公开走 `works/public/<id>`）
- **不要**用 `'\s'` 匹配空白（Python 中是字面量），用 `re.sub(r'\s', '', text)`
- **不要**在前端维护与后端重复的阈值/常量（等级/成就等），从 API 响应取值
- **不要**在 CLAUDE.md 顶部写 blockquote 历史叙事
- **不要**给外部可见文本直接 `v-html`（先统一转义）；**不要**把测试指向开发库 inkstone
- **不要**提交 `.env` / `client/dist/` / `server/uploads/` 等（见 .gitignore）；真实密钥只放本地 .env
- 改动遵循 `docs/改造守则.md`：最小增量、每步自测+回归、绿灯才前进；无关发现进 `docs/改造进度.md` Backlog
