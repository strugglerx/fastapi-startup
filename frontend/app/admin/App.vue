<template>
  <n-config-provider :theme-overrides="themeOverrides" :locale="zhCN" :date-locale="dateZhCN">
    <n-message-provider>
      <n-notification-provider>
        <n-dialog-provider>
            <div v-if="!menuRegistered" class="admin-initial-loader">
              <div class="loader-inner">
                <div class="loader-text">正在初始化...</div>
                <div class="loading-progress">
                  <div class="loading-track"></div>
                </div>
              </div>
            </div>
            <div v-else class="admin-shell" :class="{ 'sidebar-collapsed': collapsed }">
            <aside class="sidebar">
              <div class="sidebar-brand">
                <div class="brand-icon">
                  <img src="/images/logo.png" alt="智慧AI探索平台" style="width: 36px; height: 36px; object-fit: contain;" />
                </div>
                <span v-if="!collapsed" class="brand-name">智慧AI <em>探索平台</em></span>
                <button v-if="!collapsed" class="collapse-toggle" @click="onCollapse(true)" title="收起侧边栏">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="15 18 9 12 15 6"/>
                  </svg>
                </button>
              </div>

              <button v-if="collapsed" class="expand-toggle" @click="onCollapse(false)" title="展开侧边栏">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="9 18 15 12 9 6"/>
                </svg>
              </button>

              <nav class="sidebar-nav">
                <template v-for="group in visibleNavGroups" :key="group.key">
                  <p v-if="!collapsed && group.label" class="nav-group-label">{{ group.label }}</p>
                  <div v-else-if="collapsed" class="nav-group-sep"></div>
                  <button
                    v-for="item in group.items"
                    :key="item.key"
                    class="nav-item"
                    :class="{ active: activeKey === item.key }"
                    @click="navigate(item.key)"
                    :title="collapsed ? item.label : ''"
                  >
                    <span class="nav-icon">
                      <n-icon v-if="item.iconComp" :size="16">
                        <component :is="item.iconComp" />
                      </n-icon>
                    </span>
                    <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
                  </button>
                </template>
              </nav>
            </aside>

            <div class="main-area">
              <header class="topbar">
                <div class="topbar-row topbar-row--head">
                  <div class="topbar-left">
                    <nav class="breadcrumb" aria-label="breadcrumb">
                      <span class="crumb crumb-root">控制台</span>
                      <svg class="crumb-sep" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="9 18 15 12 9 6"/>
                      </svg>
                      <span class="crumb crumb-current">{{ activePageTitle }}</span>
                    </nav>
                  </div>
                  <div class="topbar-right">
                    <AdminUserDropdown
                      :user="currentUser"
                      @profile="showProfileDrawer = true"
                      @logout="handleLogout"
                    />
                  </div>
                </div>

                <nav class="topbar-tabs" role="tablist">
                  <button
                    v-for="tab in tabsWithMeta"
                    :key="tab.key"
                    class="top-tab"
                    :class="{ active: activeKey === tab.key, affix: tab.affix }"
                    role="tab"
                    :aria-selected="activeKey === tab.key"
                    @click="navigate(tab.key)"
                    @contextmenu="onTabContextMenu($event, tab.key)"
                    @mousedown.middle.prevent="closeTab(tab.key)"
                  >
                    <span class="top-tab-icon">
                      <n-icon v-if="tab.iconComp" :size="14">
                        <component :is="tab.iconComp" />
                      </n-icon>
                    </span>
                    <span class="top-tab-label">{{ tab.label }}</span>
                    <span v-if="tab.affix" class="top-tab-affix" title="固定标签">
                      <svg width="9" height="9" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 2l2.39 4.84L20 8l-4 3.9.94 5.5L12 14.77 7.06 17.4 8 11.9 4 8l5.61-1.16L12 2z"/>
                      </svg>
                    </span>
                    <span
                      v-else
                      class="top-tab-close"
                      :title="`关闭 ${tab.label}`"
                      @click.stop="closeTab(tab.key)"
                    >
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                    </span>
                  </button>
                </nav>
              </header>

              <transition name="ctx-fade">
                <div
                  v-if="ctxMenu.show"
                  class="tab-ctx-menu"
                  :style="{ left: ctxMenu.x + 'px', top: ctxMenu.y + 'px' }"
                  @click.stop
                  @contextmenu.prevent
                >
                  <button class="ctx-item" @click="onCtxAction('refresh')">
                    <svg class="ctx-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M23 4v6h-6M1 20v-6h6"/>
                      <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
                    </svg>
                    <span class="ctx-label">刷新页面</span>
                  </button>
                  <div class="ctx-sep"></div>
                  <button class="ctx-item" :disabled="!canCloseSelf" @click="onCtxAction('close')">
                    <svg class="ctx-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                      <line x1="18" y1="6" x2="6" y2="18"/>
                      <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                    <span class="ctx-label">关闭</span>
                  </button>
                  <button class="ctx-item" :disabled="!canCloseOthers" @click="onCtxAction('closeOthers')">
                    <svg class="ctx-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <rect x="5" y="5" width="14" height="14" rx="2"/>
                      <line x1="9" y1="9" x2="15" y2="15"/>
                      <line x1="15" y1="9" x2="9" y2="15"/>
                    </svg>
                    <span class="ctx-label">关闭其他</span>
                  </button>
                  <button class="ctx-item" :disabled="!canCloseLeft" @click="onCtxAction('closeLeft')">
                    <svg class="ctx-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="15 18 9 12 15 6"/>
                    </svg>
                    <span class="ctx-label">关闭左侧</span>
                  </button>
                  <button class="ctx-item" :disabled="!canCloseRight" @click="onCtxAction('closeRight')">
                    <svg class="ctx-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="9 18 15 12 9 6"/>
                    </svg>
                    <span class="ctx-label">关闭右侧</span>
                  </button>
                  <div class="ctx-sep"></div>
                  <button class="ctx-item ctx-item--danger" :disabled="!canCloseAll" @click="onCtxAction('closeAll')">
                    <svg class="ctx-icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="3 6 5 6 21 6"/>
                      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                    </svg>
                    <span class="ctx-label">关闭全部</span>
                  </button>
                </div>
              </transition>

              <main class="content-area">
                <router-view v-if="!refreshing" />
              </main>
            </div>
          </div>

          <n-modal v-model:show="showProfileDrawer" preset="card" title="我的资料" style="width: 520px; max-width: 95vw;">
            <AdminProfileView :is-drawer="true" @close="showProfileDrawer = false" />
          </n-modal>
        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup>
