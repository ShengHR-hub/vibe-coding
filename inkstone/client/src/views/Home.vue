<template>
  <div class="page-container home-hero">
    <div class="hero-content">
      <h1>让每个字都有灵魂</h1>
      <p>AI驱动的全品类创作平台 — 写作、分享、成长</p>
      <div class="hero-actions">
        <router-link to="/write" class="btn btn-primary btn-lg">开始创作</router-link>
        <router-link to="/explore" class="btn btn-outline btn-lg">探索社区</router-link>
      </div>
    </div>
    <div class="hero-stats">
      <div class="stat"><strong>10</strong><span>AI写作功能</span></div>
      <div class="stat"><strong>46</strong><span>平台子功能</span></div>
      <div class="stat"><strong>∞</strong><span>创作可能性</span></div>
    </div>
  </div>
</template>

<style scoped>
.home-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 64px - 6rem);
  text-align: center;
  gap: var(--space-2xl);
}
.hero-content h1 {
  font-size: 3rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: var(--space-md);
}
.hero-content p {
  font-size: 1.15rem;
  color: var(--text-secondary);
}
.hero-actions {
  display: flex;
  gap: var(--space-md);
  justify-content: center;
  margin-top: var(--space-xl);
}
.btn-lg { padding: 12px 32px; font-size: 1.05rem; border-radius: var(--radius-md); }
.hero-stats {
  display: flex;
  gap: var(--space-2xl);
  margin-top: var(--space-xl);
}
.stat { display: flex; flex-direction: column; align-items: center; }
.stat strong { font-size: 2rem; color: var(--accent-primary); }
.stat span { font-size: 0.85rem; color: var(--text-muted); }
</style>
