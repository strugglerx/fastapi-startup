<template>
  <header class="admin-page-header">
    <div class="admin-page-header__text">
      <h2 class="admin-page-header__title">
        <slot name="title">{{ title }}</slot>
      </h2>
      <p v-if="$slots.subtitle || subtitle" class="admin-page-header__sub">
        <slot name="subtitle">{{ subtitle }}</slot>
      </p>
    </div>
    <div v-if="$slots.actions" class="admin-page-header__actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<script setup>
/**
 * AdminPageHeader — the title block every admin view starts with.
 *
 * Usage:
 *   <AdminPageHeader title="任务" subtitle="生成记录与回调状态">
 *     <template #actions>
 *       <button class="admin-btn admin-btn--primary">刷新</button>
 *     </template>
 *   </AdminPageHeader>
 */
defineProps({
  title:    { type: String, default: "" },
  subtitle: { type: String, default: "" },
})
</script>
