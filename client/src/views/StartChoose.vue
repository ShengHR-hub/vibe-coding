<template>
  <div class="sc-page">
    <div class="sc-head">
      <p class="sc-kicker">CHOOSE YOUR PATH</p>
      <h1 class="sc-title">选择你的写作方式</h1>
      <p class="sc-desc">同一个墨池，三条路。不确定就选「新手系统」，随时可回。</p>
    </div>
    <div class="sc-cards">
      <router-link to="/write/new" class="sc-card sc-newbie">
        <span class="sc-en">Newbie</span>
        <span class="sc-name">新手系统</span>
        <span class="sc-sub">左边写作 · 右边引导：灵感 → 主线 → 大纲 → 主角，AI 偶尔搭把手</span>
        <span class="sc-line"></span>
        <span class="sc-tag">第一次用？选这个</span>
      </router-link>
      <router-link to="/write" class="sc-card sc-pro">
        <span class="sc-en">Pro</span>
        <span class="sc-name">老手系统</span>
        <span class="sc-sub">完整写作台：蓝图 · 大纲 · 设定 · 任务卡 · 续写 · 审校 · 交付</span>
        <span class="sc-line"></span>
        <span class="sc-tag">功能最全</span>
      </router-link>
      <router-link to="/write/plain" class="sc-card sc-plain">
        <span class="sc-en">Plain</span>
        <span class="sc-name">纯净写作</span>
        <span class="sc-sub">只有编辑区：选作品 → 写 → 保存 / 导出，零干扰</span>
        <span class="sc-line"></span>
        <span class="sc-tag">只想安静写</span>
      </router-link>
    </div>
  </div>
</template>

<style scoped>
.sc-page { min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 2rem 1rem; }
.sc-head { text-align: center; margin-bottom: 2.2rem; }
.sc-kicker { font-size: 0.72rem; letter-spacing: 0.3em; color: var(--accent-primary); margin-bottom: 0.6rem; }
.sc-title { font-family: var(--font-serif); font-size: 1.8rem; margin: 0 0 0.6rem; color: var(--text-primary); }
.sc-desc { color: var(--text-secondary); font-size: 0.88rem; }
.sc-cards { display: flex; gap: 1.5rem; justify-content: center; flex-wrap: wrap; max-width: 940px; width: 100%; }
.sc-card {
  position: relative; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px;
  padding: 2rem 1.8rem; border-radius: 2px; text-decoration: none; overflow: hidden;
  flex: 1 1 220px; max-width: 300px;
  background: transparent; border: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
}
.sc-card:hover { transform: translateY(-3px); border-color: rgba(255, 255, 255, 0.15); }
.sc-newbie:hover { background: rgba(196, 163, 90, 0.04); box-shadow: 0 20px 60px rgba(196, 163, 90, 0.08); }
.sc-pro:hover { background: rgba(167, 139, 250, 0.04); box-shadow: 0 20px 60px rgba(167, 139, 250, 0.08); }
.sc-plain:hover { background: rgba(96, 165, 250, 0.04); box-shadow: 0 20px 60px rgba(96, 165, 250, 0.08); }
.sc-en { font-family: var(--font-display); font-size: 0.7rem; font-weight: 600; letter-spacing: 0.3em; text-transform: uppercase; color: var(--text-muted); opacity: 0.5; margin-bottom: 0.6rem; }
.sc-name { font-family: var(--font-serif); font-size: 1.35rem; font-weight: 700; color: var(--text-primary); letter-spacing: 0.12em; margin-bottom: 0.5rem; text-align: center; }
.sc-sub { font-size: 0.78rem; color: var(--text-muted); letter-spacing: 0.05em; line-height: 1.8; text-align: center; }
.sc-line { position: absolute; bottom: 0; left: 50%; transform: translateX(-50%); width: 0; height: 1px; transition: width 0.5s cubic-bezier(0.16, 1, 0.3, 1); }
.sc-card:hover .sc-line { width: 60%; }
.sc-newbie .sc-line { background: var(--accent-primary); }
.sc-pro .sc-line { background: var(--accent-purple, #a78bfa); }
.sc-plain .sc-line { background: #60a5fa; }
.sc-tag { font-size: 0.68rem; letter-spacing: 0.08em; color: var(--accent-primary); opacity: 0.9; }
.sc-pro .sc-tag { color: var(--accent-purple, #a78bfa); }
.sc-plain .sc-tag { color: #60a5fa; }
</style>