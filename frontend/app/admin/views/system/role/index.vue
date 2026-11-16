<template>
  <div class="admin-page">
    <AdminPageHeader title="角色管理" subtitle="定义不同的操作角色，并为其配置系统页面的访问和操作权限。">
      <template #actions>
        <n-button type="primary" size="small" @click="openCreate">新建角色</n-button>
      </template>
    </AdminPageHeader>

    <section class="role-layout">
      <RoleListPane
        :roles="roles"
        :selected-role="selectedRole"
        :loading="rolesLoading"
        @select="selectRole"
        @edit="openEdit"
        @delete="confirmDelete"
      />
      <RoleGrantPane
        v-model:checked-keys="checkedKeys"
        :selected-role="selectedRole"
        :menu-tree="menuTree"
        :all-menu-keys="allMenuKeys"
        :loading="grantsLoading"
        :saving="saving"
        @save="saveGrants"
      />
    </section>

    <n-modal v-model:show="showCreate" preset="card" title="新建角色" class="role-modal">
      <n-form ref="createFormRef" :model="createForm" :rules="createRules" label-placement="top">
        <n-form-item label="Code" path="code">
          <n-input v-model:value="createForm.code" placeholder="auditor" />
        </n-form-item>
        <n-form-item label="名称" path="name">
          <n-input v-model:value="createForm.name" placeholder="审核员" />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input v-model:value="createForm.description" type="textarea" />
        </n-form-item>
        <n-form-item label="排序" path="sort">
          <n-input-number v-model:value="createForm.sort" :min="0" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-actions">
          <n-button @click="showCreate = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="submitCreate">创建</n-button>
        </div>
      </template>
    </n-modal>

    <n-modal v-model:show="showEdit" preset="card" title="编辑角色" class="role-modal">
      <n-form ref="editFormRef" :model="editForm" :rules="editRules" label-placement="top">
        <n-form-item label="Code">
          <n-input v-model:value="editForm.code" readonly />
        </n-form-item>
        <n-form-item label="名称" path="name">
          <n-input v-model:value="editForm.name" />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input v-model:value="editForm.description" type="textarea" />
        </n-form-item>
        <n-form-item label="启用">
          <n-switch v-model:value="editForm.enabled" :disabled="editTarget?.builtin" />
        </n-form-item>
        <n-form-item label="排序" path="sort">
          <n-input-number v-model:value="editForm.sort" :min="0" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-actions">
          <n-button @click="showEdit = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="submitEdit">保存</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue"
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NModal,
  NSwitch,
  useDialog,
  useMessage,
} from "naive-ui"
import { createRole, deleteRole, fetchRoles, updateRole } from "../../../api/role.js"
import { fetchMenuList, fetchRoleGrants, setRoleGrants } from "../../../api/menu.js"
import AdminPageHeader from "../../../components/AdminPageHeader.vue"
import RoleGrantPane from "./RoleGrantPane.vue"
import RoleListPane from "./RoleListPane.vue"

defineOptions({ name: "SystemRole" })

const message = useMessage()
const dialog = useDialog()
const roles = ref([])
const menus = ref([])
const selectedRole = ref(null)
const checkedKeys = ref([])
const rolesLoading = ref(false)
const grantsLoading = ref(false)
const saving = ref(false)

const showCreate = ref(false)
const showEdit = ref(false)
const createFormRef = ref(null)
const editFormRef = ref(null)
const editTarget = ref(null)

const createForm = reactive({ code: "", name: "", description: "", sort: 0 })
const editForm = reactive({ code: "", name: "", description: "", enabled: true, sort: 0 })

const codePattern = /^[a-z][a-z0-9_-]*$/
const createRules = {
  code: {
    required: true,
    validator: (_rule, value) => codePattern.test(value || ""),
    message: "小写字母开头，仅支持小写字母、数字、_、-",
    trigger: ["blur", "input"],
  },
  name: { required: true, message: "请输入角色名称", trigger: ["blur", "input"] },
}
const editRules = {
  name: { required: true, message: "请输入角色名称", trigger: ["blur", "input"] },
}

const allMenuKeys = computed(() => menus.value.map((item) => item.menuKey))
const menuTree = computed(() => buildTree(menus.value, selectedRole.value?.code === "admin"))

onMounted(async () => {
  await Promise.all([loadRoles(), loadMenus()])
})

