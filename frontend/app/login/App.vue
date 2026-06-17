<template>
  <div class="promax-shell">
    <LoginBackground />

    <header class="top-nav">
      <div class="brand">
        <img class="brand-logo" src="/images/logo.png" :alt="`${APP_NAME} Logo`" style="object-fit: contain;" />
        <span class="brand-text">{{ APP_NAME }}</span>
      </div>
      <div class="nav-links">
        <a href="#">文档中心</a>
        <a href="#">联系支持</a>
      </div>
    </header>

    <main class="main-content">
      <FeatureShowcase />
      <LoginCard />
    </main>
  </div>
</template>

<script setup>
import LoginBackground from "./components/LoginBackground.vue"
import FeatureShowcase from "./components/FeatureShowcase.vue"
import LoginCard from "./components/LoginCard.vue"
import { APP_NAME } from "#/shared/app-meta.js"
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

/* Shell & Variables */
.promax-shell {
  --bg-color: #000000;
  --text-primary: #FFFFFF;
  --text-secondary: #A1A1AA;

  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: var(--text-primary);
  background-color: var(--bg-color);
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  -webkit-font-smoothing: antialiased;
}

/* Top Nav */
.top-nav {
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 48px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}
.brand-logo {
  width: 38px;
  height: 38px;
}
.brand-text {
  font-weight: 700;
  font-size: 20px;
  letter-spacing: -0.01em;
}
.nav-links {
  display: flex;
  gap: 24px;
}
.nav-links a {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: color 0.2s;
}
.nav-links a:hover {
  color: var(--text-primary);
}

/* Main Layout */
.main-content {
  flex: 1;
  display: flex;
  position: relative;
  z-index: 10;
}

@media (max-width: 768px) {
  .top-nav { padding: 20px 24px; }
}
</style>
