<template>
  <span
    class="admin-status-badge"
    :class="`admin-status--${tone}`"
  >
    <span v-if="dot" class="admin-status-badge__dot"></span>
    <slot>{{ label }}</slot>
  </span>
</template>

<script setup>
/**
 * AdminStatusBadge — 5 semantic channels: success / warning / error / info / neutral.
 *
 *   <AdminStatusBadge tone="success">已完成</AdminStatusBadge>
 *   <AdminStatusBadge tone="warning" dot>排队中</AdminStatusBadge>
 *
 * Tone is the source of truth — never pass raw hex colors. If you need
 * a new channel, add it to admin-tokens.css and admin-shared.css first.
 */
defineProps({
  tone:  { type: String, default: "neutral", validator: (v) => ["success", "warning", "error", "info", "neutral"].includes(v) },
  label: { type: String, default: "" },
  dot:   { type: Boolean, default: false },
})
</script>