import { computed, defineAsyncComponent, nextTick, onMounted, onUnmounted, reactive, ref, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import {
  NConfigProvider,
  NDialogProvider,
  NMessageProvider,
  NNotificationProvider,
  NModal,
  NIcon,
  zhCN,
  dateZhCN,
} from "naive-ui"
import { http } from "./api/http.js"
import { clearToken, getToken, setToken } from "./api/base.js"
import AdminUserDropdown from "./components/AdminUserDropdown.vue"
import { getIconComponent } from "./shared/icon-library.js"
import { useKeepAliveStore } from "./stores/keep-alive.js"
import { useMenuStore } from "./stores/menu.js"

const showProfileDrawer = ref(false)
const AdminProfileView = defineAsyncComponent(() => import("./components/AdminProfileView.vue"))

const USER_KEY = "smartai_admin_user"
const currentUser = ref(loadCachedUser())

function loadCachedUser() {
  try {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

async function refreshCurrentUser() {
  if (!getToken()) return
  try {
    const res = await http.get("/api/v1/auth/me")
    const user = res.data?.data ?? res.data
    if (user && user.id) {
      currentUser.value = user
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    }
  } catch (error) {
    if (error?.response?.status === 401 || error?.response?.status === 403) {
      clearToken()
      localStorage.removeItem(USER_KEY)
      currentUser.value = null
      window.location.assign("/login/")
    }
  }
}

const route = useRoute()
const router = useRouter()
const menu = useMenuStore()
const menuRegistered = computed(() => menu.registered.value)
const keepAlive = useKeepAliveStore()

const COLLAPSE_KEY = "smartai_admin_sider_collapsed"
const collapsed = ref(localStorage.getItem(COLLAPSE_KEY) === "true")
function onCollapse(v) {
  collapsed.value = v
  localStorage.setItem(COLLAPSE_KEY, String(v))
}

const visibleNavGroups = computed(() => {
  const tree = menu.tree.value
  return tree.map((node) => {
    if (node.component === "__group__") {
      return {
        key: node.menuKey,
        label: node.title,
        items: node.children.map((c) => ({
          key: c.menuKey,
          label: c.title,
          iconComp: getIconComponent(c.icon),
          path: c.path,
        })),
      }
    }
    return {
      key: node.menuKey,
      label: null,
      items: [{
        key: node.menuKey,
        label: node.title,
        iconComp: getIconComponent(node.icon),
        path: node.path,
      }],
    }
  })
})

const tabMeta = computed(() => {
  const map = {}
  for (const item of menu.rawList.value) {
    if (item.component === "__group__") continue
    map[item.menuKey] = {
      label: item.title,
      iconComp: getIconComponent(item.icon),
      path: item.path,
      affix: item.menuKey === "dashboard",
    }
  }
  return map
})

const AFFIX_KEY = "dashboard"
const TABS_STORE_KEY = "smartai_admin_open_tabs"

function loadOpenTabs() {
  try {
    const raw = JSON.parse(localStorage.getItem(TABS_STORE_KEY) || "[]")
    const valid = raw.filter((k) => tabMeta.value[k] && k !== AFFIX_KEY)
    return [AFFIX_KEY, ...valid]
  } catch {
    return [AFFIX_KEY]
  }
}

const openTabs = ref(loadOpenTabs())

function persistTabs() {
  const slim = openTabs.value.filter((k) => k !== AFFIX_KEY)
  localStorage.setItem(TABS_STORE_KEY, JSON.stringify(slim))
}

const refreshing = ref(false)
async function reloadView() {
  refreshing.value = true
  await nextTick()
  refreshing.value = false
}

const activeKey = computed(() => route.name || AFFIX_KEY)

const tabsWithMeta = computed(() =>
  openTabs.value
    .filter((k) => tabMeta.value[k])
    .map((k) => ({ key: k, ...tabMeta.value[k] })),
)

watch(
  tabMeta,
  () => {
    openTabs.value = openTabs.value.filter((k) => k === AFFIX_KEY || tabMeta.value[k])
    if (!openTabs.value.includes(AFFIX_KEY)) openTabs.value.unshift(AFFIX_KEY)
    persistTabs()
  },
  { immediate: true },
)

watch(
  () => route.name,
  (name) => {
    if (!name || !tabMeta.value[name]) return
    if (!openTabs.value.includes(name)) {
      openTabs.value.push(name)
      persistTabs()
    }
    if (route.meta?.cacheKey && route.meta?.cacheable) keepAlive.add(route.meta.cacheKey)
  },
  { immediate: true },
)

function closeTab(key) {
  if (key === AFFIX_KEY) return
  const idx = openTabs.value.indexOf(key)
  if (idx === -1) return
  const wasActive = activeKey.value === key
  openTabs.value.splice(idx, 1)
  keepAlive.remove(key)
  persistTabs()
  if (wasActive) {
    const next = openTabs.value[idx] || openTabs.value[idx - 1] || AFFIX_KEY
    router.push({ name: next })
  }
}

function closeOthers(key) {
  openTabs.value = openTabs.value.filter((k) => k === AFFIX_KEY || k === key)
  for (const cached of [...keepAlive.cachedViews.value]) {
    if (cached !== AFFIX_KEY && cached !== key) keepAlive.remove(cached)
  }
  persistTabs()
  if (activeKey.value !== key && activeKey.value !== AFFIX_KEY) {
    router.push({ name: key })
  }
}

function closeLeft(key) {
  const idx = openTabs.value.indexOf(key)
  if (idx === -1) return
  const removed = openTabs.value.filter((k, i) => k !== AFFIX_KEY && i < idx)
  openTabs.value = openTabs.value.filter((k, i) => k === AFFIX_KEY || i >= idx)
  removed.forEach((k) => keepAlive.remove(k))
  persistTabs()
  if (!openTabs.value.includes(activeKey.value)) {
    router.push({ name: key })
  }
}

function closeRight(key) {
  const idx = openTabs.value.indexOf(key)
  if (idx === -1) return
  const removed = openTabs.value.filter((_, i) => i > idx)
  openTabs.value = openTabs.value.filter((_, i) => i <= idx)
  removed.forEach((k) => keepAlive.remove(k))
  persistTabs()
  if (!openTabs.value.includes(activeKey.value)) {
    router.push({ name: key })
  }
}

function closeAll() {
  openTabs.value = [AFFIX_KEY]
  keepAlive.clear()
  persistTabs()
  if (activeKey.value !== AFFIX_KEY) {
    router.push({ name: AFFIX_KEY })
  }
}

const ctxMenu = reactive({
  show: false,
  x: 0,
  y: 0,
  targetKey: null,
})

function onTabContextMenu(e, key) {
  e.preventDefault()
  ctxMenu.targetKey = key
  ctxMenu.show = true
  ctxMenu.x = e.clientX
  ctxMenu.y = e.clientY
  nextTick(() => {
    const menuEl = document.querySelector(".tab-ctx-menu")
    if (!menuEl) return
    const rect = menuEl.getBoundingClientRect()
    if (rect.right > window.innerWidth - 8) {
      ctxMenu.x = window.innerWidth - rect.width - 8
    }
    if (rect.bottom > window.innerHeight - 8) {
      ctxMenu.y = window.innerHeight - rect.height - 8
    }
  })
}

function closeCtxMenu() {
  ctxMenu.show = false
  ctxMenu.targetKey = null
}

const ctxTargetIdx = computed(() =>
  ctxMenu.targetKey ? openTabs.value.indexOf(ctxMenu.targetKey) : -1,
)
const canCloseSelf = computed(() => ctxMenu.targetKey && ctxMenu.targetKey !== AFFIX_KEY)
const canCloseOthers = computed(() =>
  openTabs.value.filter((k) => k !== AFFIX_KEY && k !== ctxMenu.targetKey).length > 0,
)
const canCloseLeft = computed(() => {
  const idx = ctxTargetIdx.value
  if (idx <= 0) return false
  return openTabs.value.slice(0, idx).some((k) => k !== AFFIX_KEY)
})
const canCloseRight = computed(() => {
  const idx = ctxTargetIdx.value
  return idx >= 0 && idx < openTabs.value.length - 1
})
const canCloseAll = computed(() =>
  openTabs.value.some((k) => k !== AFFIX_KEY),
)

function onCtxAction(action) {
  const key = ctxMenu.targetKey
  closeCtxMenu()
  if (!key) return
  switch (action) {
    case "refresh":
      if (activeKey.value !== key) router.push({ name: key }).then(reloadView)
      else reloadView()
      break
    case "close": closeTab(key); break
    case "closeOthers": closeOthers(key); break
    case "closeLeft": closeLeft(key); break
    case "closeRight": closeRight(key); break
    case "closeAll": closeAll(); break
  }
}

function onGlobalClick() {
  if (ctxMenu.show) closeCtxMenu()
}

function onGlobalKey(e) {
  if (e.key === "Escape" && ctxMenu.show) closeCtxMenu()
}

onMounted(() => {
  document.addEventListener("click", onGlobalClick)
  document.addEventListener("keydown", onGlobalKey)
  refreshCurrentUser()
})

onUnmounted(() => {
  document.removeEventListener("click", onGlobalClick)
  document.removeEventListener("keydown", onGlobalKey)
})

const activePageTitle = computed(() =>
  tabMeta.value[route.name]?.label || route.meta?.title || "管理后台",
)

function navigate(key) {
  router.push({ name: key })
}

async function handleLogout() {
  try {
    await http.post("/api/v1/auth/logout")
  } catch {
    /* local cleanup is authoritative */
  }

  clearToken()
  setToken("")
  localStorage.removeItem(USER_KEY)
  menu.reset()
  keepAlive.clear()
  window.location.assign("/login/")
}

const themeOverrides = {
  common: {
    primaryColor: "#6366f1",
    primaryColorHover: "#4f46e5",
    primaryColorPressed: "#4338ca",
    primaryColorSuppl: "#818cf8",
    borderRadius: "6px",
    fontFamily: "'IBM Plex Sans', 'PingFang SC', system-ui, sans-serif",
  },
  DataTable: {
    thColor: "#F9FAFB",
    thTextColor: "#6B7280",
    tdColor: "#FFFFFF",
    tdColorHover: "#FAFBFC",
    borderColor: "rgba(226, 232, 240, 0.8)",
    thFontWeight: "600",
  },
  Pagination: {
    itemColorActive: "#EEF2FF",
    itemTextColorActive: "#6366f1",
    itemBorderActive: "1px solid #6366f1",
    itemBorderRadius: "4px",
  },
  Card: {
    color: "#ffffff",
    borderColor: "rgba(226, 232, 240, 0.8)",
    borderRadius: "8px",
    boxShadow: "0 4px 6px -1px rgba(15, 23, 42, 0.03), 0 2px 4px -2px rgba(15, 23, 42, 0.03), 0 0 0 1px rgba(15, 23, 42, 0.02)",
  },
  Modal: {
    borderRadius: "12px",
  },
  Drawer: {
    bodyPadding: "24px",
  },
  Input: {
    borderRadius: "6px",
  },
  Button: {
    borderRadiusMedium: "6px",
    borderRadiusSmall: "4px",
  },
  Tag: {
    borderRadius: "4px",
  },
}
</script>

<style scoped>
.admin-shell {
  --sb-width: 220px;
  --sb-collapsed: 56px;
  --sb-bg: #0f1117;
  --sb-border: rgba(255, 255, 255, 0.07);
  --sb-hover: rgba(255, 255, 255, 0.06);
  --sb-active-bg: rgba(99, 102, 241, 0.14);
  --sb-active-border: #818cf8;
  --sb-text: #9ca3af;
  --sb-text-active: #e0e7ff;
  --sb-label: #4b5563;
  --topbar-h: 56px;
  --topbar-tabs-h: 46px;
  --content-bg: #f8fafc;

  display: flex;
  height: 100dvh;
  overflow: hidden;
  background: var(--content-bg);
}

.sidebar {
  width: var(--sb-width);
  min-width: var(--sb-width);
  background: var(--sb-bg);
  border-right: 1px solid var(--sb-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.22s ease, min-width 0.22s ease;
  z-index: 10;
}

.admin-shell.sidebar-collapsed .sidebar {
  width: var(--sb-collapsed);
  min-width: var(--sb-collapsed);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  height: var(--topbar-h);
  padding: 0 14px;
  border-bottom: 1px solid var(--sb-border);
  flex-shrink: 0;
}

.brand-icon {
  width: 38px;
  height: 38px;
  min-width: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.brand-name {
  flex: 1;
  font-size: 16px;
  font-weight: 700;
  color: #f9fafb;
  letter-spacing: 0;
  white-space: nowrap;
}
.brand-name em { color: #818cf8; font-style: normal; }

.collapse-toggle,
.expand-toggle {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--sb-label);
  padding: 4px;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.15s, background 0.15s;
  flex-shrink: 0;
}
.collapse-toggle:hover,
.expand-toggle:hover {
  color: var(--sb-text);
  background: var(--sb-hover);
}

.expand-toggle {
  margin: 10px auto;
  display: flex;
}

.sidebar-nav {
  flex: 1;
  padding: 8px 8px 0;
  overflow-y: auto;
  overflow-x: hidden;
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.1) transparent;
}

.nav-group-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--sb-label);
  padding: 14px 8px 6px;
  white-space: nowrap;
}

.nav-group-sep {
  height: 1px;
  background: var(--sb-border);
  margin: 10px 6px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 9px;
  width: 100%;
  padding: 7px 10px;
  border: none;
  background: none;
  border-radius: 7px;
  cursor: pointer;
  color: var(--sb-text);
  font-size: 13px;
  font-weight: 500;
  font-family: inherit;
  text-align: left;
  white-space: nowrap;
  transition: background 0.12s, color 0.12s;
  position: relative;
  margin-bottom: 1px;
}

.nav-item:hover {
  background: var(--sb-hover);
  color: #d1d5db;
}

.nav-item.active {
  background: var(--sb-active-bg);
  color: var(--sb-text-active);
}
.nav-item.active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 3px;
  height: 60%;
  background: var(--sb-active-border);
  border-radius: 0 2px 2px 0;
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  min-width: 16px;
}

.nav-label { flex: 1; }

.admin-shell.sidebar-collapsed .nav-item {
  justify-content: center;
  padding: 9px;
}
.admin-shell.sidebar-collapsed .nav-group-label { display: none; }

.main-area {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.topbar {
  background: var(--c-surface);
  border-bottom: 1px solid rgba(226, 232, 240, 0.8);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  z-index: 5;
}

.topbar-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.topbar-row--head {
  height: var(--topbar-h);
  min-height: var(--topbar-h);
}

.topbar-left { display: flex; align-items: center; gap: 10px; min-width: 0; }
.topbar-right { display: flex; align-items: center; gap: 10px; }

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--c-text-secondary);
  min-width: 0;
}
.crumb {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.crumb-root {
  color: var(--c-text-tertiary);
  font-weight: 500;
}
.crumb-current {
  color: var(--c-text-primary);
  font-weight: 600;
  letter-spacing: 0;
}
.crumb-sep {
  color: var(--c-border-strong);
  flex-shrink: 0;
}

.topbar-tabs {
  display: flex;
  align-items: center;
  gap: 6px;
  height: var(--topbar-tabs-h);
  padding: 0 24px;
  background: var(--c-surface);
  border-top: 1px solid rgba(226, 232, 240, 0.8);
  border-bottom: 1px solid rgba(226, 232, 240, 0.8);
  overflow-x: auto;
  scrollbar-width: none;
}
.topbar-tabs::-webkit-scrollbar { display: none; }

.top-tab {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 10px 0 12px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 6px;
  background: var(--c-surface-hover);
  cursor: pointer;
  font-family: inherit;
  font-size: 12.5px;
  font-weight: 500;
  color: var(--c-text-secondary);
  white-space: nowrap;
  transition: all 0.15s ease;
  user-select: none;
}
.top-tab:hover {
  color: var(--c-text-primary);
  background: var(--c-bg-subtle);
  border-color: var(--c-border-strong);
}
.top-tab.active {
  color: var(--c-info-text);
  font-weight: 600;
  background: var(--c-info-bg);
  border-color: var(--c-info-border);
}

.top-tab-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  opacity: 0.7;
}
.top-tab.active .top-tab-icon { opacity: 1; color: var(--c-info-dot); }

