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

    <!-- 文件预览 Modal -->
    <n-modal
      v-model:show="showPreview"
      preset="card"
      :title="`文件预览 - ${previewFile.filename}`"
      style="width: 800px; max-width: 95vw;"
      class="file-preview-modal"
      @after-leave="handlePreviewClose"
    >
      <div class="preview-content-wrapper">
        <n-spin :show="loadingText">
          <!-- 1. 图片预览 -->
          <div v-if="previewType === 'image'" class="preview-image-box">
            <n-image :src="previewFile.url" object-fit="contain" style="max-height: 60vh; width: 100%; display: block;" />
          </div>

          <!-- 2. PDF 预览 -->
          <div v-else-if="previewType === 'pdf'" class="preview-iframe-box">
            <iframe :src="previewFile.url" class="preview-iframe"></iframe>
          </div>

          <!-- 3. 视频预览 -->
          <div v-else-if="previewType === 'video'" class="preview-media-box">
            <video :src="previewFile.url" controls class="preview-video" autoplay></video>
          </div>

          <!-- 4. 音频预览 -->
          <div v-else-if="previewType === 'audio'" class="preview-media-box audio-preview">
            <div class="audio-card">
              <div class="audio-icon">🎵</div>
              <audio :src="previewFile.url" controls class="preview-audio" autoplay></audio>
            </div>
          </div>

          <!-- 5. 文本预览 -->
          <div v-else-if="previewType === 'text'" class="preview-text-box">
            <pre class="preview-pre">{{ textContent }}</pre>
          </div>

          <!-- 6. Office 预览 -->
          <div v-else-if="previewType === 'office'" class="preview-office-box">
            <div class="office-fallback-card">
              <div class="office-icon" :class="officeClass">📄</div>
              <div class="office-filename">{{ previewFile.filename }}</div>
              <div class="office-size">大小: {{ formatBytes(previewFile.file_size) }}</div>
              <n-space justify="center" style="margin-top: 16px;">
                <n-button type="primary" @click="downloadFile(previewFile)">下载并查看</n-button>
                <n-button secondary @click="toggleOfficeOnline">
                  {{ showOfficeOnline ? '关闭网页预览' : '使用 Office Online 预览' }}
                </n-button>
              </n-space>
              <div v-if="showOfficeOnline" class="office-online-container">
                <iframe :src="officeOnlineUrl" class="preview-iframe"></iframe>
              </div>
            </div>
          </div>

          <!-- 7. 其他不支持预览的文件 -->
          <div v-else class="preview-unsupported-box">
            <div class="unsupported-card">
              <div class="unsupported-icon">📥</div>
              <div class="unsupported-filename">{{ previewFile.filename }}</div>
              <div class="unsupported-desc">该文件类型不支持在线预览</div>
              <n-button type="primary" style="margin-top: 16px;" @click="downloadFile(previewFile)">下载文件</n-button>
            </div>
          </div>
        </n-spin>
      </div>
    </n-modal>
  </div>
</template>

<script setup>
import { computed, h, onMounted, reactive, ref } from "vue"
import { NButton, NDataTable, NImage, NInput, NSpace, NTag, NUpload, NSpin, useDialog, useMessage } from "naive-ui"
import AdminPageHeader from "../../../components/AdminPageHeader.vue"
import { fileApi } from "../../../api/file.js"
import { getToken } from "../../../api/base.js"
import { notifySuccess, notifyError } from "../../../api/feedback.js"

defineOptions({ name: "SystemFileList" })

const message = useMessage()
const dialog = useDialog()
const loading = ref(false)
const rows = ref([])

// 预览相关状态
const showPreview = ref(false)
const previewFile = ref({})
const showOfficeOnline = ref(false)
const textContent = ref("")
const loadingText = ref(false)

const previewType = computed(() => {
  const file = previewFile.value
  if (!file || !file.filename) return "download"
  
  const ext = file.filename.split(".").pop().toLowerCase()
  const mime = file.mime_type || ""
  
  if (mime.startsWith("image/") || ["jpg", "jpeg", "png", "gif", "svg", "webp", "bmp"].includes(ext)) {
    return "image"
  }
  if (mime === "application/pdf" || ext === "pdf") {
    return "pdf"
  }
  if (mime.startsWith("video/") || ["mp4", "webm", "ogg", "mkv"].includes(ext)) {
    return "video"
  }
  if (mime.startsWith("audio/") || ["mp3", "wav", "ogg", "m4a", "wma"].includes(ext)) {
    return "audio"
  }
  if (mime.startsWith("text/") || ["txt", "json", "md", "js", "html", "css", "xml", "py", "sh"].includes(ext)) {
    return "text"
  }
  if (["doc", "docx", "xls", "xlsx", "ppt", "pptx"].includes(ext)) {
    return "office"
  }
  return "download"
})

