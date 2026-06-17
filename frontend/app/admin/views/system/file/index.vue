<template>
  <div class="admin-page">
    <AdminPageHeader title="文件管理" subtitle="上传并管理系统静态文件，上传时将自动根据内容哈希进行物理去重">
      <template #actions>
        <n-upload
          action="/api/v1/files/upload"
          :headers="uploadHeaders"
          :show-file-list="false"
          @finish="handleUploadFinish"
          @error="handleUploadError"
          class="file-uploader"
        >
          <n-button type="primary" size="small">上传文件</n-button>
        </n-upload>
      </template>
    </AdminPageHeader>

    <div class="admin-toolbar">
      <n-input
        v-model:value="filters.filename"
        clearable
        placeholder="输入文件名搜索…"
        @input="debouncedLoadRows"
        class="toolbar-search"
      >
        <template #prefix><span class="search-icon" /></template>
      </n-input>
      <n-button @click="resetFilters" class="toolbar-btn">重置</n-button>
    </div>

    <div class="admin-data-shell file-data-shell">
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
  </div>
</template>

<script setup>
import { computed, h, onMounted, reactive, ref } from "vue"
import { NButton, NDataTable, NImage, NInput, NSpace, NTag, NUpload, useDialog, useMessage } from "naive-ui"
import AdminPageHeader from "../../../components/AdminPageHeader.vue"
import { fileApi } from "../../../api/file.js"
import { getToken } from "../../../api/base.js"
import { notifySuccess, notifyError } from "../../../api/feedback.js"

defineOptions({ name: "SystemFileList" })

const message = useMessage()
const dialog = useDialog()
const loading = ref(false)
const rows = ref([])

const uploadHeaders = computed(() => {
  const token = getToken()
  return token ? { Token: token } : {}
})

const filters = reactive({
  filename: "",
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
})

const columns = [
  {
    title: "ID",
    key: "id",
    width: 80,
  },
  {
    title: "预览",
    key: "preview",
    width: 90,
    render(row) {
      if (row.mime_type && row.mime_type.startsWith("image/")) {
        return h(NImage, {
          src: row.url,
          width: 44,
          height: 44,
          showToolbarTooltip: true,
          style: "border-radius: 4px; border: 1px solid rgba(226, 232, 240, 0.8); object-fit: cover; display: block;"
        })
      }
      return h("div", {
        style: "width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; background: #f3f4f6; border-radius: 4px; color: #6b7280; font-size: 11px; font-weight: 600; text-transform: uppercase;"
      }, row.mime_type ? row.mime_type.split("/")[1] || "FILE" : "FILE")
    }
  },
  {
    title: "文件名",
    key: "filename",
    render(row) {
      return h("a", {
        href: row.url,
        target: "_blank",
        class: "file-link-btn"
      }, row.filename)
    }
  },
  {
    title: "文件大小",
    key: "file_size",
    width: 120,
    render(row) {
      return formatBytes(row.file_size)
    }
  },
  {
    title: "MIME 类型",
    key: "mime_type",
    width: 160,
    render(row) {
      return h(NTag, { size: "small", bordered: false, type: "info" }, { default: () => row.mime_type || "unknown" })
    }
  },
  {
    title: "MD5 哈希值",
    key: "hash_md5",
    width: 280,
    render(row) {
      return h("span", { class: "font-mono" }, row.hash_md5 || "-")
    }
  },
  {
    title: "上传时间",
    key: "created_at",
    width: 170,
    render(row) {
      return formatTime(row.created_at)
    }
  },
  {
    title: "操作",
    key: "actions",
    width: 100,
    render(row) {
      return h(NButton, {
        type: "error",
        size: "small",
        quaternary: true,
        onClick: () => confirmDelete(row)
      }, { default: () => "删除" })
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
  filters.filename = ""
  reloadFirstPage()
}

async function loadRows() {
  loading.value = true
  try {
    const res = await fileApi.list({
      page: pagination.page,
      size: pagination.pageSize,
      filename: filters.filename || undefined,
    })
    rows.value = res.items || []
    pagination.itemCount = res.total || 0
  } catch (err) {
    notifyError(err.message || "加载文件列表失败")
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

function handleUploadFinish({ file, event }) {
  let responseData
  try {
    const rawResponse = event.target.response
    responseData = JSON.parse(rawResponse)
  } catch (e) {
    responseData = {}
  }
  
  // 提取真正的业务数据，注意统一响应格式包装
  const fileInfo = responseData.data || responseData
  
  if (fileInfo && fileInfo.id) {
    if (fileInfo.duplicate) {
      message.info(`文件秒传成功：已检测到同内容物理文件并自动关联`)
    } else {
      message.success(`文件上传成功`)
    }
    loadRows()
  } else {
    notifyError(responseData.msg || "上传失败")
  }
}

function handleUploadError() {
  notifyError("网络或接口错误，上传失败")
}

function confirmDelete(row) {
  const d = dialog.warning({
    title: "确认删除",
    content: `您确定要删除文件 "${row.filename}" 吗？物理文件在没有其他关联记录时将被同步删除。`,
    positiveText: "删除",
    negativeText: "取消",
    onPositiveClick: async () => {
      d.loading = true
      try {
        await fileApi.delete(row.id)
        message.success("删除成功")
        loadRows()
      } catch (err) {
        notifyError(err.message || "删除失败")
      } finally {
        d.loading = false
      }
    }
  })
}

function formatBytes(bytes) {
  if (bytes === 0) return "0 B"
  const k = 1024
  const sizes = ["B", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
}

function formatTime(isoStr) {
  if (!isoStr) return "-"
  return isoStr.replace("T", " ").split(".")[0]
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

.file-data-shell {
  padding: var(--sp-3) var(--sp-4) var(--sp-4);
  min-height: 360px;
  display: flex;
  flex-direction: column;
}

.file-data-shell :deep(.n-data-table) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.file-data-shell :deep(.n-data-table-wrapper) {
  flex: 1;
  min-height: 240px;
}

.file-data-shell :deep(.n-pagination) {
  margin-top: var(--sp-3);
  padding: var(--sp-1) var(--sp-1) var(--sp-1);
  justify-content: flex-end;
}

.file-link-btn {
  color: var(--c-primary);
  text-decoration: none;
  font-weight: 500;
  transition: color 0.15s ease;
}

.file-link-btn:hover {
  color: var(--c-primary-hover);
  text-decoration: underline;
}

.font-mono {
  font-family: monospace;
  font-size: 12px;
  color: #6b7280;
}

.file-uploader {
  display: inline-block;
}
</style>
