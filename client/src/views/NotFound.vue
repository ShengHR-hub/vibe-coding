<template>
  <div class="not-found">
    <div class="nf-content">
      <span class="nf-code">404</span>
      <h2 class="nf-title">页面走丢了</h2>
      <p class="nf-desc">墨池虽大，但这里似乎还没有开辟新的水域。</p>
      <div class="nf-actions">
        <router-link to="/" class="nf-btn nf-primary">返回首页</router-link>
        <router-link to="/explore" class="nf-btn nf-ghost">探索社区</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.not-found {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 80px);
  text-align: center;
}
.nf-code {
  font-family: var(--font-display);
  font-size: 8rem;
  font-weight: 700;
  color: var(--accent-primary);
  opacity: 0.15;
  line-height: 1;
  display: block;
  margin-bottom: 1rem;
}
.nf-title {
  font-family: var(--font-serif);
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}
.nf-desc {
  font-size: 0.95rem;
  color: var(--text-muted);
  margin-bottom: 2rem;
}
.nf-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}
.nf-btn {
  padding: 10px 28px;
  border-radius: 24px;
  font-size: 0.9rem;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.3s ease;
}
.nf-primary {
  background: linear-gradient(135deg, #c4a35a, #9b7d3c);
  color: #0f0f1a;
}
.nf-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(196, 163, 90, 0.3);
}
.nf-ghost {
  color: var(--text-secondary);
  border: 1px solid rgba(196, 163, 90, 0.25);
}
.nf-ghost:hover {
  color: var(--accent-primary);
  border-color: var(--accent-primary);
}
</style>
