<template>
  <!--
    AppShell provides the two-column workspace layout (sidebar + content area).
    The global navigation header now lives in AppLayout.vue so this component
    only handles the inner layout structure.
  -->
  <div class="flex h-full overflow-hidden">
    <slot name="sidebar" />
    <slot name="content" />
  </div>
</template>
