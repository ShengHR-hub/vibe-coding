<template>
  <div class="home-fullpage" ref="container">
    <FluidCursor />

    <!-- 左上角墨池标志 -->
    <div class="corner-area">
      <InkstoneLogo />
    </div>

    <!-- 右上角用户区域 -->
    <div class="user-area">
      <UserMenu />
    </div>

    <!-- 浮动装饰光点 -->
    <div class="floating-orbs">
      <span class="f-orb f-orb-1"></span>
      <span class="f-orb f-orb-2"></span>
      <span class="f-orb f-orb-3"></span>
      <span class="f-diamond f-diamond-1">&#x2666;</span>
      <span class="f-diamond f-diamond-2">&#x2666;</span>
      <span class="f-ring f-ring-1"></span>
    </div>

    <div class="scroll-indicator" ref="indicator">
      <span class="indicator-dot" v-for="i in totalSections" :key="i" :class="{ active: currentSection === i - 1 }" @click="scrollToSection(i - 1)"></span>
    </div>

    <!-- ====== 1. Hero ====== -->
    <section class="fp-section section-hero">
      <div class="section-inner">
        <div class="hero-glow-ring"></div>
        <p class="hero-overline">Inkstone</p>
        <MorphingText :texts="heroTexts" class="hero-morphing" />
        <p class="hero-subtitle">Where ink blooms into art</p>
        <div class="hero-divider"></div>
        <p class="hero-desc">墨池是一个 AI 驱动的读写一体化平台，涵盖 AI 写作工作室、沉浸式阅读系统、<br>出版连载、角色扮演、社区互动、挑战赛、数据仪表盘等 28 个功能模块。</p>
        <div class="hero-portals">
          <router-link to="/write" class="portal-card portal-write">
            <span class="portal-en">Writing</span>
            <span class="portal-title">开始写作</span>
            <span class="portal-sub">AI 续写 · 灵感激发 · 角色塑造</span>
            <span class="portal-line"></span>
          </router-link>
          <router-link to="/library?from=reading" class="portal-card portal-read">
            <span class="portal-en">Reading</span>
            <span class="portal-title">开始阅读</span>
            <span class="portal-sub">书库探索 · 沉浸阅读 · 批注打卡</span>
            <span class="portal-line"></span>
          </router-link>
          <router-link to="/explore" class="portal-card portal-community">
            <span class="portal-en">Community</span>
            <span class="portal-title">社区广场</span>
            <span class="portal-sub">发现作品 · 互动交流 · 排行榜</span>
            <span class="portal-line"></span>
          </router-link>
        </div>
        <p class="hero-hint">Scroll to explore</p>
        <span class="scroll-arrow">&darr;</span>
      </div>
    </section>

    <!-- ====== 2. 平台概览 ====== -->
    <section class="fp-section section-overview">
      <div class="section-inner">
        <p class="sec-tag">Overview <span class="tag-cn">概览</span></p>
        <h2 class="sec-heading">读写一体<br>智能创作空间</h2>
        <p class="sec-subtitle">
          28 个功能模块覆盖创作与阅读的每一个环节——从 AI 辅助写作到沉浸式阅读，<br>
          从社区互动到数据驱动的成长体系，读与写在这里深度融合。
        </p>
        <div class="stat-row">
          <div class="stat-card" v-for="s in stats" :key="s.label">
            <span class="stat-num" :data-target="s.num">{{ s.num }}</span>
            <span class="stat-label">{{ s.label }}</span>
            <span class="stat-desc">{{ s.desc }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ====== 3. AI 写作工作室 ====== -->
    <section class="fp-section section-feature-detail">
      <div class="section-inner split-layout">
        <div class="split-text">
          <span class="feature-badge">01</span>
          <h2 class="sec-heading">AI Writing<br>Studio</h2>
          <h3 class="feature-cn-title">AI 写作工作室</h3>
          <p class="feature-long-desc">
            7 大 AI 能力覆盖创作全流程。智能续写通过 SSE 流式响应实时生成，支持多种文风；灵感激发从关键词挖掘故事创意；大纲规划自动生成分章结构；角色塑造构建五维立体人物；润色优化提供四种模式；文字诊断从七个维度深度分析；AI 对话助手随时讨论创意。
          </p>
          <ul class="feature-points">
            <li>智能续写：上下文感知 + SSE 流式 + 多文风支持</li>
            <li>灵感激发 / 大纲规划 / 角色塑造：从构思到成型</li>
            <li>润色优化（4 模式）+ 文字诊断（7 维度分析）</li>
            <li>AI 对话助手：多轮讨论创意，自动保存历史</li>
            <li>章节摘要生成：一键提炼章节核心内容</li>
          </ul>
        </div>
        <div class="split-visual">
          <div class="visual-card shimmer-card">
            <span class="visual-icon">→</span>
            <div class="visual-demo">
              <p class="demo-line prompt">她推开那扇尘封已久的门，</p>
              <p class="demo-line ai">阳光透过裂缝洒进来，映出空气中飞舞的微尘。房间里弥漫着旧书和时光的气味——那是祖母留下的图书馆，每一本书都藏着一个未完成的故事。</p>
            </div>
            <div class="card-shimmer"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- ====== 4. 沉浸式阅读系统 ====== -->
    <section class="fp-section section-feature-detail">
      <div class="section-inner split-layout reverse">
        <div class="split-visual">
          <div class="visual-card shimmer-card">
            <span class="visual-icon"> </span>
            <div class="visual-demo">
              <div class="reading-demo">
                <div class="rd-progress">
                  <span class="rd-label">阅读进度</span>
                  <div class="rd-bar"><div class="rd-fill" style="width:68%"></div></div>
                  <span class="rd-pct">68%</span>
                </div>
                <div class="rd-tools">
                  <span class="rd-tag">  书签</span>
                  <span class="rd-tag">  批注</span>
                  <span class="rd-tag">✨ 好句</span>
                  <span class="rd-tag">  打卡</span>
                </div>
              </div>
            </div>
            <div class="card-shimmer"></div>
          </div>
        </div>
        <div class="split-text">
          <span class="feature-badge">02</span>
          <h2 class="sec-heading">Immersive<br>Reading</h2>
          <h3 class="feature-cn-title">沉浸式阅读系统</h3>
          <p class="feature-long-desc">
            完整的阅读体验闭环。个人书架管理想读、在读、已读书籍；阅读进度精确到章节和滚动百分比，自动同步书架状态；书签标记精彩段落，批注记录阅读感悟，好句标记可一键同步到写作素材库。还有阅读打卡、阅读目标、阅读热力图、年度阅读报告等丰富的数据追踪。
          </p>
          <ul class="feature-points">
            <li>个人书架：分组管理 + 自定义书单 + 批量操作</li>
            <li>阅读进度：章节级追踪 + 自动流转（想读→在读→已读）</li>
            <li>书签 / 批注 / 好句标记：完整的阅读笔记体系</li>
            <li>阅读打卡 + 热力图 + 目标设定 + 年度报告</li>
            <li>好句一键同步到写作素材库，读写深度融合</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- ====== 5. 书库与出版连载 ====== -->
    <section class="fp-section section-feature-detail">
      <div class="section-inner split-layout">
        <div class="split-text">
          <span class="feature-badge">03</span>
          <h2 class="sec-heading">Library &<br>Serialization</h2>
          <h3 class="feature-cn-title">书库与出版连载</h3>
          <p class="feature-long-desc">
            双轨书库系统——用户创作的作品与外部导入的书籍统一管理。支持 TXT 文件上传自动解析章节，书库排行榜多维度推荐，AI 基于阅读偏好智能推荐同类书籍。出版连载系统支持卷管理、章节分配、连载状态切换，满足长篇连载需求。
          </p>
          <ul class="feature-points">
            <li>双轨书库：用户创作 + 外部导入，统一搜索浏览</li>
            <li>TXT 上传自动解析：正则识别章节标题 + 编码检测</li>
            <li>书库排行榜：热门 / 评分 / 最新，多维度推荐</li>
            <li>出版连载：卷管理 + 章节分配 + 连载/完结/暂停状态</li>
            <li>AI 推荐：基于阅读偏好分析推荐同类热门书籍</li>
          </ul>
        </div>
        <div class="split-visual">
          <div class="visual-card shimmer-card">
            <span class="visual-icon"> </span>
            <div class="outline-tree">
              <div class="ot-item ot-l1">  书库浏览</div>
              <div class="ot-item ot-l2">  热门排行 · 评分排行</div>
              <div class="ot-item ot-l2">  TXT 上传 · 自动解析</div>
              <div class="ot-item ot-l1">  出版连载</div>
              <div class="ot-item ot-l2">卷管理 · 章节分配</div>
              <div class="ot-item ot-l2">连载中 / 已完结 / 暂停</div>
            </div>
            <div class="card-shimmer"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- ====== 6. 角色系统与角色扮演 ====== -->
    <section class="fp-section section-feature-detail">
      <div class="section-inner split-layout reverse">
        <div class="split-visual">
          <div class="visual-card shimmer-card">
            <span class="visual-icon">♛</span>
            <div class="char-card">
              <div class="char-header">
                <span class="char-avatar">林</span>
                <div class="char-meta">
                  <strong>林墨白</strong>
                  <span>28岁 · 考古学家</span>
                </div>
              </div>
              <div class="char-traits">
                <span>好奇心旺盛</span><span>略带偏执</span><span>内心柔软</span>
              </div>
              <p class="char-bio">生于书香门第，幼年随祖父出入各地古迹，练就一双看透千年尘埃的眼睛。不相信巧合，却总被命运捉弄。</p>
            </div>
            <div class="card-shimmer"></div>
          </div>
        </div>
        <div class="split-text">
          <span class="feature-badge">04</span>
          <h2 class="sec-heading">Character &<br>Role Play</h2>
          <h3 class="feature-cn-title">角色系统与角色扮演</h3>
          <p class="feature-long-desc">
            角色系统不止于设定卡片。AI 可从作品文本中自动提取角色设定，生成人物关系图谱和剧情时间线。角色扮演功能让你与笔下的角色进行沉浸式对话——AI 严格保持角色性格和说话风格，帮你检验人物的一致性，发现性格中的盲点。
          </p>
          <ul class="feature-points">
            <li>AI 角色提取：从作品文本自动提取角色设定（最多 8 个）</li>
            <li>角色关系图谱：AI 分析人物关联与冲突，可视化展示</li>
            <li>剧情时间线：按章节提取关键事件，梳理故事脉络</li>
            <li>角色扮演聊天：SSE 流式对话，严格保持角色人格</li>
            <li>角色设定五维：外貌 / 性格 / 背景 / 动机 / 说话风格</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- ====== 7. 挑战赛与每日练习 ====== -->
    <section class="fp-section section-feature-detail">
      <div class="section-inner split-layout">
        <div class="split-text">
          <span class="feature-badge">05</span>
          <h2 class="sec-heading">Challenges &amp;<br>Daily Practice</h2>
          <h3 class="feature-cn-title">挑战赛与每日练习</h3>
          <p class="feature-long-desc">
            写作是需要坚持的习惯。挑战赛系统提供 30 天写作马拉松、古风诗词挑战、科幻微小说大赛等多种活动，每日打卡记录进度，接龙段落让多人协作创作。每日练习提供精选题目（微小说、诗歌、对话、描写、续写），提交后参与社区投票排行。
          </p>
          <ul class="feature-points">
            <li>挑战赛：参与 / 每日打卡 / 进度追踪 / 接龙创作</li>
            <li>每日练习：5 种题型 + 字数要求 + 难度分级</li>
            <li>练习提交与社区投票，点赞排行</li>
            <li>连续打卡天数统计，培养写作习惯</li>
          </ul>
        </div>
        <div class="split-visual">
          <div class="visual-card shimmer-card">
            <span class="visual-icon"> </span>
            <div class="visual-demo">
              <div class="outline-tree">
                <div class="ot-item ot-l1">  30天写作马拉松</div>
                <div class="ot-item ot-l2">每日打卡 · 进度追踪</div>
                <div class="ot-item ot-l1">  每日练习</div>
                <div class="ot-item ot-l2">微小说 · 诗歌 · 对话</div>
                <div class="ot-item ot-l2">描写 · 续写 · 社区投票</div>
              </div>
            </div>
            <div class="card-shimmer"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- ====== 8. 数据仪表盘与 AI 分析 ====== -->
    <section class="fp-section section-feature-detail">
      <div class="section-inner split-layout reverse">
        <div class="split-visual">
          <div class="visual-card shimmer-card">
            <span class="visual-icon"> </span>
            <div class="outline-tree">
              <div class="ot-item ot-l1">  写作数据仪表盘</div>
              <div class="ot-item ot-l2">总字数 · 连续天数 · 日均产出</div>
              <div class="ot-item ot-l2">年度热力图 · 月度趋势</div>
              <div class="ot-item ot-l1">  AI 风格分析</div>
              <div class="ot-item ot-l2">文艺 / 朴实 / 幽默 / 激昂 / 忧郁</div>
              <div class="ot-item ot-l1">  月度写作报告</div>
              <div class="ot-item ot-l2">AI 生成个性化写作建议</div>
            </div>
            <div class="card-shimmer"></div>
          </div>
        </div>
        <div class="split-text">
          <span class="feature-badge">06</span>
          <h2 class="sec-heading">Analytics &amp;<br>AI Insight</h2>
          <h3 class="feature-cn-title">数据仪表盘与 AI 分析</h3>
          <p class="feature-long-desc">
            用数据驱动创作成长。写作仪表盘追踪总字数、连续写作天数、日均产出、周/月对比；年度热力图可视化你的创作节奏；AI 风格分析从文艺、朴实、幽默、激昂、忧郁五个维度量化你的文笔特征；月度报告由 AI 生成个性化写作建议和鼓励。
          </p>
          <ul class="feature-points">
            <li>写作仪表盘：总览 + 热力图 + 月度趋势 + 会话记录</li>
            <li>AI 风格分析：五维度雷达图，量化你的文笔特征</li>
            <li>AI 月度报告：自动生成个性化写作建议</li>
            <li>阅读报告：周报 / 月报 / 年报 / 阅读速度分析</li>
            <li>作品版本快照：每次修改自动保存，支持任意回退</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- ====== 9. 社区与诗词素材 ====== -->
    <section class="fp-section section-community">
      <div class="section-inner">
        <p class="sec-tag">Community <span class="tag-cn">社区与资源</span></p>
        <h2 class="sec-heading">Share &amp;<br>Discover</h2>
        <p class="sec-subtitle">
          创作不是孤独的事。在墨池社区发布作品、发现同好、交流技巧。<br>
          诗词库收录 150+ 首精选古诗词，素材库提供海量写作素材，每日推荐实时获取。
        </p>
        <div class="comm-grid">
          <div class="comm-card" v-for="c in community" :key="c.en">
            <div class="comm-icon-box">
              <span class="comm-icon">{{ c.icon }}</span>
            </div>
            <span class="comm-en">{{ c.en }}</span>
            <span class="comm-cn">{{ c.cn }}</span>
            <p class="comm-desc">{{ c.desc }}</p>
            <div class="card-shimmer"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- ====== 10. 每日精选诗词 ====== -->
    <section class="fp-section section-featured">
      <div class="section-inner">
        <p class="sec-tag">Daily Picks <span class="tag-cn">每日精选</span></p>
        <h2 class="sec-heading">Poetry<br>Inspirations</h2>
        <p class="sec-subtitle">
          每日精选古典诗词，为你的创作注入千年文韵。<br>
          轮播自动切换，悬停暂停，点击卡片沉浸阅读。
        </p>
        <div class="featured-wrapper">
          <FeaturedPoemsCarousel :poems="featuredPoems" />
        </div>
      </div>
    </section>

    <!-- ====== 11. 成就 & 成长体系 ====== -->
    <section class="fp-section section-achievements">
      <div class="section-inner">
        <p class="sec-tag">Growth <span class="tag-cn">成长</span></p>
        <h2 class="sec-heading">Level Up<br>Your Craft</h2>
        <p class="sec-subtitle">
          每一次创作和阅读都在积累经验。从"初窥门径"到"文坛巨匠"，<br>
          18 种成就覆盖写作、阅读、社交全场景，你的每个字都算数。
        </p>
        <div class="level-row">
          <div class="level-card" v-for="l in levels" :key="l.level">
            <span class="level-num">Lv.{{ l.level }}</span>
            <span class="level-name">{{ l.name }}</span>
            <span class="level-exp">{{ l.exp }}</span>
            <div class="card-shimmer"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- ====== 12. CTA ====== -->
    <section class="fp-section section-cta">
      <div class="section-inner">
        <h2 class="sec-heading cta-heading">Ready to<br>Create?</h2>
        <p class="sec-subtitle">加入墨池，28 个模块、155 个端点、42 个页面，<br>打造属于你的读写一体化空间</p>
        <div class="cta-buttons">
          <router-link to="/write" class="cta-btn cta-primary pulse-glow">
            <span>Start Writing</span>
            <span class="cta-arrow">&rarr;</span>
          </router-link>
          <router-link to="/library" class="cta-btn cta-ghost">
            <span>Start Reading</span>
            <span class="cta-arrow">&rarr;</span>
          </router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import FluidCursor from '../components/FluidCursor.vue'
import FeaturedPoemsCarousel from '../components/FeaturedPoemsCarousel.vue'
import MorphingText from '../components/MorphingText.vue'
import InkstoneLogo from '../components/InkstoneLogo.vue'
import UserMenu from '../components/UserMenu.vue'
import { api } from '../api/index.js'
import { useUserStore } from '../stores/user.js'

gsap.registerPlugin(ScrollTrigger)

const router = useRouter()
const userStore = useUserStore()

const totalSections = 12
const currentSection = ref(0)
const container = ref(null)
const indicator = ref(null)
const featuredPoems = ref([])
const heroTexts = ['以墨为池', '字字生花', '让文字自由生长']

const stats = [
  { num: 28, label: '功能模块', desc: '覆盖读写全场景' },
  { num: 155, label: 'API 端点', desc: '每个细节都打磨到位' },
  { num: 42, label: '页面', desc: '完整的产品体验' },
  { num: 36, label: '数据表', desc: '严谨的数据架构' },
]

const samplePrompts = [
  '用赛博朋克风格描写一个雨夜的街头场景',
  '为我的主角设计一个令人心碎的背景故事',
  '帮我构思三个意想不到的情节转折',
  '写一段关于离别的不落俗套的对话',
  '用五感描写法重新写这段场景',
]

const community = [
  { icon: '♥', en: 'Like', cn: '点赞互动', desc: '为喜欢的作品送上欣赏，优质内容获得更多曝光' },
  { icon: '★', en: 'Favorite', cn: '收藏关注', desc: '收藏好文随时回顾，关注作者不遗漏新作品' },
  { icon: '✎', en: 'Comment', cn: '评论交流', desc: '嵌套评论 + 置顶评论，深度交流创作心得' },
  { icon: '✨', en: 'Poems', cn: '诗词库', desc: '150+ 精选古典诗词，分类浏览，每日推荐' },
  { icon: '☆', en: 'Materials', cn: '素材库', desc: '海量写作素材，分类检索，好句一键同步' },
  { icon: '♕', en: 'Rankings', cn: '排行榜', desc: '作品 / 作者 / 周榜 / 新作，多维度排行' },
]

const levels = ref([
  { level: 1, name: '初窥门径', exp: 0 },
  { level: 3, name: '小有所成', exp: 500 },
  { level: 5, name: '妙笔生花', exp: 5000 },
  { level: 7, name: '才华横溢', exp: 30000 },
  { level: 10, name: '文坛巨匠', exp: 500000 },
])

let stTriggers = []
let tiltCleanups = []
let floatingAnims = []

function animateCounters() {
  document.querySelectorAll('.stat-num').forEach(el => {
    const target = parseInt(el.getAttribute('data-target'))
    if (!target) return
    const obj = { val: 0 }
    gsap.fromTo(obj, { val: 0 }, {
      val: target,
      duration: 2.5,
      ease: 'power2.out',
      snap: { val: 1 },
      onUpdate: () => { el.textContent = Math.round(obj.val) },
      scrollTrigger: {
        trigger: el.closest('.stat-row'),
        start: 'top 75%',
      },
    })
  })
}

function bindTilt() {
  document.querySelectorAll('.visual-card, .comm-card, .level-card').forEach(card => {
    const onMove = (e) => {
      const rect = card.getBoundingClientRect()
      const x = (e.clientX - rect.left) / rect.width - 0.5
      const y = (e.clientY - rect.top) / rect.height - 0.5
      gsap.to(card, { rotateY: x * 10, rotateX: -y * 10, duration: 0.4, ease: 'power2.out' })
    }
    const onLeave = () => {
      gsap.to(card, { rotateY: 0, rotateX: 0, duration: 0.7, ease: 'elastic.out(1, 0.4)' })
    }
    card.addEventListener('mousemove', onMove)
    card.addEventListener('mouseleave', onLeave)
    tiltCleanups.push({ card, onMove, onLeave })
  })
}

function unbindTilt() {
  tiltCleanups.forEach(({ card, onMove, onLeave }) => {
    card.removeEventListener('mousemove', onMove)
    card.removeEventListener('mouseleave', onLeave)
  })
  tiltCleanups = []
}

function scrollToSection(idx) {
  const sections = document.querySelectorAll('.fp-section')
  if (sections[idx]) {
    sections[idx].scrollIntoView({ behavior: 'smooth' })
  }
}

onMounted(async () => {
  // 获取每日精选诗词
  try {
    const res = await api.get('/api/poems/featured?count=7')
    if (res.code === 0) featuredPoems.value = res.data.poems
  } catch {}

  // 获取等级定义（从 API 而非硬编码）
  try {
    const res = await api.get('/api/users/levels')
    if (res.code === 0) {
      const allLevels = res.data.levels
      // 只展示关键等级节点
      const showcase = [1, 3, 5, 7, 10]
      levels.value = allLevels.filter(l => showcase.includes(l.level))
    }
  } catch {}

  nextTick(() => {
    const sectionsEl = document.querySelectorAll('.fp-section')

    sectionsEl.forEach((section, i) => {
      const tl = gsap.timeline({ paused: true })
      const isHero = i === 0
      const isSplit = section.classList.contains('section-feature-detail')
      const isCommunity = section.classList.contains('section-community')
      const isFeatured = section.classList.contains('section-featured')
      const isAchievements = section.classList.contains('section-achievements')

      if (isHero) {
        // === Hero: 分层浮现 ===
        tl.fromTo('.hero-overline', { y: 16, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, ease: 'power3.out' })
        tl.fromTo('.hero-glow-ring', { scale: 0.3, opacity: 0 }, { scale: 1, opacity: 0.5, duration: 2, ease: 'elastic.out(1, 0.6)' }, '-=0.2')
        tl.fromTo('.hero-morphing', { y: 30, opacity: 0 }, { y: 0, opacity: 1, duration: 0.8, ease: 'power3.out' }, '-=1.5')
        tl.fromTo('.hero-subtitle', { opacity: 0 }, { opacity: 1, duration: 0.7 }, '-=0.3')
        tl.fromTo('.hero-divider', { scaleX: 0, opacity: 0 }, { scaleX: 1, opacity: 1, duration: 0.8, ease: 'power3.inOut' }, '-=0.3')
        tl.fromTo('.hero-desc, .hero-portals', { y: 16, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, stagger: 0.1, ease: 'power3.out' }, '-=0.2')
        tl.fromTo('.hero-hint', { opacity: 0 }, { opacity: 1, duration: 0.4 }, '-=0.1')
        tl.fromTo('.scroll-arrow', { y: -6, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5 })
        tl.play()
      } else if (isSplit) {
        tl.fromTo(section.querySelector('.split-text').children, {
          y: 50, opacity: 0,
        }, {
          y: 0, opacity: 1, duration: 0.55, stagger: 0.06, ease: 'power3.out',
        })
        tl.fromTo(section.querySelector('.split-visual'), {
          y: 60, opacity: 0, scale: 0.9, rotateY: -15,
        }, {
          y: 0, opacity: 1, scale: 1, rotateY: 0,
          duration: 0.8, ease: 'back.out(1.4)',
        }, '-=0.35')
      } else if (isCommunity) {
        tl.fromTo('.section-community .sec-tag, .section-community .sec-heading, .section-community .sec-subtitle', {
          y: 30, opacity: 0,
        }, {
          y: 0, opacity: 1, duration: 0.5, stagger: 0.08, ease: 'power3.out',
        })
        tl.fromTo('.comm-card', {
          y: 80, opacity: 0, scale: 0.7, rotateY: 30,
        }, {
          y: 0, opacity: 1, scale: 1, rotateY: 0,
          duration: 0.8, stagger: 0.1, ease: 'back.out(1.5)',
        }, '-=0.15')
      } else if (isFeatured) {
        tl.fromTo('.section-featured .sec-tag, .section-featured .sec-heading, .section-featured .sec-subtitle', {
          y: 30, opacity: 0,
        }, {
          y: 0, opacity: 1, duration: 0.5, stagger: 0.08, ease: 'power3.out',
        })
        tl.fromTo('.featured-wrapper', {
          y: 60, opacity: 0, scale: 0.92,
        }, {
          y: 0, opacity: 1, scale: 1,
          duration: 1, ease: 'power3.out',
        }, '-=0.2')
      } else if (isAchievements) {
        tl.fromTo('.section-achievements .sec-tag, .section-achievements .sec-heading, .section-achievements .sec-subtitle', {
          y: 30, opacity: 0,
        }, {
          y: 0, opacity: 1, duration: 0.5, stagger: 0.08, ease: 'power3.out',
        })
        tl.fromTo('.level-card', {
          y: 50, opacity: 0, scale: 0.8,
        }, {
          y: 0, opacity: 1, scale: 1,
          duration: 0.6, stagger: 0.1, ease: 'elastic.out(1, 0.7)',
        }, '-=0.1')
      } else {
        tl.fromTo(section.querySelector('.section-inner').children, {
          y: 40, opacity: 0,
        }, {
          y: 0, opacity: 1, duration: 0.6, stagger: 0.06, ease: 'power3.out',
        })
      }

      const st = ScrollTrigger.create({
        trigger: section,
        start: 'top 55%',
        onEnter: () => { currentSection.value = i; tl.play() },
        onEnterBack: () => { currentSection.value = i; tl.play() },
      })
      stTriggers.push(st)
    })

    // 数字滚动
    animateCounters()

    // 箭头弹跳
    gsap.to('.scroll-arrow', { y: 10, duration: 1.2, repeat: -1, yoyo: true, ease: 'power1.inOut' })

    // 3D tilt
    bindTilt()

    // 浮动光点持续动画
    floatingAnims = [
      gsap.to('.f-orb-1', { y: -30, x: 20, duration: 8, repeat: -1, yoyo: true, ease: 'sine.inOut' }),
      gsap.to('.f-orb-2', { y: 25, x: -20, duration: 10, repeat: -1, yoyo: true, ease: 'sine.inOut' }),
      gsap.to('.f-orb-3', { y: -20, x: -15, duration: 7, repeat: -1, yoyo: true, ease: 'sine.inOut' }),
      gsap.to('.f-diamond-1', { y: -40, rotate: 180, duration: 12, repeat: -1, yoyo: true, ease: 'sine.inOut' }),
      gsap.to('.f-diamond-2', { y: 30, rotate: -180, duration: 9, repeat: -1, yoyo: true, ease: 'sine.inOut' }),
      gsap.to('.f-ring-1', { scale: 1.2, opacity: 0.15, duration: 6, repeat: -1, yoyo: true, ease: 'sine.inOut' }),
    ]
  })
})

onUnmounted(() => {
  stTriggers.forEach(st => st.kill())
  floatingAnims.forEach(a => a.kill())
  unbindTilt()
})
</script>

<style scoped>
.home-fullpage {
  position: relative; z-index: 1;
}

/* 左上角标志 */
.corner-area {
  position: fixed;
  top: 16px;
  left: 24px;
  z-index: 101;
}

/* 右上角用户区域 */
.user-area {
  position: fixed;
  top: 16px;
  right: 24px;
  z-index: 101;
}

/* ====== 浮动装饰 ====== */
.floating-orbs {
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  overflow: hidden;
}
.f-orb {
  position: absolute; border-radius: 50%;
  background: radial-gradient(circle, rgba(196,163,90,0.15), transparent 70%);
}
.f-orb-1 { width: 300px; height: 300px; top: 15%; right: -80px; }
.f-orb-2 { width: 200px; height: 200px; top: 55%; left: -60px; }
.f-orb-3 { width: 250px; height: 250px; bottom: 20%; right: 30%; }
.f-diamond {
  position: absolute; font-size: 1.2rem;
  color: var(--accent-primary); opacity: 0.2;
}
.f-diamond-1 { top: 30%; left: 10%; }
.f-diamond-2 { bottom: 25%; right: 15%; }
.f-ring {
  position: absolute;
  width: 400px; height: 400px;
  border-radius: 50%;
  border: 1px solid rgba(196,163,90,0.06);
  top: 40%; left: 50%;
  transform: translate(-50%, -50%);
  opacity: 0.08;
}

/* ====== 滚动指示器 ====== */
.scroll-indicator {
  position: fixed; right: 24px; top: 50%;
  transform: translateY(-50%); z-index: 90;
  display: flex; flex-direction: column; gap: 10px;
}
.indicator-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: rgba(255,255,255,0.12);
  transition: all 0.4s ease;
  cursor: pointer;
}
.indicator-dot:hover {
  background: rgba(196,163,90,0.4);
}
.indicator-dot.active {
  background: var(--accent-primary);
  box-shadow: 0 0 6px rgba(196,163,90,0.5);
}