.top-tab-affix {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 12px;
  height: 12px;
  color: var(--c-text-secondary);
  margin-left: 1px;
  opacity: 0.85;
}

.top-tab-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  margin-left: 1px;
  border-radius: 4px;
  color: var(--c-text-tertiary);
  opacity: 0;
  transition: opacity 0.12s, background 0.12s, color 0.12s;
  cursor: pointer;
}
.top-tab:hover .top-tab-close,
.top-tab.active .top-tab-close { opacity: 1; }
.top-tab-close:hover {
  background: var(--c-error-bg);
  color: var(--c-error-dot);
}

.tab-ctx-menu {
  position: fixed;
  z-index: 1000;
  min-width: 168px;
  padding: 5px;
  background: var(--c-surface);
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 8px;
  box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.08), 0 4px 6px -4px rgba(15, 23, 42, 0.04);
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.ctx-item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 7px 10px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  font-weight: 500;
  color: var(--c-text-secondary);
  text-align: left;
  transition: background 0.1s, color 0.1s;
}
.ctx-item:hover:not(:disabled) {
  background: var(--c-bg-subtle);
  color: var(--c-text-primary);
}
.ctx-item:disabled {
  color: var(--c-text-tertiary);
  cursor: not-allowed;
}
.ctx-item:disabled .ctx-icon { color: var(--c-neutral-border); }