const officeClass = computed(() => {
  const file = previewFile.value
  if (!file || !file.filename) return ""
  const ext = file.filename.split(".").pop().toLowerCase()
  if (["doc", "docx"].includes(ext)) return "word"
  if (["xls", "xlsx"].includes(ext)) return "excel"
  if (["ppt", "pptx"].includes(ext)) return "ppt"
  return ""
})

const officeOnlineUrl = computed(() => {
  const file = previewFile.value
  if (!file || !file.url) return ""
  let fileUrl = file.url
  if (fileUrl.startsWith("/")) {
    fileUrl = window.location.origin + fileUrl
  }
  return `https://view.officeapps.live.com/op/view.aspx?src=${encodeURIComponent(fileUrl)}`
})

function toggleOfficeOnline() {
  showOfficeOnline.value = !showOfficeOnline.value
}

async function fetchTextContent(url) {
  loadingText.value = true
  textContent.value = ""
  try {
    const response = await fetch(url)
    if (response.ok) {
      textContent.value = await response.text()
    } else {
      textContent.value = "无法加载文本内容"
    }
  } catch (e) {
    textContent.value = `加载文本失败: ${e.message}`
  } finally {
    loadingText.value = false
  }
}

function handlePreview(row) {
  previewFile.value = row
  showOfficeOnline.value = false
  showPreview.value = true
  
  if (previewType.value === "text") {
    fetchTextContent(row.url)
  }
}

function handlePreviewClose() {
  previewFile.value = {}
  textContent.value = ""
  showOfficeOnline.value = false
}

function downloadFile(file) {
  const link = document.createElement("a")
  link.href = file.url
  link.download = file.filename
  link.target = "_blank"
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

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
    title: "缩略图",
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
    width: 150,
    render(row) {
      return h(NSpace, { size: 6 }, {
        default: () => [
          h(NButton, {
            type: "primary",
            size: "small",
            quaternary: true,
            onClick: () => handlePreview(row)
          }, { default: () => "预览" }),
          h(NButton, {
            type: "error",
            size: "small",
            quaternary: true,
            onClick: () => confirmDelete(row)
          }, { default: () => "删除" })
        ]
      })
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

/* 预览相关样式 */
.preview-content-wrapper {
  min-height: 150px;
  display: flex;
  flex-direction: column;
}

.preview-image-box {
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f8fafc;
  border-radius: 6px;
  padding: 12px;
}

.preview-iframe-box {
  height: 60vh;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  overflow: hidden;
}

.preview-iframe {
  width: 100%;
  height: 100%;
  border: none;
}

.preview-media-box {
  display: flex;
  justify-content: center;
  align-items: center;
  background: #0f172a;
  border-radius: 6px;
  padding: 12px;
}

.preview-video {
  max-width: 100%;
  max-height: 60vh;
  outline: none;
}

.audio-preview {
  background: #f1f5f9;
  padding: 32px;
}

.audio-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.audio-icon {
  font-size: 48px;
}

.preview-audio {
  width: 320px;
}

.preview-text-box {
  max-height: 60vh;
  overflow-y: auto;
  background: #0f172a;
  color: #e2e8f0;
  padding: 16px;
  border-radius: 6px;
  font-family: monospace;
}

.preview-pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
  font-size: 13px;
  line-height: 1.6;
}

.preview-office-box,
.preview-unsupported-box {
  padding: 24px;
}

.office-fallback-card,
.unsupported-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 24px;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
}

.office-icon,
.unsupported-icon {
  font-size: 64px;
  margin-bottom: 12px;
}

.office-filename,
.unsupported-filename {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 6px;
  word-break: break-all;
}

.office-size,
.unsupported-desc {
  font-size: 13px;
  color: #64748b;
}

.office-online-container {
  width: 100%;
  height: 50vh;
  margin-top: 24px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  overflow: hidden;
}

:global(.file-preview-modal) {
  width: min(800px, calc(100vw - 32px));
}
</style>
