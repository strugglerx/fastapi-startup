<template>
  <div class="admin-page">
    <AdminPageHeader title="账号管理" subtitle="后台登录账号的创建、编辑、重置密码与删除">
      <template #actions>
        <n-button v-auth="'system:admin:create'" type="primary" size="small" @click="openCreate">新建账号</n-button>
      </template>
    </AdminPageHeader>

    <div class="admin-toolbar">
      <n-input 
        v-model:value="filters.keyword" 
        clearable 
        placeholder="按邮箱或用户名搜索…" 
        @input="debouncedLoadRows"
        class="toolbar-search"
      >
        <template #prefix><span class="search-icon" /></template>
      </n-input>
      <n-select
        v-model:value="filters.role"
        clearable
        placeholder="选择角色"
        :options="allRoleOptions"
        @update:value="reloadFirstPage"
        class="toolbar-select"
      />
      <n-select
        v-model:value="filters.is_active"
        clearable
        placeholder="启用状态"
        :options="statusOptions"
        @update:value="reloadFirstPage"
        class="toolbar-select"
      />
      <n-button @click="resetFilters" class="toolbar-btn">重置</n-button>
    </div>

    <div class="admin-data-shell account-data-shell">
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

    <n-modal v-model:show="showCreate" preset="card" title="新建账号" class="admin-account-modal">
      <n-form ref="createFormRef" :model="createForm" :rules="createRules" label-placement="top">
        <n-form-item label="用户名" path="username">
          <n-input v-model:value="createForm.username" placeholder="至少 3 个字符" />
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="createForm.email" placeholder="admin@example.com" />
        </n-form-item>
        <n-form-item label="角色" path="role">
          <n-select v-model:value="createForm.role" :options="enabledRoleOptions" />
        </n-form-item>
        <n-form-item label="初始密码" path="password">
          <n-input v-model:value="createForm.password" type="password" show-password-on="click" placeholder="至少 6 位" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-actions">
          <n-button @click="showCreate = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="submitCreate">创建</n-button>
        </div>
      </template>
    </n-modal>

    <n-modal v-model:show="showEdit" preset="card" title="编辑账号" class="admin-account-modal">
      <n-form ref="editFormRef" :model="editForm" :rules="editRules" label-placement="top">
        <n-form-item label="用户名" path="username">
          <n-input v-model:value="editForm.username" placeholder="至少 3 个字符" />
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="editForm.email" placeholder="admin@example.com" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-actions">
          <n-button @click="showEdit = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="submitEdit">保存</n-button>
        </div>
      </template>
    </n-modal>

    <n-modal v-model:show="showReset" preset="card" title="重置密码" class="admin-account-modal">
      <n-form ref="resetFormRef" :model="resetForm" :rules="resetRules" label-placement="top">
        <n-form-item label="新密码" path="password">
          <n-input v-model:value="resetForm.password" type="password" show-password-on="click" placeholder="至少 6 位" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-actions">
          <n-button @click="showReset = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="submitReset">确认重置</n-button>
        </div>
      </template>
    </n-modal>

    <n-modal v-model:show="showRole" preset="card" title="修改角色" class="admin-account-modal">
      <n-form :model="roleForm" label-placement="top">
        <n-form-item label="账号">
          <n-input :value="roleTargetName" readonly />
        </n-form-item>
        <n-form-item label="角色">
          <n-select v-model:value="roleForm.role" :options="roleSelectOptions" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-actions">
          <n-button @click="showRole = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="submitRole">保存</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { computed, h, onMounted, reactive, ref } from "vue"
import {
  NButton,
  NDataTable,
  NForm,
  NFormItem,
  NInput,
  NModal,
  NSelect,
  NSpace,
  NSwitch,
  NTag,
  useDialog,
  useMessage,
} from "naive-ui"
import { fetchRoles } from "../../../api/role.js"
import { request } from "../../../api/fetch.js"
import { hasPermission } from "../../../shared/auth.js"
import AdminPageHeader from "../../../components/AdminPageHeader.vue"

defineOptions({ name: "SystemAdmin" })

const ADMIN_ENDPOINT = "/api/v1/admins"

const message = useMessage()
const dialog = useDialog()
const currentUser = readCurrentUser()
const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const roleRows = ref([])
let searchTimer = null

const filters = reactive({ keyword: "", role: null, is_active: null })
const pagination = reactive({
  page: 1,
  pageSize: 20,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
})

const showCreate = ref(false)
const showEdit = ref(false)
const showReset = ref(false)
const showRole = ref(false)
const createFormRef = ref(null)
const editFormRef = ref(null)
const resetFormRef = ref(null)
const editTarget = ref(null)
const resetTarget = ref(null)
const roleTarget = ref(null)

