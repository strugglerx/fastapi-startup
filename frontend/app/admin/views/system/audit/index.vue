<template>
  <div class="admin-page">
    <AdminPageHeader title="审计日志" subtitle="系统操作日志记录，审计关键数据的增删改操作" />

    <div class="admin-toolbar">
      <n-input
        v-model:value="filters.username"
        clearable
        placeholder="操作人用户名…"
        @input="debouncedLoadRows"
        class="toolbar-search"
      >
        <template #prefix><span class="search-icon" /></template>
      </n-input>
      <n-input
        v-model:value="filters.action"
        clearable
        placeholder="操作动作或描述…"
        @input="debouncedLoadRows"
        class="toolbar-search"
      >
        <template #prefix><span class="search-icon" /></template>
      </n-input>
      <n-select
        v-model:value="filters.status_code"
        clearable
        placeholder="响应状态"
        :options="statusOptions"
        @update:value="reloadFirstPage"
        class="toolbar-select"
      />
      <n-button @click="resetFilters" class="toolbar-btn">重置</n-button>
    </div>

    <div class="admin-data-shell audit-data-shell">
      <n-data-table
        remote
        :columns="columns"
        :data="rows"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row) => row.id"
        @update:page="onPageChange"
        @update:page-size="onPageSizeChange"
      />
    </div>

    <n-modal v-model:show="showDetails" preset="card" title="日志详情" style="width: 700px; max-width: 95vw;">
      <n-descriptions label-placement="left" bordered :column="2" class="audit-details-desc">
        <n-descriptions-item label="操作人">
          {{ selectedRow.username || "系统/未登录" }} <span v-if="selectedRow.user_id" class="text-muted">(ID: {{ selectedRow.user_id }})</span>
        </n-descriptions-item>
        <n-descriptions-item label="操作时间">
          {{ formatTime(selectedRow.created_at) }}
        </n-descriptions-item>
        <n-descriptions-item label="操作动作">
          {{ selectedRow.description || "未知" }}
        </n-descriptions-item>
        <n-descriptions-item label="动作编码">
          <code>{{ selectedRow.action }}</code>
        </n-descriptions-item>
        <n-descriptions-item label="请求方式">
          <n-tag :type="getMethodTagType(selectedRow.method)" size="small" bordered="false">{{ selectedRow.method }}</n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="HTTP 状态码">
          <n-tag :type="getStatusTagType(selectedRow.status_code)" size="small" round bordered="false">{{ selectedRow.status_code }}</n-tag>
        </n-descriptions-item>
        <n-descriptions-item label="耗时">
          {{ selectedRow.cost_time }} ms
        </n-descriptions-item>
        <n-descriptions-item label="IP 地址">
          {{ selectedRow.ip_address }} <span v-if="selectedRow.ip_location" class="text-muted">({{ selectedRow.ip_location }})</span>
        </n-descriptions-item>
        <n-descriptions-item label="请求路径" :span="2">
          <code class="code-path">{{ selectedRow.path }}</code>
        </n-descriptions-item>
        <n-descriptions-item label="浏览器 User Agent" :span="2">
          <span class="ua-text">{{ selectedRow.user_agent }}</span>
        </n-descriptions-item>
        <n-descriptions-item v-if="selectedRow.query_params" label="查询参数 (Query)" :span="2">
          <pre class="json-block">{{ selectedRow.query_params }}</pre>
        </n-descriptions-item>
        <n-descriptions-item v-if="selectedRow.request_body" label="请求体 (Body)" :span="2">
          <pre class="json-block">{{ formatJson(selectedRow.request_body) }}</pre>
        </n-descriptions-item>
      </n-descriptions>
      <template #footer>
        <div class="modal-actions">
          <n-button type="primary" @click="showDetails = false">关闭</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { h, onMounted, reactive, ref } from "vue"
import { NButton, NDataTable, NDescriptions, NDescriptionsItem, NForm, NFormItem, NInput, NModal, NSelect, NTag } from "naive-ui"
import AdminPageHeader from "../../../components/AdminPageHeader.vue"
import { auditApi } from "../../../api/audit.js"
import { notifyError } from "../../../api/feedback.js"

defineOptions({ name: "SystemAuditList" })

const loading = ref(false)
const rows = ref([])

const filters = reactive({
  username: "",
  action: "",
  status_code: null,
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  prefix: ({ itemCount }) => `共 ${itemCount} 条`,
})

const statusOptions = [
  { label: "成功 (2xx)", value: 200 },
  { label: "客户端错误 (4xx)", value: 400 },
  { label: "服务端错误 (5xx)", value: 500 },
]

const showDetails = ref(false)
const selectedRow = ref({})