/* ====== 每屏 ====== */
.fp-section {
  min-height: 100vh;
  display: flex; align-items: center; justify-content: center;
  padding: 3rem 2rem; position: relative;
}
.section-inner { max-width: 1000px; width: 100%; text-align: center; }

/* ====== 通用标签 ====== */
.sec-tag {
  font-family: var(--font-display);
  font-size: 0.85rem; font-weight: 600; letter-spacing: 0.25em;
  color: var(--accent-primary); text-transform: uppercase;
  margin-bottom: 1.25rem; opacity: 0.85;
}
.tag-cn {
  font-family: var(--font-sans);
  font-size: 0.8rem; font-weight: 400; letter-spacing: 0.15em;
  color: var(--text-muted); margin-left: 0.5rem; text-transform: none;
}
.sec-heading {
  font-family: var(--font-display);
  font-size: clamp(2.4rem, 4.5vw, 3.6rem); font-weight: 700;
  color: var(--text-primary); line-height: 1.15; letter-spacing: 0.01em;
  margin-bottom: 1.25rem;
}
.sec-subtitle {
  font-size: 1rem; color: var(--text-muted);
  line-height: 2; letter-spacing: 0.05em;
}

/* ====== Hero ====== */
.section-hero { padding-top: 0; }
.hero-glow-ring {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 500px; height: 500px; border-radius: 50%;
  background: radial-gradient(circle, rgba(196,163,90,0.04), transparent 70%);
  pointer-events: none;
}
.hero-overline {
  font-family: var(--font-display);
  font-size: 0.95rem; font-weight: 600; letter-spacing: 0.35em;
  color: var(--accent-primary); text-transform: uppercase;
  opacity: 0.8; margin-bottom: 1.5rem; position: relative;
}
.hero-morphing {
  margin-bottom: 1.25rem;
  filter: drop-shadow(0 0 30px rgba(196,163,90,0.2));
}
.hero-subtitle {
  font-family: var(--font-display);
  font-size: 1.1rem; font-style: italic;
  color: var(--text-muted); letter-spacing: 0.06em;
  opacity: 0.7; margin-bottom: 2rem;
}
.hero-divider {
  width: 60px; height: 1px; background: var(--accent-primary);
  opacity: 0.5; margin: 0 auto 2rem;
}
.hero-desc {
  font-size: 0.95rem; color: var(--text-muted);
  line-height: 2; letter-spacing: 0.05em;
  max-width: 600px; margin: 0 auto 2rem;
}
.hero-cta { margin-bottom: 2.5rem; }
.hero-portals {
  display: flex; gap: 2rem; justify-content: center;
  margin-bottom: 2.5rem; flex-wrap: wrap;
}
.portal-card {
  display: flex; flex-direction: column; align-items: center;
  padding: 2rem 2.8rem; border-radius: 2px;
  text-decoration: none; transition: all 0.5s cubic-bezier(0.16,1,0.3,1);
  min-width: 220px; position: relative; overflow: hidden;
  background: transparent;
  border: 1px solid rgba(255,255,255,0.08);
}
.portal-card:hover {
  transform: translateY(-3px);
  border-color: rgba(255,255,255,0.15);
}
.portal-write:hover {
  background: rgba(196,163,90,0.04);
  box-shadow: 0 20px 60px rgba(196,163,90,0.08);
}
.portal-read:hover {
  background: rgba(167,139,250,0.04);
  box-shadow: 0 20px 60px rgba(167,139,250,0.08);
}
.portal-community:hover {
  background: rgba(52,211,153,0.04);
  box-shadow: 0 20px 60px rgba(52,211,153,0.08);
}
.portal-en {
  font-family: var(--font-display);
  font-size: 0.7rem; font-weight: 600;
  letter-spacing: 0.3em; text-transform: uppercase;
  color: var(--text-muted); opacity: 0.5;
  margin-bottom: 0.6rem;
}
.portal-title {
  font-family: var(--font-serif);
  font-size: 1.35rem; font-weight: 700;
  color: var(--text-primary); letter-spacing: 0.12em;
  margin-bottom: 0.5rem;
}
.portal-sub {
  font-size: 0.75rem; color: var(--text-muted);
  letter-spacing: 0.06em;
}
.portal-line {
  position: absolute; bottom: 0; left: 50%;
  transform: translateX(-50%); width: 0; height: 1px;
  transition: width 0.5s cubic-bezier(0.16,1,0.3,1);
}
.portal-write .portal-line { background: var(--accent-primary); }
.portal-read .portal-line { background: var(--accent-purple); }
.portal-community .portal-line { background: #34d399; }
.portal-card:hover .portal-line { width: 60%; }
.hero-hint {
  font-family: var(--font-display);
  font-size: 0.75rem; letter-spacing: 0.25em;
  color: var(--text-muted); text-transform: uppercase;
  opacity: 0.5; margin-bottom: 0.5rem;
}
.scroll-arrow { display: block; font-size: 1.1rem; color: var(--accent-primary); opacity: 0.5; }

/* ====== 统计行 ====== */
.stat-row {
  display: flex; justify-content: center; gap: 3rem;
  margin-top: 3rem; flex-wrap: wrap;
}
.stat-card {
  display: flex; flex-direction: column; align-items: center;
  gap: 0.15rem; padding: 1rem 1.5rem;
}
.stat-num {
  font-family: var(--font-display);
  font-size: 3rem; font-weight: 700;
  color: var(--accent-primary); line-height: 1;
  font-variant-numeric: tabular-nums;
}
.stat-label { font-size: 0.95rem; font-weight: 600; color: var(--text-primary); letter-spacing: 0.04em; }
.stat-desc { font-size: 0.78rem; color: var(--text-muted); letter-spacing: 0.06em; }

/* ====== 左右分栏 ====== */
.split-layout { display: flex; align-items: center; gap: 4rem; text-align: left; }
.split-layout.reverse { flex-direction: row-reverse; }
.split-text { flex: 1; min-width: 0; }
.split-visual { flex: 0 0 380px; }

.feature-badge {
  display: inline-block;
  font-family: var(--font-display);
  font-size: 0.75rem; font-weight: 700; letter-spacing: 0.2em;
  color: var(--accent-primary); opacity: 0.6;
  border: 1px solid rgba(196,163,90,0.25);
  border-radius: 20px; padding: 4px 14px;
  margin-bottom: 1.5rem;
}
.feature-cn-title {
  font-family: var(--font-serif);
  font-size: 1.3rem; font-weight: 700;
  color: var(--accent-primary); letter-spacing: 0.06em;
  margin-bottom: 1rem;
}
.feature-long-desc {
  font-size: 0.9rem; color: var(--text-secondary);
  line-height: 1.9; letter-spacing: 0.04em;
  margin-bottom: 1.5rem;
}
.feature-points {
  list-style: none; padding: 0;
  display: flex; flex-direction: column; gap: 0.6rem;
}
.feature-points li {
  font-size: 0.85rem; color: var(--text-muted);
  line-height: 1.6; letter-spacing: 0.03em;
  padding-left: 1.2rem; position: relative;
}
.feature-points li::before {
  content: '—'; position: absolute; left: 0;
  color: var(--accent-primary); opacity: 0.5;
}

/* ====== 可视化卡片 ====== */
.visual-card {
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 20px;
  padding: 2rem;
  position: relative; overflow: hidden;
  transition: border-color 0.35s ease, box-shadow 0.35s ease;
  transform-style: preserve-3d;
}
.visual-card:hover {
  border-color: rgba(196,163,90,0.2);
  box-shadow: 0 20px 60px rgba(0,0,0,0.5);
}
.visual-icon {
  position: absolute; top: -16px; right: -16px;
  width: 36px; height: 36px; border-radius: 50%;
  background: rgba(196,163,90,0.15);
  border: 1px solid rgba(196,163,90,0.3);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.95rem; color: var(--accent-primary);
}
.visual-demo { margin-top: 0.5rem; position: relative; z-index: 1; }
.demo-line { font-size: 0.85rem; line-height: 1.8; letter-spacing: 0.04em; margin-bottom: 0.5rem; }
.demo-line.prompt { color: var(--text-muted); font-style: italic; }
.demo-line.ai {
  color: var(--text-secondary);
  padding-left: 0.8rem;
  border-left: 2px solid rgba(196,163,90,0.3);
}
.polish-arrow { color: var(--accent-primary); font-size: 1rem; margin: 0.3rem 0; padding-left: 2rem; }

/* 灵感标签 */
.inspo-grid { display: flex; flex-wrap: wrap; gap: 8px; position: relative; z-index: 1; }
.inspo-tag {
  font-size: 0.78rem; color: var(--text-secondary);
  background: rgba(196,163,90,0.06);
  border: 1px solid rgba(196,163,90,0.15);
  border-radius: 20px; padding: 6px 14px;
  letter-spacing: 0.04em; transition: all 0.3s ease;
}
.inspo-tag:hover {
  background: rgba(196,163,90,0.15);
  border-color: rgba(196,163,90,0.4);
  transform: translateY(-2px);
}

/* 大纲树 */
.outline-tree { margin-top: 0.5rem; position: relative; z-index: 1; }
.ot-item { font-size: 0.85rem; color: var(--text-secondary); padding: 4px 0; letter-spacing: 0.04em; }
.ot-l1 { color: var(--text-primary); font-weight: 600; padding-left: 0; }
.ot-l2 { padding-left: 1.2rem; }
.ot-l3 { padding-left: 2.4rem; color: var(--text-muted); font-size: 0.8rem; }

/* 角色卡片 */
.char-card { margin-top: 0.5rem; position: relative; z-index: 1; }
.char-header { display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.8rem; }
.char-avatar {
  width: 40px; height: 40px; border-radius: 50%;
  background: rgba(196,163,90,0.2);
  display: flex; align-items: center; justify-content: center;
  font-size: 1rem; color: var(--accent-primary); font-weight: 700;
}
.char-meta { display: flex; flex-direction: column; gap: 2px; }
.char-meta strong { font-size: 0.9rem; color: var(--text-primary); }
.char-meta span { font-size: 0.75rem; color: var(--text-muted); }
.char-traits { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 0.6rem; }
.char-traits span {
  font-size: 0.72rem; color: var(--accent-primary);
  background: rgba(196,163,90,0.08);
  border-radius: 10px; padding: 2px 10px;
}
.char-bio {
  font-size: 0.8rem; color: var(--text-muted);
  line-height: 1.7; letter-spacing: 0.03em; margin: 0;
}

/* 提示词列表 */
.prompt-list { margin-top: 0.5rem; display: flex; flex-direction: column; gap: 8px; position: relative; z-index: 1; }
.prompt-item {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.8rem; color: var(--text-secondary); letter-spacing: 0.03em;
}
.prompt-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--accent-primary); opacity: 0.5; flex-shrink: 0;
}