async function loadRoles() {
  rolesLoading.value = true
  try {
    roles.value = await fetchRoles()
    if (!selectedRole.value && roles.value.length) selectRole(roles.value[0])
    if (selectedRole.value) {
      selectedRole.value = roles.value.find((item) => item.code === selectedRole.value.code) || roles.value[0] || null
    }
  } finally {
    rolesLoading.value = false
  }
}

async function loadMenus() {
  menus.value = await fetchMenuList()
}

async function selectRole(role) {
  selectedRole.value = role
  if (!role || role.code === "admin") {
    checkedKeys.value = []
    return
  }
  await loadGrants(role.code)
}

async function loadGrants(role) {
  grantsLoading.value = true
  try {
    const data = await fetchRoleGrants(role)
    checkedKeys.value = data.menuKeys || []
  } catch (error) {
    message.error(error?.message || "加载角色授权失败")
  } finally {
    grantsLoading.value = false
  }
}

function buildTree(items, adminMode) {
  const map = new Map()
  items.forEach((item) => {
    map.set(item.menuKey, {
      key: item.menuKey,
      label: item.title,
      disabled: adminMode,
      raw: item,
      children: [],
    })
  })
  const roots = []
  map.forEach((node) => {
    const parentKey = node.raw.parentKey
    if (parentKey && map.has(parentKey)) map.get(parentKey).children.push(node)
    else roots.push(node)
  })

  // 递归处理：没有子节点的节点，移除 children 属性以隐藏三角展开图标
  const cleanRec = (nodes) => {
    nodes.forEach((node) => {
      if (!node.children || node.children.length === 0) {
        delete node.children
      } else {
        cleanRec(node.children)
      }
    })
  }
  cleanRec(roots)

  const sortRec = (nodes) => {
    nodes.sort((a, b) => (a.raw.sort || 0) - (b.raw.sort || 0))
    nodes.forEach((node) => {
      if (node.children) sortRec(node.children)
    })
  }
  sortRec(roots)
  return roots
}

function openCreate() {
  Object.assign(createForm, { code: "", name: "", description: "", sort: 0 })
  showCreate.value = true
}

function openEdit(role) {
  editTarget.value = role
  Object.assign(editForm, {
    code: role.code,
    name: role.name,
    description: role.description || "",
    enabled: Boolean(role.enabled),
    sort: role.sort || 0,
  })
  showEdit.value = true
}

async function submitCreate() {
  try {
    await createFormRef.value?.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    const role = await createRole({ ...createForm })
    message.success("角色已创建")
    showCreate.value = false
    await loadRoles()
    selectRole(role)
  } catch (error) {
    message.error(error?.response?.data?.msg || error?.message || "创建角色失败")
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
    await updateRole(editTarget.value.id, {
      name: editForm.name,
      description: editForm.description,
      enabled: editForm.enabled,
      sort: editForm.sort,
    })
    message.success("角色已保存")
    showEdit.value = false
    await loadRoles()
  } catch (error) {
    message.error(error?.response?.data?.msg || error?.message || "保存角色失败")
  } finally {
    saving.value = false
  }
}

function confirmDelete(role) {
  dialog.warning({
    title: "删除角色",
    content: `删除后 ${role.name} 的菜单授权会被清理，确认？`,
    positiveText: "删除",
    negativeText: "取消",
    onPositiveClick: () => removeRole(role),
  })
}

async function removeRole(role) {
  saving.value = true
  try {
    await deleteRole(role.id)
    message.success("角色已删除")
    if (selectedRole.value?.id === role.id) selectedRole.value = null
    await loadRoles()
  } catch (error) {
    message.error(error?.response?.data?.msg || error?.message || "删除角色失败")
  } finally {
    saving.value = false
  }
}

async function saveGrants() {
  if (!selectedRole.value || selectedRole.value.code === "admin") return
  saving.value = true
  try {
    const data = await setRoleGrants(selectedRole.value.code, checkedKeys.value)
    checkedKeys.value = data.menuKeys || checkedKeys.value
    message.success("菜单授权已保存")
  } catch (error) {
    message.error(error?.response?.data?.msg || error?.message || "保存菜单授权失败")
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.admin-page {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.role-layout {
  display: grid;
  grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
  gap: var(--sp-4);
  min-height: 560px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-2);
}

:global(.role-modal) {
  width: min(520px, calc(100vw - 32px));
}

@media (max-width: 900px) {
  .role-layout {
    grid-template-columns: 1fr;
  }
}
</style>
