# 墨池 Inkstone — AI 写作社交平台

## 项目概况

Vue3 + Flask + MySQL + MiMo 大模型，面向写作爱好者的全品类创作平台。
10 模块 46 功能，当前 6/13 阶段完成。

## 启动命令

```bash
# 后端（端口 5000）
cd server && python app.py

# 前端（端口 5173）
cd client && npm run dev

# 初始化数据库
mysql -u root -p123456 < server/database/schema.sql
cd server && python -m database.seed
```

## 项目结构

```
inkstone/
├── client/                  # Vue3 + Vite 前端
│   └── src/
│       ├── api/index.js     # HTTP 封装（request + SSE stream）
│       ├── router/index.js  # 路由 + 全局守卫（auth/guest meta）
│       ├── stores/          # Pinia（user.js, writing.js）
│       ├── views/           # 页面组件
│       │   ├── write/       # AI 写作工作室
│       │   ├── works/       # 作品管理 + 阅读器
│       │   ├── community/   # 社区广场
│       │   └── user/        # 个人主页
│       └── components/      # 通用组件
└── server/                  # Flask 后端
    ├── app.py               # 应用工厂
    ├── config.py            # 配置（环境变量）
    ├── routes/              # 蓝图路由
    │   ├── auth.py          # 注册/登录/登出（bcrypt + session）
    │   ├── write.py         # AI 写作（6 端点，续写用 SSE）
    │   ├── works.py         # 作品 CRUD + 版本快照 + 发布/阅读
    │   ├── community.py     # 社区流/搜索/分类
    │   ├── interactions.py  # 评论/点赞/收藏
    │   └── users.py         # 个人主页/关注/成就/等级
    ├── database/
    │   ├── schema.sql       # 17 张表 DDL
    │   ├── db.py            # PyMySQL 封装（query/execute, DictCursor）
    │   └── seed.py          # 成就定义 + 预制数据
    └── utils/
        └── helpers.py       # ok()/fail()/login_required
```

## 技术约定

### API 响应格式
```json
{"code": 0, "data": {...}, "msg": "success"}
// code=0 成功，非0失败；401=未登录，404=不存在
```

### 认证
- Session-based（Flask session），`@login_required` 装饰器保护路由
- `client/src/stores/user.js` 用 `initialized` 标志防止路由守卫竞态
- 全局路由守卫：`auth` meta 需登录，`guest` meta 登录后重定向到 `/`

### 数据库
- PyMySQL + DictCursor，`database/db.py` 提供 `query()` 和 `execute()`
- 所有路由通过这两个函数操作数据库，不直接写 SQL 连接
- `execute()` 自动 commit/rollback，返回 `lastrowid`
- 点赞/关注用 toggle 模式：SELECT 检查 → INSERT 或 DELETE
- 计数器使用 `GREATEST(x-1, 0)` 防负值

### AI 流式响应
- SSE `text/event-stream`，chunk 格式 `data: xxx\n\n`，结束 `data: [DONE]\n\n`
- 前端 `api.stream()` 解析 SSE，支持 onChunk/onDone/onError 回调
- 对话历史按 `session_key` (UUID) 存入 `ai_conversations`

### 前端样式
- CSS 自定义属性体系（`--accent-primary`, `--bg-glass`, `--border-glass` 等）
- 毛玻璃卡片：`class="glass-card"`
- 路由切换动画：`<transition name="page" mode="out-in">`

### 等级系统
- 经验值 = 总字数 + 获赞×2 + 评论×3
- 10 级：初窥门径→文坛巨匠，阈值 [0, 100, 500, 1500, 5000, 12000, 30000, 80000, 200000, 500000]
- 查看主页时自动重算，后端返回 `prev_level_exp` + `next_level_exp` 供前端算进度条

### 作品版本快照
- 每次更新前 JSON 序列化当前状态 → `work_versions`
- 回退前先创建当前状态快照（可逆操作）
- 日期字段用 `_fmt()` 转 ISO 字符串再序列化

## 关键路由

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/auth/me | 当前用户（无需 auth） |
| POST | /api/write/continue | AI 续写（SSE 流式） |
| GET | /api/works | 自己的作品列表（需 auth） |
| GET | /api/works/public/:id | 公开作品详情（无需 auth） |
| GET | /api/community/feed?sort=hot | 社区推荐流 |
| GET | /api/community/search?q= | 全文搜索 |
| POST | /api/interactions/like | 点赞 toggle |
| POST | /api/interactions/favorite | 收藏 toggle |
| GET | /api/users/:id | 个人主页 |
| POST | /api/users/follow | 关注 toggle |
| GET | /api/users/achievements | 成就列表（需 auth） |

## 红线

- **不要**在路由中直接创建数据库连接，用 `db.query()` / `db.execute()`
- **不要**在 `works/<id>` 端点返回非本人作品（已拆分为 `works/public/<id>`）
- **不要**用 `'\s'` 匹配空白（Python 中它是字面量），用 `re.sub(r'\s', '', text)`
- **不要**在前端维护与后端重复的阈值/常量（如等级表），从 API 响应取值
- **不要**在 CLAUDE.md 顶部写 blockquote 历史叙事