/* 阅读系统演示 */
.reading-demo { margin-top: 0.5rem; position: relative; z-index: 1; }
.rd-progress { display: flex; align-items: center; gap: 10px; margin-bottom: 1rem; }
.rd-label { font-size: 0.8rem; color: var(--text-muted); white-space: nowrap; }
.rd-bar { flex: 1; height: 6px; background: rgba(255,255,255,0.06); border-radius: 3px; overflow: hidden; }
.rd-fill { height: 100%; background: linear-gradient(90deg, var(--accent-primary), #a78bfa); border-radius: 3px; transition: width 1s ease; }
.rd-pct { font-size: 0.8rem; color: var(--accent-primary); font-weight: 600; }
.rd-tools { display: flex; flex-wrap: wrap; gap: 8px; }
.rd-tag {
  font-size: 0.75rem; color: var(--text-secondary);
  background: rgba(196,163,90,0.06); border: 1px solid rgba(196,163,90,0.12);
  border-radius: 12px; padding: 4px 12px;
}

/* ====== 流光效果 ====== */
.shimmer-card { overflow: hidden; }
.card-shimmer {
  position: absolute; top: 0; left: -100%;
  width: 60%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.02), transparent);
  transform: skewX(-20deg);
  transition: left 0.7s ease;
  pointer-events: none; z-index: 0;
}
.shimmer-card:hover .card-shimmer,
.comm-card:hover .card-shimmer,
.level-card:hover .card-shimmer { left: 150%; }

