<template>
  <div class="admin-page">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner">
      <div class="welcome-banner__content">
        <h1 class="welcome-title">欢迎使用 智慧AI 探索平台</h1>
        <p class="welcome-subtitle">您好，管理员！这是专为 AI 辅助开发设计的后台管理工作台，提供快速运维与数据闭环服务。</p>
      </div>
      <div class="welcome-banner__bg-glow"></div>
    </div>

    <!-- 数据指标统计 -->
    <div class="stats-row">
      <div class="admin-card stat-card" @click="goPage('admins')">
        <div class="stat-icon-wrapper bg-blue-soft text-blue">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
        </div>
        <div class="stat-main">
          <span class="stat-label">系统账号</span>
          <span class="stat-value">{{ loading ? '...' : adminsCount }} <em class="stat-unit">个</em></span>
        </div>
      </div>

      <div class="admin-card stat-card" @click="goPage('roles')">
        <div class="stat-icon-wrapper bg-purple-soft text-purple">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
        </div>
        <div class="stat-main">
          <span class="stat-label">授权角色组</span>
          <span class="stat-value">{{ loading ? '...' : rolesCount }} <em class="stat-unit">个</em></span>
        </div>
      </div>

      <div class="admin-card stat-card" @click="goPage('settings')">
        <div class="stat-icon-wrapper bg-cyan-soft text-cyan">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="7" height="7"/>
            <rect x="14" y="3" width="7" height="7"/>
            <rect x="14" y="14" width="7" height="7"/>
            <rect x="3" y="14" width="7" height="7"/>
          </svg>
        </div>
        <div class="stat-main">
          <span class="stat-label">注册菜单节点</span>
          <span class="stat-value">{{ loading ? '...' : menusCount }} <em class="stat-unit">个</em></span>
        </div>
      </div>
    </div>

    <!-- 底部双面板布局 -->
    <div class="dashboard-grid">
      <!-- 快捷入口 -->
      <div class="admin-card panel-card">
        <div class="admin-card__eyebrow">QUICK NAV</div>
        <h2 class="admin-card__title">快捷运维入口</h2>
        
        <div class="quick-nav-list">
          <div class="quick-nav-item" @click="goPage('admins')">
            <div class="quick-nav-icon bg-blue-soft text-blue">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/>
              </svg>
            </div>
            <div class="quick-nav-text">
              <h4>账号管理</h4>
              <p>管理员账户的开通、修改与状态禁用</p>
            </div>
            <span class="arrow-icon">→</span>
          </div>

          <div class="quick-nav-item" @click="goPage('roles')">
            <div class="quick-nav-icon bg-purple-soft text-purple">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="3"/>
                <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
              </svg>
            </div>
            <div class="quick-nav-text">
              <h4>角色与授权</h4>
              <p>自定义角色组并进行精确的菜单节点勾选</p>
            </div>
            <span class="arrow-icon">→</span>
          </div>

          <div class="quick-nav-item" @click="goPage('settings')">
            <div class="quick-nav-icon bg-cyan-soft text-cyan">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
              </svg>
            </div>
            <div class="quick-nav-text">
              <h4>系统设置</h4>
              <p>同步代码级路由（page.js）到数据库菜单库</p>
            </div>
            <span class="arrow-icon">→</span>
          </div>
        </div>
      </div>

      <!-- 动态菜单闭环说明 -->
      <div class="admin-card panel-card">
        <div class="admin-card__eyebrow">系统机制</div>
        <h2 class="admin-card__title">动态菜单闭环机制</h2>
        
        <div class="pipeline-steps">
          <div class="step-item">
            <div class="step-badge">1</div>
            <div class="step-content">
              <h5>声明页面配置</h5>
              <p>开发者在视图目录下新建视图组件及对应的 <code>page.js</code>，声明资源标识码与路径。</p>
            </div>
          </div>
          
          <div class="step-item">
            <div class="step-badge">2</div>
            <div class="step-content">
              <h5>同步至数据库</h5>
              <p>在「系统设置」中一键同步，或在终端运行 <code>pnpm sync:menu</code> 将页面定义写入数据库表 <code>sys_menu</code>。</p>
            </div>
          </div>

          <div class="step-item">
            <div class="step-badge">3</div>
            <div class="step-content">
              <h5>分配角色权限</h5>
              <p>进入「角色管理」，将新注册的菜单选项分配勾选给相应的角色组。</p>
            </div>
          </div>

          <div class="step-item">
            <div class="step-badge">4</div>
            <div class="step-content">
              <h5>动态菜单渲染</h5>
              <p>下次登录或刷新后，前端将全量拉取已授权的菜单，并动态注册路由生成侧边导航栏。</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from "vue"
import { useRouter } from "vue-router"
import { fetchRoles } from "../../api/role.js"
import { fetchMenuList } from "../../api/menu.js"
import { http } from "../../api/http.js"

defineOptions({ name: "Dashboard" })

const router = useRouter()
const loading = ref(false)
const rolesCount = ref(0)
const menusCount = ref(0)
const adminsCount = ref(0)

