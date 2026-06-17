<template>
  <div class="media-input">
    <n-input
      :value="modelValue"
      :placeholder="placeholder"
      clearable
      @update:value="(v) => emit('update:modelValue', v)"
    />
    <n-button
      :disabled="true"
      title="上传接口尚未启用（待七牛 upToken 接口完成）"
    >
      <template #icon><span>⤴</span></template>
      上传
    </n-button>
    <n-button
      v-if="modelValue"
      quaternary
      circle
      title="预览（在新窗口打开）"
      @click="preview"
    >
      🔍
    </n-button>
  </div>
</template>

<script setup>
import { NButton, NInput } from "naive-ui"

const props = defineProps({
  modelValue: { type: String, default: "" },
  placeholder: { type: String, default: "URL 或 七牛 key" },
})
const emit = defineEmits(["update:modelValue"])

function preview() {
  const v = (props.modelValue || "").trim()
  if (!v) return
  const url = /^https?:\/\//i.test(v) ? v : `https://qiniu.muqiangyun.cn/${v.replace(/^\/+/, "")}`
  window.open(url, "_blank", "noopener")
}
</script>

<style scoped>
.media-input {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.media-input :deep(.n-input) { flex: 1; }
</style>
