<template>
  <div class="home-fullpage" ref="container">
    <FluidCursor />

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
      <span class="indicator-dot" v-for="i in totalSections" :key="i" :class="{ active: currentSection === i - 1 }"></span>
    </div>

    <!-- ====== 1. Hero ====== -->
    <section class="fp-section section-hero">
      <div class="section-inner">
        <div class="hero-glow-ring"></div>
        <p class="hero-overline">Inkstone</p>
        <h1 class="hero-title" ref="heroTitle">让每个字<br>都有灵魂</h1>
        <p class="hero-subtitle">Where every word finds its soul</p>
        <div class="hero-divider"></div>
        <p class="hero-desc">墨池是一个 AI 驱动的全品类创作平台，融合前沿大语言模型与<br>优雅的写作体验，覆盖小说、诗歌、散文、剧本、自媒体等创作场景。</p>
        <div class="hero-cta">
          <router-link to="/write" class="cta-btn cta-primary">
            <span>Start Writing</span>
            <span class="cta-arrow">&rarr;</span>
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
        <h2 class="sec-heading">一站式<br>智能创作空间</h2>
        <p class="sec-subtitle">
          墨池将 AI 深度融入创作的每一个环节——从灵感捕捉到最终发布，<br>
          你只需专注创意本身，其余交给 AI。
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

    <!-- ====== 3. AI 续写 ====== -->
    <section class="fp-section section-feature-detail">
      <div class="section-inner split-layout">
        <div class="split-text">
          <span class="feature-badge">01</span>
          <h2 class="sec-heading">Smart<br>Continuation</h2>
          <h3 class="feature-cn-title">智能续写</h3>
          <p class="feature-long-desc">
            不只是简单的文本补全。墨池的智能续写引擎会深度理解你的上下文语境、角色设定和文风特征，生成与原文高度一致的高质量续写内容。支持小说、散文、诗歌、剧本等多种文体，通过 SSE 流式响应让你实时看到 AI 创作的过程。
          </p>
          <ul class="feature-points">
            <li>上下文感知，保持文风、人称、时代背景一致</li>
            <li>SSE 流式输出，实时查看 AI 生成过程</li>
            <li>支持随时中断、调整方向，人机协作而非单向输出</li>
            <li>自动保存对话历史，随时回溯修改</li>
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

    <!-- ====== 4. 灵感激发 ====== -->
    <section class="fp-section section-feature-detail">
      <div class="section-inner split-layout reverse">
        <div class="split-visual">
          <div class="visual-card shimmer-card">
            <span class="visual-icon">☆</span>
            <div class="visual-demo">
              <div class="inspo-grid">
                <span class="inspo-tag">赛博朋克 + 唐代宫廷</span>
                <span class="inspo-tag">AI 觉醒与自我意识</span>
                <span class="inspo-tag">双主角镜像叙事</span>
                <span class="inspo-tag">末世废墟中的希望</span>
              </div>
            </div>
            <div class="card-shimmer"></div>
          </div>
        </div>
        <div class="split-text">
          <span class="feature-badge">02</span>
          <h2 class="sec-heading">Inspiration<br>Engine</h2>
          <h3 class="feature-cn-title">灵感激发</h3>
          <p class="feature-long-desc">
            每个创作者都会遇到瓶颈。灵感激发引擎是你的随身创意伙伴——输入一个模糊的想法，它能生成完整的角色设定、世界观框架、情节转折方案。从简单构思到包含人物关系图谱和章节大纲的完整策划，只需一键。
          </p>
          <ul class="feature-points">
            <li>角色设定生成：外貌、性格、背景故事、动机弧线</li>
            <li>世界观构建：时代背景、社会结构、魔法/科技体系</li>
            <li>情节转折：冲突设计、高潮编排、多结局方案</li>
            <li>创作提示库：海量精选 prompt，覆盖各类文体场景</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- ====== 5. 大纲规划 ====== -->
    <section class="fp-section section-feature-detail">
      <div class="section-inner split-layout">
        <div class="split-text">
          <span class="feature-badge">03</span>
          <h2 class="sec-heading">Outline<br>Architect</h2>
          <h3 class="feature-cn-title">大纲规划</h3>
          <p class="feature-long-desc">
            长篇创作最大的挑战是结构。大纲规划器能智能分析你的创作主题，自动生成多层级章节大纲——从卷、篇、章到节，每一层都有清晰的内容指引。你可以拖拽调整结构、增删节点，AI 实时更新建议。
          </p>
          <ul class="feature-points">
            <li>多层级大纲自动生成，从宏观结构到微观段落</li>
            <li>拖拽式结构调整，AI 实时同步更新内容建议</li>
            <li>支持导入/导出，与主流写作工具兼容</li>
            <li>进度追踪：每个章节完成度一目了然</li>
          </ul>
        </div>
        <div class="split-visual">
          <div class="visual-card shimmer-card">
            <span class="visual-icon">≡</span>
            <div class="outline-tree">
              <div class="ot-item ot-l1">卷一 · 启程</div>
              <div class="ot-item ot-l2">第1章 · 离别</div>
              <div class="ot-item ot-l3">场景：火车站送别</div>
              <div class="ot-item ot-l2">第2章 · 旅途</div>
              <div class="ot-item ot-l1">卷二 · 抵达</div>
            </div>
            <div class="card-shimmer"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- ====== 6. 角色塑造 ====== -->
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
          <h2 class="sec-heading">Character<br>Builder</h2>
          <h3 class="feature-cn-title">角色塑造</h3>
          <p class="feature-long-desc">
            扁平的角色是故事的致命伤。角色塑造器从外貌、性格、背景、动机、成长弧线五个维度帮你构建有血有肉的立体人物。AI 基于人格心理学模型分析角色行为逻辑，确保人物的每一步选择都有迹可循。
          </p>
          <ul class="feature-points">
            <li>五维角色建模：外貌 / 性格 / 背景 / 动机 / 弧线</li>
            <li>人格心理学驱动，行为逻辑自洽</li>
            <li>角色关系图谱：自动生成人物之间的关联与冲突</li>
            <li>角色对话模拟：用你的角色进行对话测试一致性</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- ====== 7. 润色优化 ====== -->
    <section class="fp-section section-feature-detail">
      <div class="section-inner split-layout">
        <div class="split-text">
          <span class="feature-badge">05</span>
          <h2 class="sec-heading">Polish &amp;<br>Refine</h2>
          <h3 class="feature-cn-title">润色优化</h3>
          <p class="feature-long-desc">
            初稿是矿石，润色是冶炼。墨池的润色引擎不止于语法纠错——它会分析你的文笔风格，在保留你独特声音的前提下提升文字质感。从用词精准度、句式变化到篇章节奏，AI 提供多维度优化建议。
          </p>
          <ul class="feature-points">
            <li>语法修正 + 用词优化 + 句式多样化，三合一</li>
            <li>尊重作者风格，不做模板化替换</li>
            <li>可调节润色力度：轻微修饰 / 深度改写</li>
            <li>逐句对比模式：修改前后并排展示，一目了然</li>
          </ul>
        </div>
        <div class="split-visual">
          <div class="visual-card shimmer-card">
            <span class="visual-icon">♦</span>
            <div class="visual-demo">
              <p class="demo-line prompt">他很快地走到了那个很大的房子前面。</p>
              <div class="polish-arrow">↓</div>
              <p class="demo-line ai">他快步走到那座宏伟的老宅前，月光正爬上斑驳的墙壁。</p>
            </div>
            <div class="card-shimmer"></div>
          </div>
        </div>
      </div>
    </section>

    <!-- ====== 8. 提示词库 ====== -->
    <section class="fp-section section-feature-detail">
      <div class="section-inner split-layout reverse">
        <div class="split-visual">
          <div class="visual-card shimmer-card">
            <span class="visual-icon">✎</span>
            <div class="prompt-list">
              <div class="prompt-item" v-for="p in samplePrompts" :key="p">
                <span class="prompt-dot"></span>
                <span>{{ p }}</span>
              </div>
            </div>
            <div class="card-shimmer"></div>
          </div>
        </div>
        <div class="split-text">
          <span class="feature-badge">06</span>
          <h2 class="sec-heading">Prompt<br>Library</h2>
          <h3 class="feature-cn-title">提示词库</h3>
          <p class="feature-long-desc">
            好的 prompt 是 AI 创作的关键。墨池内置了海量精心调校的创作提示词，覆盖小说开篇、情节转折、对话生成、场景描写、情感渲染等数十种创作场景。每个提示词都经过真实创作验证，你也可以收藏、修改和分享。
          </p>
          <ul class="feature-points">
            <li>10+ 文体、30+ 场景分类，快速找到需要的提示词</li>
            <li>每条提示词含使用示例和效果说明</li>
            <li>自定义提示词：创建、编辑、收藏、分享</li>
            <li>社区共享：浏览其他创作者的提示词方案</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- ====== 9. 创作社区 ====== -->
    <section class="fp-section section-community">
      <div class="section-inner">
        <p class="sec-tag">Community <span class="tag-cn">社区</span></p>
        <h2 class="sec-heading">Share &amp;<br>Discover</h2>
        <p class="sec-subtitle">
          创作不是孤独的事。在墨池社区，你可以发布作品、<br>发现同好、交流技巧、互相激励。
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

    <!-- ====== 10. 成就 & 成长体系 ====== -->
    <section class="fp-section section-achievements">
      <div class="section-inner">
        <p class="sec-tag">Growth <span class="tag-cn">成长</span></p>
        <h2 class="sec-heading">Level Up<br>Your Craft</h2>
        <p class="sec-subtitle">
          每一次创作都在积累经验。从"初窥门径"到"文坛巨匠"，<br>你的每个字都算数。
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

    <!-- ====== 11. CTA ====== -->
    <section class="fp-section section-cta">
      <div class="section-inner">
        <h2 class="sec-heading cta-heading">Ready to<br>Create?</h2>
        <p class="sec-subtitle">加入墨池，让 AI 激发你的下一个伟大故事</p>
        <div class="cta-buttons">
          <router-link to="/write" class="cta-btn cta-primary pulse-glow">
            <span>Start Writing</span>
            <span class="cta-arrow">&rarr;</span>
          </router-link>
          <router-link to="/register" class="cta-btn cta-ghost">Create Account</router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import FluidCursor from '../components/FluidCursor.vue'