onMounted(loadDashboardStats)

async function loadDashboardStats() {
  loading.value = true
  try {
    const [roles, menus, adminsRes] = await Promise.all([
      fetchRoles().catch(() => []),
      fetchMenuList().catch(() => []),
      http.get("/api/v1/admins", { params: { size: 1 } }).catch(() => null)
    ])
    rolesCount.value = roles.length
    menusCount.value = menus.length
    adminsCount.value = adminsRes?.data?.data?.total ?? adminsRes?.data?.total ?? 0
  } catch (error) {
    console.error("加载工作台仪表盘指标失败", error)
  } finally {
    loading.value = false
  }
}

function goPage(name) {
  router.push({ name })
}
</script>

<style scoped>
.admin-page {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

/* 欢迎横幅 */
.welcome-banner {
  position: relative;
  background: linear-gradient(135deg, var(--c-brand) 0%, #3b82f6 100%);
  border-radius: var(--r-xl);
  padding: var(--sp-6) var(--sp-7);
  color: #ffffff;
  overflow: hidden;
  box-shadow: var(--sh-2);
}

.welcome-banner__content {
  position: relative;
  z-index: 5;
  max-width: 600px;
}

.welcome-title {
  font-size: var(--fs-xl);
  font-weight: var(--fw-bold);
  margin: 0 0 var(--sp-2) 0;
  line-height: var(--lh-tight);
}

.welcome-subtitle {
  font-size: var(--fs-base);
  color: rgba(255, 255, 255, 0.88);
  margin: 0;
  line-height: var(--lh-loose);
}

.welcome-banner__bg-glow {
  position: absolute;
  top: -50%;
  right: -10%;
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.15) 0%, transparent 80%);
  border-radius: 50%;
  pointer-events: none;
}

/* 指标统计面板 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--sp-4);
}

.stat-card {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  cursor: pointer;
  transition: transform var(--motion-fast) var(--ease-out), border-color var(--motion-fast) var(--ease-out), box-shadow var(--motion-fast) var(--ease-out);
}

.stat-card:hover {
  transform: translateY(-2px);
  border-color: var(--c-brand-border);
  box-shadow: var(--sh-2);
}

.stat-icon-wrapper {
  width: 44px;
  height: 44px;
  border-radius: var(--r-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.bg-blue-soft {
  background-color: var(--c-info-bg);
}
.text-blue {
  color: var(--c-info-text);
}

.bg-purple-soft {
  background-color: var(--c-brand-soft);
}
.text-purple {
  color: var(--c-brand-text);
}

.bg-cyan-soft {
  background-color: var(--c-success-bg);
}
.text-cyan {
  color: var(--c-success-text);
}

.stat-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-label {
  font-size: var(--fs-sm);
  color: var(--c-text-muted);
}

.stat-value {
  font-size: 20px;
  font-weight: var(--fw-bold);
  color: var(--c-text-primary);
  line-height: 1;
}

.stat-unit {
  font-style: normal;
  font-size: var(--fs-xs);
  color: var(--c-text-faint);
  font-weight: var(--fw-regular);
}

/* 双面板网格 */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--sp-4);
}

.panel-card {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

/* 快捷导航 */
.quick-nav-list {
  display: flex;
  flex-direction: column;
  gap: var(--sp-3);
}

.quick-nav-item {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-3) var(--sp-4);
  background: var(--c-surface-sunken);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  cursor: pointer;
  transition: transform var(--motion-fast) var(--ease-out), border-color var(--motion-fast) var(--ease-out), background var(--motion-fast) var(--ease-out);
}

.quick-nav-item:hover {
  transform: translateX(4px);
  border-color: var(--c-brand-border);
  background: var(--c-surface);
}

.quick-nav-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--r-xs);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.quick-nav-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.quick-nav-text h4 {
  margin: 0;
  font-size: 13px;
  font-weight: var(--fw-semibold);
  color: var(--c-text-primary);
}

.quick-nav-text p {
  margin: 0;
  font-size: 12px;
  color: var(--c-text-muted);
}

.arrow-icon {
  margin-left: auto;
  color: var(--c-text-faint);
  font-weight: var(--fw-bold);
  transition: transform var(--motion-fast) var(--ease-out), color var(--motion-fast) var(--ease-out);
}

.quick-nav-item:hover .arrow-icon {
  color: var(--c-brand);
  transform: translateX(2px);
}

/* 闭环流程步骤 */
.pipeline-steps {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.step-item {
  display: flex;
  gap: var(--sp-3);
}

.step-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--c-brand-soft);
  color: var(--c-brand-text);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--fs-sm);
  font-weight: var(--fw-bold);
  flex-shrink: 0;
}

.step-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.step-content h5 {
  margin: 0;
  font-size: 13px;
  font-weight: var(--fw-semibold);
  color: var(--c-text-primary);
}

.step-content p {
  margin: 0;
  font-size: 12px;
  color: var(--c-text-muted);
  line-height: var(--lh-loose);
}

@media (min-width: 960px) {
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