.ctx-icon {
  width: 13px;
  height: 13px;
  color: var(--c-text-muted);
  flex-shrink: 0;
}
.ctx-item:hover:not(:disabled) .ctx-icon { color: var(--c-text-primary); }

.ctx-label { flex: 1; }

.ctx-sep {
  height: 1px;
  background: rgba(226, 232, 240, 0.8);
  margin: 4px 6px;
}

.ctx-item--danger { color: var(--c-error-dot); }
.ctx-item--danger:hover:not(:disabled) {
  background: var(--c-error-bg);
  color: var(--c-error-text);
}
.ctx-item--danger .ctx-icon { color: var(--c-error-dot); }
.ctx-item--danger:hover:not(:disabled) .ctx-icon { color: var(--c-error-text); }

.ctx-fade-enter-active,
.ctx-fade-leave-active {
  transition: opacity 0.1s ease, transform 0.1s ease;
}
.ctx-fade-enter-from,
.ctx-fade-leave-to {
  opacity: 0;
  transform: scale(0.96);
  transform-origin: top left;
}

.content-area {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  overflow-x: auto;
  padding: 24px;
  scrollbar-width: thin;
  scrollbar-color: var(--c-border-strong) transparent;
}

.admin-initial-loader {
  position: fixed;
  inset: 0;
  z-index: 99999;
  background-color: #fff;
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  animation: fadeIn 0.4s ease-in-out 1 forwards;
}