const columns = [
  {
    title: "时间",
    key: "created_at",
    width: 170,
    render(row) {
      return formatTime(row.created_at)
    }
  },
  {
    title: "操作人",
    key: "username",
    width: 120,
    render(row) {
      return row.username || h("span", { style: "color: #9ca3af; font-style: italic" }, "系统/未登录")
    }
  },
  {
    title: "操作动作",
    key: "description",
    width: 185,
    render(row) {
      return h("div", [
        h("div", { style: "font-weight: 500; color: #1f2937" }, row.description || "未知操作"),
        h("div", { style: "font-size: 11px; color: #9ca3af; font-family: monospace" }, row.action)
      ])
    }
  },
  {
    title: "方式",
    key: "method",
    width: 80,
    render(row) {
      return h(
        NTag,
        { type: getMethodTagType(row.method), size: "small", bordered: false },
        { default: () => row.method }
      )
    }
  },
  {
    title: "请求路径",
    key: "path",
    ellipsis: { tooltip: true }
  },
  {
    title: "IP/归属地",
    key: "ip_address",
    width: 160,
    render(row) {
      return h("div", [
        h("div", { class: "font-mono" }, row.ip_address || "-"),
        row.ip_location ? h("div", { style: "font-size: 11px; color: #9ca3af" }, row.ip_location) : null
      ])
    }
  },
  {
    title: "状态",
    key: "status_code",
    width: 80,
    render(row) {
      return h(
        NTag,
        { type: getStatusTagType(row.status_code), size: "small", round: true, bordered: false },
        { default: () => String(row.status_code) }
      )
    }
  },
  {
    title: "耗时",
    key: "cost_time",
    width: 100,
    render(row) {
      const time = row.cost_time
      let style = "color: #10b981"
      if (time > 1000) style = "color: #ef4444"
      else if (time > 500) style = "color: #f59e0b"
      return h("span", { style, class: "font-mono" }, `${time} ms`)
    }
  },
  {
    title: "操作",
    key: "actions",
    width: 80,
    render(row) {
      return h(
        NButton,
        {
          type: "primary",
          size: "tiny",
          quaternary: true,
          onClick: () => viewDetails(row)
        },
        { default: () => "详情" }
      )
    }
  }
]

let timer = null
function debouncedLoadRows() {
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => {
    reloadFirstPage()
  }, 300)
}

function reloadFirstPage() {
  pagination.page = 1
  loadRows()
}

function resetFilters() {
  filters.username = ""
  filters.action = ""
  filters.status_code = null
  reloadFirstPage()
}

async function loadRows() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.pageSize,
      username: filters.username || undefined,
      action: filters.action || undefined,
    }
    if (filters.status_code) {
      params.status_code = filters.status_code
    }
    const res = await auditApi.list(params)
    rows.value = res.items || []
    pagination.itemCount = res.total || 0
  } catch (err) {
    notifyError(err.message || "加载审计日志失败")
  } finally {
    loading.value = false
  }
}

function onPageChange(page) {
  pagination.page = page
  loadRows()
}

function onPageSizeChange(pageSize) {
  pagination.pageSize = pageSize
  reloadFirstPage()
}

function viewDetails(row) {
  selectedRow.value = row
  showDetails.value = true
}

function formatTime(isoStr) {
  if (!isoStr) return "-"
  return isoStr.replace("T", " ").split(".")[0]
}

function getMethodTagType(method) {
  const colors = {
    GET: "info",
    POST: "success",
    PUT: "warning",
    PATCH: "warning",
    DELETE: "error",
  }
  return colors[method] || "default"
}

function getStatusTagType(status) {
  if (status >= 500) return "error"
  if (status >= 400) return "warning"
  return "success"
}

function formatJson(val) {
  if (!val) return ""
  try {
    const obj = JSON.parse(val)
    return JSON.stringify(obj, null, 2)
  } catch {
    return val
  }
}

onMounted(() => {
  loadRows()
})
</script>

<style scoped>
.admin-page {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.toolbar-search {
  flex: 2;
  min-width: 220px;
  max-width: 320px;
}

.toolbar-select {
  flex: 1;
  min-width: 140px;
  max-width: 180px;
}

.toolbar-btn {
  flex-shrink: 0;
}

.search-icon {
  width: 12px;
  height: 12px;
  border: 2px solid var(--c-text-faint);
  border-radius: 50%;
  position: relative;
  display: inline-block;
}

.search-icon::after {
  content: "";
  position: absolute;
  width: 6px;
  height: 2px;
  right: -6px;
  bottom: -4px;
  border-radius: 2px;
  background: var(--c-text-faint);
  transform: rotate(45deg);
}

.audit-data-shell {
  padding: var(--sp-3) var(--sp-4) var(--sp-4);
  min-height: 360px;
  display: flex;
  flex-direction: column;
}

.audit-data-shell :deep(.n-data-table) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.audit-data-shell :deep(.n-data-table-wrapper) {
  flex: 1;
  min-height: 240px;
}

.audit-data-shell :deep(.n-pagination) {
  margin-top: var(--sp-3);
  padding: var(--sp-1) var(--sp-1) var(--sp-1);
  justify-content: flex-end;
}

.code-path {
  font-family: monospace;
  font-size: 13px;
  background-color: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  word-break: break-all;
}

.ua-text {
  font-size: 12px;
  color: #6b7280;
  word-break: break-all;
}

.json-block {
  margin: 0;
  font-family: monospace;
  font-size: 12px;
  max-height: 250px;
  overflow-y: auto;
  background-color: #f9fafb;
  border: 1px solid #e5e7eb;
  padding: 8px;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-all;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.text-muted {
  color: #9ca3af;
}

.font-mono {
  font-family: monospace;
}
</style>
