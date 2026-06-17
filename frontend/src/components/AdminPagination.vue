<template>
  <div class="admin-pagination-bar" v-if="itemCount > 0">
    <span class="admin-pagination-bar__info">
      共 {{ itemCount }} 条记录
    </span>
    <n-pagination
      :page="page"
      @update:page="(p) => $emit('update:page', p)"
      :page-size="pageSize"
      @update:page-size="(s) => $emit('update:pageSize', s)"
      :item-count="itemCount"
      :page-sizes="pageSizes"
      show-size-picker
      size="small"
    />
  </div>
</template>

<script setup>
import { NPagination } from "naive-ui"

defineProps({
  page: {
    type: Number,
    required: true
  },
  pageSize: {
    type: Number,
    required: true
  },
  itemCount: {
    type: Number,
    required: true
  },
  pageSizes: {
    type: Array,
    default: () => [15, 30, 60]
  }
})

defineEmits(["update:page", "update:pageSize"])
</script>
