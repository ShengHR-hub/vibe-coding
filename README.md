# 墨池 Inkstone · AI 智能创作与写作社交平台

面向写作爱好者的全品类创作平台，融合 **AI 写作助手**、**素材灵感**、**社区社交互动** 与 **数据洞察成长** 四大能力。
技术栈：Vue 3 + Vite + Pinia · Flask 3 · MySQL 8 · MiMo 大模型（OpenAI 兼容流式接口）。

> 当前状态：功能开发已超出毕设原始范围；正在进行收缩重构——**P1 写作主线强化（W1-W4）✅ → P2 书籍模块下线（R，已完成）→ P3 重造灵感馆（F，进行）**。
> 方向与纪律见 `docs/灵感馆方向.md`、`docs/写作强化计划.md`、`docs/改造守则.md`；分步进度见 `docs/改造进度.md`。

---

## 功能总览

| 域 | 模块 | 说明 |
|---|---|---|
| AI 创作 | 写作工作室 | AI 续写（可注入作品设定/角色/素材）/ 灵感 / 大纲 / 角色 / 润色 / 提示 / 对话 / 诊断 / 摘要（SSE 流式），安全限流与每日配额 |
| 创作管理 | 作品中心 | 作品 CRUD、章节与分卷、版本快照回退、草稿/发布/私密、导出、**作品设定记忆 work_lore** |
| 社交 | 社区广场 | 推荐流、分类、搜索、互动（点赞/评论/收藏）、排行 |
| 内容 | 诗词 / 素材 / 每日练习 / 挑战 / 角色扮演 | 精选诗词、素材/灵感库（可"引用"注入 AI 请求）、每日一题、写作挑战与共创、作品角色扮演 |
| 用户 | 主页/成长 | 关注/粉丝、等级经验、成就徽章、通知中心、写作统计（热力图/趋势/风格）、知识图谱、AI 会话历史管理 |
| AI 书评 | 书评与推荐 | AI 书评生成、个性化推荐、相似作品 |

> 注：外部书库/TXT 导入等"书"相关功能已随方向变更下线（代码与表已移除，R2-R3）；原创作品的沉浸阅读器 `/read/:id` 保留。

## 技术栈与规模

- 前端：Vue 3 + Vite + Vue Router + Pinia，毛玻璃/暗色暖色自定义主题，33 个页面
- 后端：Flask 3（应用工厂 + 17 个蓝图、106 个 API 端点）+ PyMySQL 连接池（全部参数化 SQL）
- 数据库：MySQL 8，26 张表
- AI：小米 MiMo API（SSE `text/event-stream` 流式返回），对话按 session 落库；所有 AI 端点按用户限流 + 每日配额（env 可配）
- 认证：Session-based + bcrypt，登录/注册 IP 限速

## 目录结构

```
inkstone/
├── client/                 # Vue3 前端（33 页面）
│   └── src/
│       ├── api/            # HTTP 封装（request + SSE stream）
│       ├── router/         # 路由 + 全局守卫（auth/guest meta）
│       ├── stores/         # Pinia（user / writing：含引用素材队列）
│       ├── views/          # 页面（write/works/community/user/stats/...）
│       ├── utils/render.js # 文本安全渲染（统一转义，node --test 单测）
│       └── components/     # 通用组件
├── server/                 # Flask 后端
│   ├── app.py              # 应用工厂（蓝图注册 + 静态托管 + 安全头）
│   ├── config.py           # 环境变量配置（缺 SECRET_KEY/MIMO_API_KEY 即拒绝启动）
│   ├── routes/             # 17 个蓝图（auth/write/works/community/interactions/users/
│   │                       #   stats/graph/challenges/notifications/review/poems/materials/
│   │                       #   daily/rankings/serialize/rp）
│   ├── database/
│   │   ├── schema.sql      # 26 张表 DDL（含 work_lore；书/阅读表已下线）
│   │   ├── db.py           # PyMySQL 连接池（query/execute/execute_many，自动事务）
│   │   └── seed.py         # 成就定义 + 预制数据
│   ├── utils/              # helpers（含 AI 配额）/ prompt_builder / logger / mimos
│   └── tests/              # pytest 76 用例（隔离测试库 inkstone_test）
└── docs/                   # 需求文档 / 方向与强化计划 / 改造守则与进度
```

## 本地启动

```bash
# 1. 初始化数据库（一次性）
mysql -u root -p < server/database/schema.sql
cd server && python -m database.seed

# 2. 环境变量
cp server/.env.example server/.env   # 填入 SECRET_KEY / MYSQL_PASSWORD / MIMO_API_KEY

# 3. 后端（端口 5000）
cd server && python app.py

# 4. 前端（端口 5173）
cd client && npm install && npm run dev
```

生产形态：`cd client && npm run build` 后由 Flask 直接托管 `client/dist`（单进程形态；正式部署的 gunicorn/nginx/Docker 方案见 Backlog/后续里程碑）。

## 测试

```bash
cd server && python -m pytest tests -q   # 后端 76 用例
cd client && npm run test:util            # 前端渲染工具单测
```

- pytest 一律连接独立测试库 **inkstone_test**（不触碰开发库 inkstone）；
- 每个会话自动重建库表，每个用例前清空数据与限速计数，可重复执行、相互独立；
- AI 相关用例全部 stub 掉真实模型调用（零 token 消耗）；
- 覆盖：auth / works / community / helpers / write（限流·上限·上下文注入·会话管理·references 素材注入）。

## 版本控制红线

- `.env`、`client/dist/`、`server/uploads/`、`node_modules/`、日志、缓存一律不提交（见 `.gitignore`）；
- 示例配置提交 `.env.example`；改动文档与代码必须同步（避免历史遗留的"文档数字失真"问题）。

## 文档索引

- `docs/REQUIREMENTS.md` — 毕设原始需求规格（10 模块 46 功能，历史留档）
- `docs/灵感馆方向.md` — 方向变更与范围边界（"灵感馆"路线）
- `docs/写作强化计划.md` — P1 写作主线强化 W1-W4 计划与竞品借鉴映射
- `docs/改造守则.md` — 改造期"不劣化契约"（步骤规程/红线/决策记录）
- `docs/改造进度.md` — 分步变更登记与测试证据
- `docs/墨池阅读模块需求文档.md` / `docs/阅读模块实施计划.md` — 已作废（书库下线），留档备查