gsap.registerPlugin(ScrollTrigger)

const totalSections = 11
const currentSection = ref(0)
const container = ref(null)
const indicator = ref(null)
const heroTitle = ref(null)

const stats = [
  { num: 7, label: 'AI 核心能力', desc: '覆盖创作全流程' },
  { num: 10, label: '功能模块', desc: '写作 / 社区 / 成长' },
  { num: 46, label: '平台子功能', desc: '每个细节都打磨到位' },
  { num: 5, label: '创作品类', desc: '小说 / 诗歌 / 散文 / 剧本 / 自媒体' },
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
  { icon: '✎', en: 'Comment', cn: '评论交流', desc: '深度评论交流创作心得，互相学习共同进步' },
  { icon: '♦', en: 'Rank', cn: '成就等级', desc: '从初窥门径到文坛巨匠，十级成长见证创作之路' },
]

const levels = [
  { level: 1, name: '初窥门径', exp: '0' },
  { level: 3, name: '小有所成', exp: '500' },
  { level: 5, name: '妙笔生花', exp: '5,000' },
  { level: 7, name: '才华横溢', exp: '30,000' },
  { level: 10, name: '文坛巨匠', exp: '500,000' },
]

let stTriggers = []
let tiltCleanups = []

function splitHeroChars() {
  const el = heroTitle.value
  if (!el) return
  // 保留 <br> 标签，只拆分文本节点
  const parts = []
  el.childNodes.forEach(node => {
    if (node.nodeType === 3) {
      // 文本节点：逐字拆分
      node.textContent.split('').forEach(char => {
        parts.push({ type: 'char', text: char })
      })
    } else {
      // <br> 元素
      parts.push({ type: 'br' })
    }
  })
  el.innerHTML = ''
  parts.forEach(p => {
    if (p.type === 'br') {
      el.appendChild(document.createElement('br'))
    } else {
      const span = document.createElement('span')
      span.className = 'hero-char'
      span.textContent = p.text
      span.style.display = 'inline-block'
      el.appendChild(span)
    }
  })
}

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

