<template>
  <main class="grant-pane">
    <div class="pane-header">
      <span>{{ selectedRole ? `${selectedRole.name} 的菜单授权` : "菜单授权" }}</span>
      <n-button
        type="primary"
        :loading="saving"
        :disabled="!selectedRole || selectedRole.code === 'admin'"
        @click="emit('save')"
      >
        保存
      </n-button>
    </div>
    <n-alert v-if="selectedRole?.code === 'admin'" type="info" :bordered="false" class="role-alert">
      admin 拥有全部菜单与配置权，无需配置授权
    </n-alert>
    <n-alert v-if="!isAdminRole && adminOnlyCount" type="warning" :bordered="false" class="role-alert">
      下方 {{ adminOnlyCount }} 项标记为「仅 admin 可用」，对当前角色禁选；要解锁请由 fixed=True 超级管理员去菜单管理改。
    </n-alert>
    <n-spin :show="loading">
      <n-tree
        block-line
        checkable
        cascade
        :data="processedTree"
        :checked-keys="displayCheckedKeys"
        :render-label="renderLabel"
        @update:checked-keys="onCheckedKeys"
      />
    </n-spin>
  </main>
</template>

<script setup>
import { computed, h } from "vue"
import { NAlert, NButton, NIcon, NSpin, NTag, NTree } from "naive-ui"
import { Lock as LockIcon } from "@lucide/vue"

const props = defineProps({
  selectedRole: {
    type: Object,
    default: null,
  },
  menuTree: {
    type: Array,
    required: true,
  },
  allMenuKeys: {
    type: Array,
    required: true,
  },
  checkedKeys: {
    type: Array,
    required: true,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  saving: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(["update:checkedKeys", "save"])

const isAdminRole = computed(() => props.selectedRole?.code === "admin")
const displayCheckedKeys = computed(() => (isAdminRole.value ? props.allMenuKeys : props.checkedKeys))

// 非 admin 角色 → admin_only 节点 disabled；并递归同步到 children
// 这层在前端层防误点；后端 set_role_grants 也有最终防线
function decorate(node) {
  const raw = node?.raw || {}
  const out = { ...node }
  if (!isAdminRole.value && raw.adminOnly) {
    out.disabled = true
  }
  if (Array.isArray(node.children) && node.children.length) {
    out.children = node.children.map(decorate)
  }
  return out
}
const processedTree = computed(() => (props.menuTree || []).map(decorate))

// 统计 admin_only 节点数量（用于顶上 banner 提示）
function countAdminOnly(nodes) {
  let n = 0
  for (const node of nodes || []) {
    if (node?.raw?.adminOnly) n++
    if (Array.isArray(node.children)) n += countAdminOnly(node.children)
  }
  return n
}
const adminOnlyCount = computed(() => countAdminOnly(props.menuTree || []))

function renderLabel({ option }) {
  const raw = option.raw || {}
  const isAdminOnly = !!raw.adminOnly && !isAdminRole.value
  const isButton = raw.component === "__button__"
  const lockIcon = isAdminOnly
    ? h(NIcon, {
        size: 14,
        title: "仅 admin 可用，不能授权给当前角色",
        style: "color: #d97706; vertical-align: -2px; margin-right: 6px;",
      }, { default: () => h(LockIcon) })
    : null
  if (isButton) {
    return h("span", { style: "display: inline-flex; align-items: center; gap: 6px; white-space: nowrap;" }, [
      lockIcon,
      h("span", { style: "color: #e08c00; font-weight: 500;" }, option.label),
      h(NTag, { size: "tiny", bordered: false, type: "warning" }, { default: () => raw.menuKey }),
    ])
  }
  if (!raw.hidden && !isAdminOnly) return option.label
  return h("span", { class: "role-tree-label role-tree-label--muted" }, [
    lockIcon,
    h("span", option.label),
    raw.hidden
      ? h(NTag, { size: "tiny", bordered: false, type: "default" }, { default: () => "hidden" })
      : null,
  ])
}

function onCheckedKeys(keys) {
  if (props.selectedRole?.code !== "admin") emit("update:checkedKeys", keys)
}
</script>

<style scoped>
.grant-pane {
  border: 1px solid var(--c-border);
  border-radius: var(--r-xl);
  background: var(--c-surface);
  padding: var(--sp-4);
  box-shadow: var(--sh-1);
}

.pane-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  min-height: 32px;
  margin-bottom: var(--sp-3);
  font-weight: var(--fw-bold);
  color: var(--c-text-primary);
}

.role-alert {
  margin-bottom: var(--sp-3);
}

.role-tree-label {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-2);
}

.role-tree-label--muted {
  color: var(--c-text-faint);
}
</style>