const createForm = reactive({ username: "", email: "", role: "admin", password: "" })
const editForm = reactive({ username: "", email: "" })
const resetForm = reactive({ password: "" })
const roleForm = reactive({ role: "member" })

const statusOptions = [
  { label: "启用", value: true },
  { label: "禁用", value: false },
]

const allRoleOptions = computed(() => roleRows.value.map((role) => ({ label: role.name, value: role.code })))
const enabledRoleOptions = computed(() => roleRows.value
  .filter((role) => role.enabled)
  .map((role) => ({ label: role.name, value: role.code })))
const roleNameMap = computed(() => new Map(roleRows.value.map((role) => [role.code, role.name])))
const roleSelectOptions = computed(() => {
  const options = enabledRoleOptions.value
  if (!roleTarget.value?.fixed) return options
  return options.map((option) => ({ ...option, disabled: option.value !== "admin" }))
})

const roleTargetName = computed(() => {
  const row = roleTarget.value
  return row ? (row.email || row.username || String(row.id)) : ""
})

const createRules = {
  username: { required: true, min: 3, message: "用户名至少 3 个字符", trigger: ["blur", "input"] },
  email: { type: "email", message: "请输入有效邮箱", trigger: ["blur", "input"] },
  role: { required: true, message: "请选择角色", trigger: "change" },
  password: { required: true, min: 6, message: "密码至少 6 位", trigger: ["blur", "input"] },
}

const editRules = {
  username: { required: true, min: 3, message: "用户名至少 3 个字符", trigger: ["blur", "input"] },
  email: { type: "email", message: "请输入有效邮箱", trigger: ["blur", "input"] },
}

const resetRules = {
  password: { required: true, min: 6, message: "密码至少 6 位", trigger: ["blur", "input"] },
}

const columns = computed(() => [
  { title: "用户名", key: "username", minWidth: 150, render: (row) => row.username || "—" },
  { title: "邮箱", key: "email", minWidth: 190, render: (row) => row.email || "—" },
  {
    title: "角色",
    key: "role",
    width: 140,
    render: (row) => h(NTag, { size: "small", type: row.role === "admin" ? "info" : "default" }, {
      default: () => roleNameMap.value.get(row.role) || row.role || "—",
    }),
  },
  {
    title: "状态",
    key: "is_active",
    width: 120,
    render: (row) => h(NSwitch, {
      value: Boolean(row.is_active),
      disabled: isSelf(row) || Boolean(row.fixed) || !hasPermission("system:admin:update"),
      "onUpdate:value": (value) => updateActive(row, value),
    }),
  },
  { title: "最后登录", key: "last_login_at", minWidth: 170, render: (row) => formatTime(row.last_login_at) },
  { title: "创建时间", key: "created_at", minWidth: 170, render: (row) => formatTime(row.created_at) },
  {
    title: "操作",
    key: "actions",
    width: 310,
    render: (row) => {
      const btns = []
      if (hasPermission("system:admin:update")) {
        btns.push(h(NButton, { size: "small", quaternary: true, onClick: () => openEdit(row) }, { default: () => "编辑" }))
        btns.push(h(NButton, {
          size: "small",
          quaternary: true,
          disabled: isSelf(row),
          onClick: () => openRole(row),
        }, { default: () => "改角色" }))
      }
      if (hasPermission("system:admin:password")) {
        btns.push(h(NButton, { size: "small", quaternary: true, onClick: () => openReset(row) }, { default: () => "重置密码" }))
      }
      if (hasPermission("system:admin:delete")) {
        btns.push(h(NButton, {
          size: "small",
          quaternary: true,
          type: "error",
          disabled: isSelf(row) || Boolean(row.fixed),
          onClick: () => confirmDelete(row),
        }, { default: () => "删除" }))
      }
      return h(NSpace, { size: 6 }, { default: () => btns })
    }
  },
])

onMounted(async () => {
  await loadRoles()
  await loadRows()
})

function readCurrentUser() {
  try {
    return JSON.parse(localStorage.getItem("smartai_admin_user") || "null") || {}
  } catch {
    return {}
  }
}

function formatTime(value) {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString("zh-CN", { hour12: false })
}

async function loadRoles() {
  roleRows.value = await fetchRoles()
}

function buildParams() {
  const params = { page: pagination.page, size: pagination.pageSize }
  if (filters.keyword?.trim()) params.keyword = filters.keyword.trim()
  if (filters.role) params.role = filters.role
  if (filters.is_active !== null && filters.is_active !== undefined) params.is_active = filters.is_active
  return params
}

