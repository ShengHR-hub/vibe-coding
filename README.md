# 墨池 Inkstone · AI 智能创作与写作社交平台

面向写作爱好者的全品类创作平台，融合 **AI 写作助手**、**社区社交互动**、**数据洞察成长** 与 **书库阅读** 四大能力。
技术栈：Vue 3 + Vite + Pinia · Flask 3 · MySQL 8 · MiMo 大模型（OpenAI 兼容流式接口）。

> 当前状态：功能开发已超出毕设原始范围，正在进行 **M0→M3 收敛加固**（仓库/测试/文档基线 → 阅读模块收口 → 安全与 AI 成本加固 → 部署与工程化）。
> 过程守则与里程碑进度见 `docs/改造守则.md`、`docs/改造进度.md`。

---

## 功能总览

| 域 | 模块 | 说明 |
|---|---|---|
| AI 创作 | 写作工作室 | AI 续写 / 灵感 / 大纲 / 角色 / 润色 / 提示 / 对话 / 诊断 / 摘要（SSE 流式） |
| 创作管理 | 作品中心 | 作品 CRUD、章节与分卷、版本快照回退、草稿/发布/私密、导出 |
| 社交 | 社区广场 | 推荐流、分类、搜索、互动（点赞/评论/收藏）、排行 |
| 阅读 | 书库与阅读器 | TXT 导入、书库/书架、沉浸阅读器、进度同步、书签/批注/好句、阅读打卡与报告 |
| 内容 | 诗词 / 素材 / 每日练习 / 挑战 / 角色扮演 | 精选诗词、灵感素材库、每日一题、写作挑战与共创、作品角色扮演 |
| 用户 | 主页/成长 | 关注/粉丝、等级经验、成就徽章、通知中心、写作统计（热力图/趋势/风格）、知识图谱 |
| AI 书评 | 书评与推荐 | AI 书评生成、个性化推荐、相似作品 |

## 技术栈与规模

- 前端：Vue 3 + Vite + Vue Router + Pinia，毛玻璃/暗色暖色自定义主题，42 个页面
- 后端：Flask 3（应用工厂 + 27 个蓝图、150+ API 端点）+ PyMySQL 连接池（全部参数化 SQL）
- 数据库：MySQL 8，38 张表
- AI：小米 MiMo API（SSE `text/event-stream` 流式返回），对话按 session 落库
- 认证：Session-based + bcrypt，登录/注册 IP 限速

## 目录结构

```
inkstone/
├── client/                 # Vue3 前端
│   └── src/
│       ├── api/            # HTTP 封装（request + SSE stream）
│       ├── router/         # 路由 + 全局守卫（auth/guest meta）
│       ├── stores/         # Pinia（user / writing）
│       ├── views/          # 页面（write/works/community/library/user/...）
│       └── components/     # 通用组件
├── server/                 # Flask 后端
│   ├── app.py              # 应用工厂（蓝图注册 + 静态托管 + 安全头）
│   ├── config.py           # 环境变量配置（缺 SECRET_KEY/MIMO_API_KEY 即拒绝启动）
│   ├── routes/             # 27 个蓝图（auth/write/works/community/interactions/users/
│   │                       #   stats/graph/challenges/notifications/review/poems/materials/
│   │                       #   daily/rankings/serialize/rp/library/bookshelf/reading/
│   │                       #   bookmarks/annotations/checkin/report/highlights/reviews/compare）
│   ├── database/
│   │   ├── schema.sql      # 38 张表 DDL
│   │   ├── db.py           # PyMySQL 连接池（query/execute/execute_many，自动事务）
│   │   └── seed.py         # 成就定义 + 预制数据
│   ├── utils/              # helpers / prompt_builder / logger 等
│   └── tests/              # pytest（隔离测试库 inkstone_test）
└── docs/                   # 需求文档 / 阅读模块计划 / 改造守则与进度
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

生产形态：`cd client && npm run build` 后由 Flask 直接托管 `client/dist`（单进程形态，正式部署建议见 M3 里程碑，将提供 gunicorn/nginx/Docker 方案）。

## 测试

```bash
cd server && python -m pytest tests -q
```

- pytest 一律连接独立测试库 **inkstone_test**（不触碰开发库 inkstone）；
- 每个会话自动重建库表，每个用例前清空数据与限速计数，可重复执行、相互独立；
- 现有覆盖：auth / works / community / helpers（48 用例）。阅读模块等新模块测试在 M1/M3 里程碑补充。

## 版本控制红线

- `.env`、`client/dist/`、`server/uploads/`、`node_modules/`、日志、缓存一律不提交（见 `.gitignore`）；
- 示例配置提交 `.env.example`；改动文档与代码必须同步（避免历史遗留的"文档数字失真"问题）。

## 文档索引

- `docs/REQUIREMENTS.md` — 毕设原始需求规格（10 模块 46 功能）
- `docs/墨池阅读模块需求文档.md` / `docs/阅读模块实施计划.md` — 阅读模块 v2 需求与 54 步计划
- `docs/改造守则.md` — M0→M3 阶段"不劣化契约"（步骤规程/红线/决策记录）
- `docs/改造进度.md` — 分步变更登记与测试证据
