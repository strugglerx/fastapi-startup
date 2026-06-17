<template>
  <div class="admin-empty">
    <div class="admin-empty__icon">
      <slot name="icon">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
      </slot>
    </div>
    <p class="admin-empty__title">
      <slot name="title">{{ title }}</slot>
    </p>
    <p v-if="$slots.desc || desc" class="admin-empty__desc">
      <slot name="desc">{{ desc }}</slot>
    </p>
    <div v-if="$slots.action" class="admin-empty__action">
      <slot name="action" />
    </div>
  </div>
</template>

<script setup>
/**
 * AdminEmptyState — drop inside an .admin-data-shell when zero rows.
 *
 *   <div class="admin-data-shell">
 *     <AdminEmptyState title="还没有任务" desc="生成第一个文档后任务会出现在这里">
 *       <template #action>
 *         <button class="admin-btn admin-btn--primary">新建任务</button>
 *       </template>
 *     </AdminEmptyState>
 *   </div>
 */
defineProps({
  title: { type: String, default: "暂无数据" },
  desc:  { type: String, default: "" },
})
</script>

<style scoped>
.admin-empty__action { margin-top: var(--sp-2); }
</style>