/* ====== Community 卡片 ====== */
.comm-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-top: 2.5rem; }
.comm-card {
  display: flex; flex-direction: column; align-items: center;
  gap: 0.3rem; padding: 2rem 1.2rem;
  border-radius: 14px;
  background: rgba(255,255,255,0.015);
  border: 1px solid rgba(255,255,255,0.04);
  transition: all 0.35s ease;
  transform-style: preserve-3d;
  position: relative; overflow: hidden;
}
.comm-card:hover {
  border-color: rgba(196,163,90,0.2);
  background: rgba(196,163,90,0.03);
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0,0,0,0.3);
}
.comm-icon-box {
  width: 52px; height: 52px; border-radius: 50%;
  background: rgba(196,163,90,0.06);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 0.5rem; transition: background 0.3s ease;
  position: relative; z-index: 1;
}
.comm-card:hover .comm-icon-box { background: rgba(196,163,90,0.15); }
.comm-icon { font-size: 1.4rem; color: var(--accent-primary); }
.comm-en {
  font-family: var(--font-display);
  font-size: 0.9rem; font-weight: 600;
  color: var(--text-primary); letter-spacing: 0.04em;
  position: relative; z-index: 1;
}
.comm-cn { font-size: 0.78rem; color: var(--text-muted); position: relative; z-index: 1; }
.comm-desc {
  font-size: 0.75rem; color: var(--text-muted);
  line-height: 1.6; letter-spacing: 0.03em;
  text-align: center; margin: 0.25rem 0 0;
  position: relative; z-index: 1;
}