async function loadRows() {
  loading.value = true
  try {
    const data = await request.get(ADMIN_ENDPOINT, buildParams())
    rows.value = data.items ?? data.list ?? []
    pagination.itemCount = data.total ?? rows.value.length
  } catch {
    // 错误由 fetch.js 拦截器展示
  } finally {
    loading.value = false
  }
}

function debouncedLoadRows() {
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(reloadFirstPage, 300)
}

function reloadFirstPage() {
  pagination.page = 1
  loadRows()
}

function resetFilters() {
  filters.keyword = ""
  filters.role = null
  filters.is_active = null
  reloadFirstPage()
}

function onPageChange(page) {
  pagination.page = page
  loadRows()
}

function onPageSizeChange(pageSize) {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadRows()
}

function openCreate() {
  createForm.username = ""
  createForm.email = ""
  createForm.role = enabledRoleOptions.value[0]?.value || "admin"
  createForm.password = ""
  showCreate.value = true
}

function openEdit(row) {
  editTarget.value = row
  editForm.username = row.username || ""
  editForm.email = row.email || ""
  showEdit.value = true
}

function openReset(row) {
  resetTarget.value = row
  resetForm.password = ""
  showReset.value = true
}

function isSelf(row) {
  return String(row.id) === String(currentUser.id)
}

function openRole(row) {
  if (isSelf(row)) return
  roleTarget.value = row
  roleForm.role = row.fixed ? "admin" : (row.role || enabledRoleOptions.value[0]?.value || "member")
  showRole.value = true
}

async function submitCreate() {
  try {
    await createFormRef.value?.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    await request.post(ADMIN_ENDPOINT, { ...createForm })
    message.success("账号已创建")
    showCreate.value = false
    loadRows()
  } catch {
    // 错误由 fetch.js 拦截器展示
  } finally {
    saving.value = false
  }
}

async function submitEdit() {
  try {
    await editFormRef.value?.validate()
  } catch {
    return
  }
  if (!editTarget.value) return
  saving.value = true
  try {
    await request.put(`${ADMIN_ENDPOINT}/${editTarget.value.id}`, {
      username: editForm.username,
      email: editForm.email,
    })
    message.success("账号已保存")
    showEdit.value = false
    loadRows()
  } catch {
    // 错误由 fetch.js 拦截器展示
  } finally {
    saving.value = false
  }
}

async function submitReset() {
  try {
    await resetFormRef.value?.validate()
  } catch {
    return
  }
  if (!resetTarget.value) return
  saving.value = true
  try {
    await request.post(`${ADMIN_ENDPOINT}/${resetTarget.value.id}/reset-password`, {
      new_password: resetForm.password,
    })
    message.success("密码已重置")
    showReset.value = false
  } catch {
    // 错误由 fetch.js 拦截器展示
  } finally {
    saving.value = false
  }
}

async function submitRole() {
  if (!roleTarget.value) return
  if (roleTarget.value.fixed && roleForm.role !== "admin") {
    message.warning("种子管理员不可降级")
    return
  }
  saving.value = true
  try {
    await request.put(`${ADMIN_ENDPOINT}/${roleTarget.value.id}`, { role: roleForm.role })
    message.success("角色已更新")
    showRole.value = false
    loadRows()
  } catch {
    // 错误由 fetch.js 拦截器展示
  } finally {
    saving.value = false
  }
}

async function updateActive(row, value) {
  try {
    await request.put(`${ADMIN_ENDPOINT}/${row.id}`, { is_active: value })
    row.is_active = value
    message.success(value ? "账号已启用" : "账号已禁用")
  } catch {
    loadRows()
  }
}

function confirmDelete(row) {
  dialog.warning({
    title: "删除账号",
    content: "删除后该账号将无法登录，确认？",
    positiveText: "删除",
    negativeText: "取消",
    onPositiveClick: () => softDelete(row),
  })
}

async function softDelete(row) {
  try {
    await request.delete(`${ADMIN_ENDPOINT}/${row.id}`)
    message.success("账号已删除")
    loadRows()
  } catch {
    // 错误由 fetch.js 拦截器展示
  }
}
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

.account-data-shell {
  padding: var(--sp-3) var(--sp-4) var(--sp-4);
  min-height: 360px;
  display: flex;
  flex-direction: column;
}

.account-data-shell :deep(.n-data-table) {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.account-data-shell :deep(.n-data-table-wrapper) {
  flex: 1;
  min-height: 240px;
}

.account-data-shell :deep(.n-pagination) {
  margin-top: var(--sp-3);
  padding: var(--sp-1) var(--sp-1) var(--sp-1);
  justify-content: flex-end;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-2);
}

:global(.admin-account-modal) {
  width: min(520px, calc(100vw - 32px));
}
</style>
