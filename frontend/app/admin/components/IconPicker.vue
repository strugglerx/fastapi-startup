<template>
  <n-popover trigger="click" placement="bottom-start" :width="360">
    <template #trigger>
      <n-button>
        <n-icon v-if="iconComp" :size="16" style="margin-right: 6px">
          <component :is="iconComp" />
        </n-icon>
        <span>{{ modelValue || "选择图标" }}</span>
      </n-button>
    </template>
    <div class="icon-picker">
      <n-input v-model:value="query" placeholder="搜索图标..." clearable />
      <div class="icon-grid">
        <button
          v-for="icon in filtered"
          :key="icon.code"
          class="icon-cell"
          :class="{ active: modelValue === icon.code }"
          :title="`${icon.label} (${icon.code})`"
          type="button"
          @click="$emit('update:modelValue', icon.code)"
        >
          <n-icon :size="20">
            <component :is="icon.component" />
          </n-icon>
        </button>
      </div>
      <div v-if="modelValue" class="icon-picker-footer">
        <n-button size="small" @click="$emit('update:modelValue', null)">清除</n-button>
      </div>
    </div>
  </n-popover>
</template>

<script setup>
import { computed, ref } from "vue"
import { NButton, NIcon, NInput, NPopover } from "naive-ui"
import { getIconComponent, searchIcons } from "../shared/icon-library.js"

const props = defineProps({
  modelValue: { type: String, default: null },
})

defineEmits(["update:modelValue"])

const query = ref("")
const filtered = computed(() => searchIcons(query.value))
const iconComp = computed(() => getIconComponent(props.modelValue))
</script>

<style scoped>
.icon-picker {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 4px;
}

.icon-grid {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 6px;
  max-height: 280px;
  overflow-y: auto;
}

.icon-cell {
  width: 36px;
  height: 36px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--c-border, #e2e8f0);
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
  padding: 0;
  color: var(--c-text-secondary, #475569);
}

.icon-cell:hover {
  border-color: #6366f1;
  color: #6366f1;
}

.icon-cell.active {
  border-color: #6366f1;
  background: #eef2ff;
  color: #6366f1;
}

.icon-picker-footer {
  display: flex;
  justify-content: flex-end;
}
</style>
