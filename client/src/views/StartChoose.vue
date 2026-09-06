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
.sc-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.2rem; max-width: 900px; width: 100%; }
.sc-card {
  position: relative; display: flex; flex-direction: column; gap: 8px;
  padding: 2rem 1.6rem; border-radius: var(--radius-lg, 14px); text-decoration: none;
  background: var(--bg-card, var(--bg-panel)); border: 1px solid var(--border-glass, rgba(196,163,90,0.2));
  transition: all 0.22s ease; overflow: hidden;
}
.sc-card:hover { transform: translateY(-4px); border-color: rgba(196, 163, 90, 0.5); }
.sc-en { font-size: 0.7rem; letter-spacing: 0.25em; color: var(--text-muted); }
.sc-name { font-family: var(--font-serif); font-size: 1.3rem; color: var(--text-primary); }
.sc-sub { font-size: 0.82rem; line-height: 1.8; color: var(--text-secondary); }
.sc-line { width: 36px; height: 2px; background: var(--accent-primary); transition: width 0.25s; }
.sc-card:hover .sc-line { width: 70%; }
.sc-tag { font-size: 0.72rem; color: var(--accent-primary); }
.sc-newbie .sc-line { background: var(--accent-primary); }
.sc-pro .sc-line { background: var(--accent-purple, #a78bfa); }
.sc-plain .sc-line { background: #60a5fa; }
</style>