/* ====== 等级系统 ====== */
.level-row { display: flex; justify-content: center; gap: 1rem; margin-top: 2.5rem; flex-wrap: wrap; }
.level-card {
  display: flex; flex-direction: column; align-items: center;
  gap: 0.2rem; padding: 1.5rem 1.8rem;
  border-radius: 14px;
  background: rgba(255,255,255,0.015);
  border: 1px solid rgba(255,255,255,0.04);
  transition: all 0.35s ease; min-width: 120px;
  transform-style: preserve-3d;
  position: relative; overflow: hidden;
}
.level-card:hover {
  border-color: rgba(196,163,90,0.2);
  background: rgba(196,163,90,0.03);
  transform: translateY(-3px);
}
.level-num {
  font-family: var(--font-display);
  font-size: 0.75rem; font-weight: 700;
  letter-spacing: 0.15em; color: var(--accent-primary); opacity: 0.7;
  position: relative; z-index: 1;
}
.level-name { font-size: 0.95rem; font-weight: 600; color: var(--text-primary); letter-spacing: 0.05em; position: relative; z-index: 1; }
.level-exp { font-size: 0.75rem; color: var(--text-muted); position: relative; z-index: 1; }

/* ====== 每日精选 ====== */
.featured-wrapper {
  margin-top: 2.5rem;
  max-width: 900px;
  margin-inline: auto;
}