.loader-inner {
  max-width: 100%;
  width: 160px;
  margin: auto;
  position: relative;
  text-align: center;
}

.loader-text {
  font-size: 20px;
  line-height: 24px;
  color: #314666;
  padding-bottom: 20px;
  font-weight: 500;
  letter-spacing: 0.5px;
  transform: translateY(20px);
  animation: slideIn 0.4s ease-in-out 1 forwards;
}

.loading-progress {
  width: 100%;
  height: 4px;
  border-radius: 4px;
  overflow: hidden;
  background-color: #f2f3f9;
  position: relative;
}

.loading-track {
  height: 100%;
  width: 100%;
  background-color: #1055ff;
  border-radius: 4px;
  animation: loading-track 1.3s infinite linear;
  transform-origin: 0% 50%;
}

@keyframes fadeIn {
  from { opacity: 0.01; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { transform: translateY(20px); }
  to { transform: translateY(0); }
}

@keyframes loading-track {
  0% {
    transform: translateX(0) scaleX(0);
  }
  10% {
    transform: translateX(0) scaleX(0.2);
  }
  40% {
    transform: translateX(0) scaleX(0.7);
  }
  60% {
    transform: translateX(60%) scaleX(0.4);
  }
  100% {
    transform: translateX(100%) scaleX(0.2);
  }
}
</style>
