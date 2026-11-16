<template>
  <button
    type="button"
    class="id-chip"
    :class="{ 'is-loading': loading }"
    :title="tooltip"
    :disabled="loading"
    @click="handleClick"
  >
    <span class="id-chip-text">{{ text }}</span>
    <!-- 复制 / loading 图标 -->
    <svg
      v-if="!loading"
      class="id-chip-icon"
      width="13"
      height="13"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
      <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
    </svg>
    <svg
      v-else
      class="id-chip-icon is-spinning"
      width="13"
      height="13"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      stroke-linecap="round"
      stroke-linejoin="round"
    >
      <line x1="12" y1="2" x2="12" y2="6" />
      <line x1="12" y1="18" x2="12" y2="22" />
      <line x1="4.93" y1="4.93" x2="7.76" y2="7.76" />
      <line x1="16.24" y1="16.24" x2="19.07" y2="19.07" />
      <line x1="2" y1="12" x2="6" y2="12" />
      <line x1="18" y1="12" x2="22" y2="12" />
      <line x1="4.93" y1="19.07" x2="7.76" y2="16.24" />
      <line x1="16.24" y1="7.76" x2="19.07" y2="4.93" />
    </svg>
  </button>
</template>

<script setup>
import { ref } from "vue"
import { useMessage } from "naive-ui"
import { copyWithToast } from "#/admin/utils/clipboard.js"

const props = defineProps({
  // 展示文本（通常是脱敏后的短串）
  text: { type: String, required: true },
  // 直接已知的完整复制值；优先级低于 copyFn
  copyValue: { type: String, default: "" },
  // 异步获取复制值的回调（用于 AccessKey 这种需要拉 reveal API 的场景）
  copyFn: { type: Function, default: null },
  // hover 提示
  tooltip: { type: String, default: "点击复制" },
  // 复制成功 toast 文案
  toastText: { type: String, default: "已复制" },
})

const message = useMessage()
const loading = ref(false)

async function handleClick() {
  if (loading.value) return
  let value = props.copyValue
  if (!value && props.copyFn) {
    loading.value = true
    try {
      value = await props.copyFn()
    } catch (e) {
      message.error(e?.message || "获取失败")
      loading.value = false
      return
    }
    loading.value = false
  }
  if (!value) {
    message.warning("没有可复制的内容")
    return
  }
  await copyWithToast(value, message, props.toastText)
}
</script>

<style scoped>
.id-chip {
  display: inline-flex;
  flex-direction: row;
  align-items: center;
  flex-wrap: nowrap;
  gap: 6px;
  white-space: nowrap;
  line-height: 1;
  background: linear-gradient(135deg, #f0f9ff 0%, #f5f3ff 100%);
  border: 1px solid #c7d2fe;
  color: #4338ca;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.15s ease;
  outline: none;
  user-select: all;
  vertical-align: middle;
  box-sizing: border-box;
}
.id-chip:hover {
  background: linear-gradient(135deg, #dbeafe 0%, #ede9fe 100%);
  border-color: #818cf8;
  color: #3730a3;
  box-shadow: 0 1px 3px rgba(79, 70, 229, 0.15);
}
.id-chip:active {
  transform: scale(0.97);
}
.id-chip:disabled {
  cursor: wait;
  opacity: 0.7;
}
.id-chip-text {
  letter-spacing: 0.02em;
  flex-shrink: 0;
}
.id-chip-icon {
  opacity: 0.55;
  flex-shrink: 0;
  transition: opacity 0.15s ease;
}
.id-chip:hover .id-chip-icon {
  opacity: 1;
}
.id-chip-icon.is-spinning {
  animation: chip-spin 0.8s linear infinite;
  opacity: 0.85;
}
@keyframes chip-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>