/* ====== CTA ====== */
.cta-heading { font-size: clamp(3rem, 6vw, 5rem); margin-bottom: 1rem; }
.cta-buttons { display: flex; gap: 1rem; justify-content: center; margin-top: 2.5rem; flex-wrap: wrap; }
.cta-btn {
  display: inline-flex; align-items: center; gap: 10px;
  padding: 15px 38px; border-radius: 30px;
  font-size: 0.95rem; font-weight: 600;
  letter-spacing: 0.04em; text-decoration: none;
  transition: all 0.35s cubic-bezier(0.16,1,0.3,1);
}
.cta-primary {
  background: linear-gradient(135deg, #c4a35a, #9b7d3c);
  color: #0f0f1a;
  box-shadow: 0 4px 24px rgba(196,163,90,0.25);
}
.cta-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 36px rgba(196,163,90,0.45); }
.pulse-glow { animation: pulseGlow 2.5s ease-in-out infinite; }
@keyframes pulseGlow {
  0%, 100% { box-shadow: 0 4px 24px rgba(196,163,90,0.25); }
  50% { box-shadow: 0 4px 48px rgba(196,163,90,0.5), 0 0 80px rgba(196,163,90,0.1); }
}
.cta-arrow { transition: transform 0.3s ease; font-size: 1.1rem; }
.cta-primary:hover .cta-arrow { transform: translateX(4px); }
.cta-ghost {
  color: var(--text-secondary);
  border: 1px solid rgba(196,163,90,0.25);
  background: transparent;
}
.cta-ghost:hover { color: var(--accent-primary); border-color: var(--accent-primary); transform: translateY(-2px); }


/* ====== 响应式 ====== */
@media (max-width: 900px) {
  .split-layout, .split-layout.reverse {
    flex-direction: column; gap: 2rem; text-align: center;
  }
  .split-visual { flex: 0 0 auto; width: 100%; max-width: 400px; }
  .feature-points li { text-align: left; }
  .comm-grid { grid-template-columns: repeat(2, 1fr); }
  .level-row { gap: 0.6rem; }
}
@media (max-width: 640px) {
  .comm-grid { grid-template-columns: repeat(2, 1fr); max-width: 400px; margin-inline: auto; }
  .stat-row { gap: 1rem; }
  .level-card { min-width: 80px; padding: 1rem 0.8rem; }
  .scroll-indicator { right: 8px; gap: 8px; }
  .indicator-dot { width: 5px; height: 5px; }
}
</style>
