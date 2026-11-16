<template>
  <aside class="role-list-pane">
    <div class="pane-header">
      <span>角色列表</span>
    </div>
    <n-spin :show="loading">
      <n-list hoverable clickable>
        <n-list-item
          v-for="role in roles"
          :key="role.code"
          :class="{ 'is-active': selectedRole?.code === role.code }"
          @click="emit('select', role)"
        >
          <div class="role-row">
            <div class="role-main">
              <strong>{{ role.name }}</strong>
              <span>{{ role.code }}</span>
            </div>
            <div class="role-row-actions" @click.stop>
              <n-tag v-if="role.builtin" size="tiny" :bordered="false">内置</n-tag>
              <n-button size="tiny" quaternary @click="emit('edit', role)">编辑</n-button>
              <n-button
                size="tiny"
                quaternary
                type="error"
                :disabled="role.builtin"
                @click="emit('delete', role)"
              >
                删除
              </n-button>
            </div>
          </div>
        </n-list-item>
      </n-list>
    </n-spin>
  </aside>
</template>

<script setup>
import { NButton, NList, NListItem, NSpin, NTag } from "naive-ui"

defineProps({
  roles: {
    type: Array,
    required: true,
  },
  selectedRole: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(["select", "edit", "delete"])
</script>

<style scoped>
.role-list-pane {
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

.role-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
}

.role-main {
  display: grid;
  gap: var(--sp-1);
  min-width: 0;
}

.role-main span {
  color: var(--c-text-muted);
  font-size: var(--fs-sm);
}

.role-row-actions {
  display: inline-flex;
  align-items: center;
  gap: var(--sp-1);
  flex-shrink: 0;
}

:deep(.n-list-item.is-active) {
  background: var(--c-brand-soft);
}
</style>
