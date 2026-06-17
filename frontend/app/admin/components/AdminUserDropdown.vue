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

const props = defineProps({
  user: { type: Object, default: () => null }
})

const emit = defineEmits(["profile", "logout"])

// Shared icons (copied from App.vue or passed down, but for simplicity we'll just redefine the small svgs here)
const icons = {
  profile: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
  logout: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>`
}

const displayName = computed(() => {
  if (!props.user) return 'Admin'
  return props.user.display_name || props.user.email?.split('@')[0] || 'Admin'
})

const options = computed(() => [
  { label: "我的资料", key: "profile", icon: () => h('span', { innerHTML: icons.profile, style: 'display:flex;align-items:center;' }) },
  { type: 'divider', key: 'd1' },
  { label: "退出登录", key: "logout", icon: () => h('span', { innerHTML: icons.logout, style: 'display:flex;align-items:center;' }) }
])

function handleSelect(key) {
  if (key === "profile" || key === "logout") emit(key)
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
