<template>
  <!--
    Label/value row used in admin detail drawers.  Label sits in a fixed-width
    column so multiple rows align without ad-hoc CSS in each page.
  -->
  <div class="flex items-start gap-3">
    <span class="w-20 shrink-0 text-[10px] font-medium uppercase tracking-wider text-slate-400 pt-0.5">
      {{ label }}
    </span>
    <span :class="['flex-1 min-w-0 text-slate-700', mono ? 'font-mono break-all' : '']">
      <slot />
    </span>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  mono:  { type: Boolean, default: false },
});
</script>
