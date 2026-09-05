# 墨池 Inkstone · AI 智能创作与写作社交平台

> **把"写一本书"变成一条可以执行、可以被 AI 全程辅助的流水线** —— 立项定标 → 大纲成稿 → 逐章写作 → 审校收尾 → 整书交付。
> 线上体验：https://ink.shenghui2026.top （备案域名 + HTTPS + 阿里云服务器）

面向写作爱好者的全品类创作平台：以 **成书工作流（起·承·合）** 为主线，**灵感馆** 反哺创作素材，叠加社区互动与数据成长，AI 通过**多供应商网关**（阿里云 qwen3.8-flash 主力 / 智谱 glm-4.7-flash 兜底）以流式方式在每一创作环节担任协作者。

---

## 功能总览

### ✍️ 成书工作流（写作台 · 三阶段引导）

| 阶段 | 目标 | 内置工具 |
|---|---|---|
| **起 · 定目标** | 想清楚再动笔 | 立项蓝图（Logline/读者/目标字数/Deadline）、大纲规划器（卷→章，每章 Beats + Hook）、设定库 work_lore、角色卡（含弧光/关系图谱） |
| **承 · 稳推进** | 按计划写完、不卡壳 | 本章任务卡（自动带出本章目标/前情/相关设定）、按蓝图 AI 续写、写作教练（对话答疑）、素材引用（诗词/句子入上下文）、分卷管理 |
| **合 · 精收尾** | 从"写完"到"能交付" | AI 结构审校（报告 + 逐章建议 + 优先级）、逐章润色、内容诊断、[TODO] 全书扫描清零、整书一键导出 TXT |

配套：写编分离（初稿章节/正文独立编辑器）、作品版本快照可回退、`/write?work=ID` 续作。

### 💡 灵感馆（创作素材闭环）
诗词 / 句子素材统一翻阅 → ♡ 收藏个人池 → ＋引用进创作上下文 → AI 生成时自动携带 → 好句反哺作品；支持手工收录句子入库。

### 🌐 作品与社区
作品中心（草稿/发布/私密、字数统计）、广场推荐流、搜索、分类、排行、公开作品详情页（目录/点赞/收藏/评论）、每日一练、写作挑战与共创接龙、AI 书评与个性化推荐。

### 👤 用户与成长
个人主页、关注/粉丝、等级经验（字数+赞+评驱动）、成就徽章、通知中心、写作统计（趋势/热力图/风格/报告）、角色关系图谱、AI 会话历史管理。

---

## 技术栈与规模（v2026.09.05）

- 前端：Vue 3 + Vite + Vue Router + Pinia，毛玻璃/暗色暖色主题，**39 个页面**
- 后端：Flask 3（应用工厂 + **19 个蓝图、114 个 API 端点**）+ PyMySQL 连接池（全部参数化 SQL、自动事务）
- 数据库：MySQL 8，**28 张表**（作品/章节/计划/设定/灵感/社交/会话/挑战分域，外键级联）
- AI：**多供应商网关** —— OpenAI 兼容协议 + 原 MiMo(Anthropic 风格)，主力失败自动回退兜底；智谱 GLM thinking 自动开启；统一防注入护栏；SSE `text/event-stream` 流式
- 配额与安全：AI 按用户限流 + 每日配额；bcrypt + Session；登录/注册 IP 限速；文本统一转义渲染防 XSS
- 测试：**pytest 96 passed**（隔离库 inkstone_test、AI 全 mock 零成本）+ 前端工具单测 + Playwright E2E（msedge、Mock AI）
- 部署：阿里云轻量服务器 · Nginx + Gunicorn + systemd · Let's Encrypt HTTPS（详见 `docs/DEPLOY.md`）

## 目录结构