onMounted(() => {
  nextTick(() => {
    // 拆分 Hero 文字为逐字
    splitHeroChars()

    const sectionsEl = document.querySelectorAll('.fp-section')

    sectionsEl.forEach((section, i) => {
      const tl = gsap.timeline({ paused: true })
      const isHero = i === 0
      const isSplit = section.classList.contains('section-feature-detail')
      const isCommunity = section.classList.contains('section-community')
      const isAchievements = section.classList.contains('section-achievements')

      if (isHero) {
        // === Hero: 逐字飞入 + 分层浮现 ===
        tl.fromTo('.hero-overline', { y: 16, opacity: 0 }, { y: 0, opacity: 1, duration: 0.6, ease: 'power3.out' })
        tl.fromTo('.hero-glow-ring', { scale: 0.3, opacity: 0 }, { scale: 1, opacity: 0.5, duration: 2, ease: 'elastic.out(1, 0.6)' }, '-=0.2')
        // 逐字动画
        tl.fromTo('.hero-char', {
          y: 60, opacity: 0, rotateX: -90,
        }, {
          y: 0, opacity: 1, rotateX: 0,
          duration: 0.7, stagger: 0.04, ease: 'back.out(1.7)',
        }, '-=0.5')
        tl.fromTo('.hero-subtitle', { opacity: 0 }, { opacity: 1, duration: 0.7 }, '-=0.2')
        tl.fromTo('.hero-divider', { scaleX: 0, opacity: 0 }, { scaleX: 1, opacity: 1, duration: 0.8, ease: 'power3.inOut' }, '-=0.3')
        tl.fromTo('.hero-desc, .hero-cta', { y: 16, opacity: 0 }, { y: 0, opacity: 1, duration: 0.5, stagger: 0.1, ease: 'power3.out' }, '-=0.2')
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
    gsap.to('.f-orb-1', { y: -30, x: 20, duration: 8, repeat: -1, yoyo: true, ease: 'sine.inOut' })
    gsap.to('.f-orb-2', { y: 25, x: -20, duration: 10, repeat: -1, yoyo: true, ease: 'sine.inOut' })
    gsap.to('.f-orb-3', { y: -20, x: -15, duration: 7, repeat: -1, yoyo: true, ease: 'sine.inOut' })
    gsap.to('.f-diamond-1', { y: -40, rotate: 180, duration: 12, repeat: -1, yoyo: true, ease: 'sine.inOut' })
    gsap.to('.f-diamond-2', { y: 30, rotate: -180, duration: 9, repeat: -1, yoyo: true, ease: 'sine.inOut' })
    gsap.to('.f-ring-1', { scale: 1.2, opacity: 0.15, duration: 6, repeat: -1, yoyo: true, ease: 'sine.inOut' })
  })
})

onUnmounted(() => {
  stTriggers.forEach(st => st.kill())
  unbindTilt()
})
</script>

<style scoped>
.home-fullpage {
  position: relative; z-index: 1;
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
.hero-title {
  font-family: var(--font-serif);
  font-size: clamp(3rem, 6vw, 5rem); font-weight: 700;
  line-height: 1.2; letter-spacing: 0.03em;
  background: linear-gradient(180deg, #f0ead8 0%, #c4a35a 30%, #9b7d3c 60%, #6b5428 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  filter: drop-shadow(0 0 24px rgba(196,163,90,0.15));
  margin-bottom: 1.25rem; position: relative;
}
.hero-char {
  display: inline-block;
  will-change: transform, opacity;
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
.comm-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 2.5rem; }
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
  .comm-grid { grid-template-columns: 1fr; max-width: 300px; margin-inline: auto; }
  .stat-row { gap: 1rem; }
  .level-card { min-width: 80px; padding: 1rem 0.8rem; }
  .scroll-indicator { right: 8px; gap: 8px; }
  .indicator-dot { width: 5px; height: 5px; }
}
</style>
