<template>
  <n-dropdown :options="options" @select="handleSelect" trigger="click">
    <button class="user-dropdown-btn">
      <span class="user-dropdown-icon" v-html="icons.profile"></span>
      <span class="user-dropdown-name">{{ displayName }}</span>
      <svg class="user-dropdown-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="6 9 12 15 18 9"/>
      </svg>
    </button>
  </n-dropdown>
</template>

<script setup>
import { computed, h } from "vue"
import { NDropdown } from "naive-ui"
import { useMenuStore } from "../stores/menu.js"

const props = defineProps({
  user: { type: Object, default: () => null }
})

const emit = defineEmits(["profile", "logout"])

const menu = useMenuStore()

// Shared icons (copied from App.vue or passed down, but for simplicity we'll just redefine the small svgs here)
const icons = {
  profile: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
  logout: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>`,
  debug:   `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h0a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51h0a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v0a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>`,
}

const displayName = computed(() => {
  if (!props.user) return 'Admin'
  return props.user.display_name || props.user.email?.split('@')[0] || 'Admin'
})

const isAdmin = computed(() => {
  const u = props.user
  if (!u) return false
  return Boolean(u.fixed) || u.role === "admin" || (Array.isArray(u.permissions) && u.permissions.includes("*"))
})

const options = computed(() => {
  const base = [
    { label: "我的资料", key: "profile", icon: () => h('span', { innerHTML: icons.profile, style: 'display:flex;align-items:center;' }) },
  ]
  if (isAdmin.value) {
    base.push({ type: 'divider', key: 'd0' })
    base.push({
      label: menu.debugShowAll.value ? "✓ 调试：显示全部菜单" : "调试：显示全部菜单",
      key: "toggle-debug-menu",
      icon: () => h('span', { innerHTML: icons.debug, style: 'display:flex;align-items:center;' }),
    })
  }
  base.push({ type: 'divider', key: 'd1' })
  base.push({ label: "退出登录", key: "logout", icon: () => h('span', { innerHTML: icons.logout, style: 'display:flex;align-items:center;' }) })
  return base
})

function handleSelect(key) {
  if (key === "profile" || key === "logout") emit(key)
  else if (key === "toggle-debug-menu") menu.setDebugShowAll(!menu.debugShowAll.value)
}
</script>

<style scoped>
.user-dropdown-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 28px;
  padding: 0 6px 0 2px;
  border: none;
  background: transparent;
  border-radius: 14px;
  cursor: pointer;
  transition: background 0.15s;
}
.user-dropdown-btn:hover {
  background: var(--c-bg-subtle);
}
.user-dropdown-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 12px;
  background: rgba(99, 102, 241, 0.1);
  color: var(--c-brand-strong);
}
.user-dropdown-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--c-text-secondary);
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.user-dropdown-chevron {
  color: var(--c-text-tertiary);
  transition: transform 0.15s;
}
</style>