```
inkstone/
├── client/                 # Vue3 前端（39 页面）
│   └── src/
│       ├── api/            # HTTP 封装（request + SSE stream）
│       ├── router/         # 路由 + 全局守卫（auth/guest meta）
│       ├── stores/         # Pinia（user / writing：含引用素材队列）
│       ├── views/          # 页面（write 写作台/works/community/inspire/...）
│       ├── utils/render.js # 文本安全渲染（统一转义，node --test 单测）
│       └── components/     # 通用组件
├── server/                 # Flask 后端
│   ├── app.py              # 应用工厂（蓝图注册 + 静态托管 + 安全头）
│   ├── config.py           # 环境变量配置（缺 SECRET_KEY/AI 密钥即拒绝启动）
│   ├── routes/             # 19 蓝图（auth/write/works/community/interactions/users/
│   │                       #   stats/graph/challenges/notifications/review/poems/materials/
│   │                       #   daily/rankings/serialize/rp/inspire/plans）
│   ├── database/
│   │   ├── schema.sql      # 28 张表 DDL（含 work_lore/book_plans/inspiration_favorites）
│   │   ├── db.py           # PyMySQL 连接池（query/execute/execute_many，自动事务）
│   │   └── seed.py         # 成就定义 + 预制数据
│   ├── utils/              # helpers（AI 配额）/ prompt_builder / logger / mimos（AI 网关）
│   └── tests/              # pytest 96 用例（隔离测试库 inkstone_test）
├── e2e/                    # Playwright E2E（channel=msedge，Mock AI）
├── docs/                   # 方向/计划/改造纪律/部署/讲解文档
├── start-dev.ps1           # 一键启动（后端+前端+自动开浏览器）
├── 启动开发服务.bat          # 双击即可启动（推荐）
├── 停止开发服务.bat          # 双击一键停止
└── _备份/                  # 本地大数据备份（不入库：库备份 migrate_*.sql 等）
```

## 快速启动（开发模式）

**推荐：双击根目录 `启动开发服务.bat`** —— 自动检测 MySQL、分别弹出后端(:5000)/前端(:5173)窗口并等待就绪后打开浏览器；`停止开发服务.bat` 一键停止。
**命令行/后台静默**：`powershell -ExecutionPolicy Bypass -File .\dev-up.ps1`（不开窗口、日志写 `server/logs/`，停止用 `dev-down.ps1`）；窗口模式等价命令 `start-dev.ps1`（可加 `-NoBrowser`）。

手动启动（等价于脚本内部动作）：

```bash
# 1. 初始化数据库（一次性）
mysql -u root -p < server/database/schema.sql
cd server && python -m database.seed

# 2. 环境变量
cp server/.env.example server/.env   # 填 SECRET_KEY / MYSQL_* / AI_BASE_URL+AI_API_KEY+AI_MODEL（OpenAI 兼容）

# 3. 后端（端口 5000）
cd server && python app.py

# 4. 前端（端口 5173）
cd client && npm install && npm run dev
```

> 运行环境：Python 3.13 + Node 20 + MySQL 8（本机服务）；生产部署见 `docs/DEPLOY.md`，当前线上 https://ink.shenghui2026.top。

## 测试

```bash
cd server && python -m pytest tests -q    # 后端 96 用例
cd client && npm run test:util            # 前端渲染工具单测
cd e2e && npx playwright test             # E2E（需先起 Mock 环境，见 e2e/）
```

- pytest 一律连接独立测试库 **inkstone_test**（不触碰开发库 inkstone）；
- 每会话自动重建库表、每用例清空数据与限速计数，可重复执行、相互独立；
- AI 相关用例全部 stub 真实模型调用（零 token 消耗）。

## 版本控制红线

- `.env`、`client/dist/`、`server/uploads/`、`node_modules/`、`_备份/`、日志、缓存一律不提交（见 `.gitignore`）；
- 示例配置提交 `.env.example`；改动文档与代码必须同步（避免历史遗留的"文档数字失真"问题）。

## 文档索引

- `docs/项目详解文档.md` — **老师讲解版**：架构/数据模型/工作流/演示脚本/FAQ
- `docs/成书工作流方案.md` — 三阶段工作流（起·承·合）产品与数据设计
- `docs/DEPLOY.md` / `docs/上线记录.md` — 生产部署手册与线上变更记录
- `docs/存档说明.md` — 版本快照与 GitHub 归档说明（remote: `ShengHR-hub/vibe-coding` @ `inkstone-archive`）
- `docs/改造守则.md` — 改造期"不劣化契约"（步骤规程/红线/决策记录）
- `docs/改造进度.md` — 分步变更登记与测试证据
- `docs/灵感馆方向.md` / `docs/写作强化计划.md` — 方向决策与写作主线强化记录
- `docs/REQUIREMENTS.md` — 毕设原始需求规格（历史留档）
- `docs/墨池阅读模块需求文档.md` / `docs/阅读模块实施计划.md` — 已作废（书库下线），留档备查
