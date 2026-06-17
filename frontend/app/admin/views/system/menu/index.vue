<template>
  <div class="admin-page">
    <AdminPageHeader title="菜单管理" subtitle="维护系统菜单层级、图标路由及状态配置">
      <template #actions>
        <n-button type="primary" size="small" @click="openCreateRoot">新建根菜单</n-button>
      </template>
    </AdminPageHeader>

    <section class="menu-layout">
      <!-- 左侧菜单树 -->
      <aside class="menu-tree-pane">
        <div class="pane-header">
          <span>菜单层级树</span>
        </div>
        <div class="tree-container">
          <n-spin :show="loading">
            <n-tree
              block-line
              expand-on-click
              :data="menuTree"
              :selected-keys="selectedKey ? [selectedKey] : []"
              :render-label="renderLabel"
              @update:selected-keys="handleTreeSelect"
            />
          </n-spin>
        </div>
      </aside>

      <!-- 右侧表单区 -->
      <main class="menu-detail-pane">
        <div class="pane-header">
          <span>{{ form.id ? `编辑菜单项：${form.title}` : "新建菜单项" }}</span>
          <div class="header-actions" v-if="form.id">
            <n-button 
              size="small" 
              quaternary 
              :disabled="form.menuType === 'button'"
              @click="openCreateChild"
            >
              新增子节点
            </n-button>
            <n-button size="small" quaternary type="error" @click="confirmDelete">
              删除节点
            </n-button>
          </div>
        </div>

        <div class="form-container">
          <n-form ref="formRef" :model="form" :rules="rules" label-placement="top">
            <div class="form-grid">
              <n-form-item label="节点类型">
                <n-select
                  v-model:value="form.menuType"
                  :options="[
                    { label: '菜单分组 / 目录 (Category)', value: 'group' },
                    { label: '实体页面 / 功能 (Menu Page)', value: 'menu' },
                    { label: '操作按钮 / 权限标识 (Button / Action)', value: 'button' }
                  ]"
                />
              </n-form-item>

              <n-form-item label="唯一业务标识 (menuKey)" path="menuKey">
                <n-input v-model:value="form.menuKey" placeholder="例如 system:admin 或 system:admin:create">
                  <template #suffix>
                    <n-button 
                      size="tiny" 
                      quaternary 
                      type="primary" 
                      @click="generateRandomKeySuffix"
                      style="padding: 0 4px; font-size: 11px;"
                    >
                      生成随机后缀
                    </n-button>
                  </template>
                </n-input>
              </n-form-item>

              <n-form-item label="上级节点 (parentKey)" v-if="form.menuType === 'menu' || form.menuType === 'button'">
                <n-tree-select
                  v-model:value="form.parentKey"
                  clearable
                  :options="parentTreeOptions"
                  placeholder="选择上级节点"
                />
              </n-form-item>

              <n-form-item label="菜单名称 / 按钮标题 (title)" path="title">
                <n-input v-model:value="form.title" placeholder="例如 账号管理 或 新增账号" />
              </n-form-item>

              <n-form-item label="路由路径 / 目录前缀 (path)" path="path" v-if="form.menuType !== 'button'">
                <n-input v-model:value="form.path" placeholder="例如 /system 或 /system/admin" />
              </n-form-item>

              <n-form-item label="对应前端组件 (component)" path="component" v-if="form.menuType === 'menu'">
                <n-select
                  v-model:value="form.component"
                  :options="componentOptions"
                  placeholder="选择页面组件路径"
                  filterable
                />
              </n-form-item>

              <n-form-item label="菜单图标">
                <IconPicker v-model="form.icon" />
              </n-form-item>

              <n-form-item label="排序权重 (sort)">
                <n-input-number v-model:value="form.sort" :min="0" />
              </n-form-item>
            </div>

            <div class="switch-grid">
              <n-form-item label="侧边栏隐藏">
                <n-switch v-model:value="form.hidden" />
              </n-form-item>
              
              <n-form-item label="组件缓存" v-if="form.menuType === 'menu'">
                <n-switch v-model:value="form.cacheable" />
              </n-form-item>

              <n-form-item label="启用状态">
                <n-switch v-model:value="form.enabled" />
              </n-form-item>
            </div>

            <div class="form-submit-row">
              <n-button 
                type="primary" 
                :loading="saving" 
                @click="handleSave"
                class="save-btn"
              >
                保存配置
              </n-button>
              <n-button 
                quaternary 
                @click="resetForm"
                v-if="!form.id"
              >
                清空重置
              </n-button>
            </div>
          </n-form>
        </div>
      </main>
    </section>
  </div>
</template>

<script setup>
import { computed, h, onMounted, reactive, ref, watch } from "vue"
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NSpin,
  NSwitch,
  NTag,
  NTree,
  NTreeSelect,
  useDialog,
  useMessage,
} from "naive-ui"
import { fetchMenuList, createMenu, updateMenu, deleteMenu } from "../../../api/menu.js"
import { availableComponents } from "../../../router/dynamic.js"
import { getLocalPages } from "../../../shared/page-registry.js"
import AdminPageHeader from "../../../components/AdminPageHeader.vue"
import IconPicker from "../../../components/IconPicker.vue"

defineOptions({ name: "SystemMenu" })

const componentOptions = computed(() => {
  const localPages = getLocalPages()
  return availableComponents.map((name) => {
    const found = localPages.find((p) => p.component === name)
    const label = found ? `${name} (${found.title})` : name
    return {
      label,
      value: name,
    }
  })
})

// 表单响应式数据
const form = reactive({
  id: null,
  menuType: "menu", // group | menu
  menuKey: "",
  parentKey: null,
  title: "",
  path: "",
  component: "",
  icon: null,
  sort: 0,
  hidden: false,
  cacheable: false,
  enabled: true,
})

watch(
  [() => form.component, () => form.parentKey],
  ([newComp, newParent]) => {
    if (form.id || !newComp || newComp === "__group__" || newComp === "__button__") return

    // 创建新菜单时，智能填充相关配置
    const cleanName = newComp.replace("/index", "")
    const segments = cleanName.split("/")
    const leafName = segments[segments.length - 1] || cleanName

    const parentPrefix = newParent ? newParent.replace(/^g:/, "") : ""
    const expectedDefaultPath = "/" + cleanName
    const expectedDefaultKey = cleanName.replace(/\//g, ":")

    if (!form.menuKey || form.menuKey === expectedDefaultKey || form.menuKey.endsWith(":" + leafName) || form.menuKey.startsWith("system:")) {
      if (parentPrefix) {
        form.menuKey = `${parentPrefix}:${leafName}`
      } else {
        form.menuKey = expectedDefaultKey
      }
    }

    if (!form.path || form.path === "/" || form.path === expectedDefaultPath || form.path.endsWith("/" + leafName) || form.path.startsWith("/system/")) {
      if (parentPrefix) {
        form.path = `/${parentPrefix}/${leafName}`
      } else {
        form.path = expectedDefaultPath
      }
    }

    if (!form.title || form.title === "新根菜单" || form.title === "新子菜单") {
      const localPages = getLocalPages()
      const found = localPages.find((p) => p.component === newComp)
      if (found) {
        form.title = found.title
        if (found.icon) form.icon = found.icon
        if (found.sort !== undefined) form.sort = found.sort
        if (found.cacheable !== undefined) form.cacheable = found.cacheable
      }
    }
  }
)

watch(
  () => form.menuType,
  (newVal) => {
    if (newVal === "group") {
      form.parentKey = null
      form.path = ""
      form.component = "__group__"
    } else if (newVal === "button") {
      form.path = ""
      form.component = "__button__"
      form.hidden = true
      form.cacheable = false
    }
  }
)

watch(
  () => form.title,
  (newTitle) => {
    if (form.id || !newTitle || form.menuType !== "group") return
    if (newTitle === "新根菜单" || newTitle === "新子菜单") return

    const cleanStr = newTitle.toLowerCase().trim().replace(/[^a-zA-Z0-9]/g, "")
    if (cleanStr) {
      if (!form.menuKey || form.menuKey === "新根菜单" || form.menuKey.startsWith("g:")) {
        form.menuKey = `g:${cleanStr}`
      }
      if (!form.path || form.path === "/" || form.path.startsWith("/")) {
        form.path = `/${cleanStr}`
      }
    }
  }
)

const message = useMessage()
const dialog = useDialog()

const menus = ref([])
const loading = ref(false)
const saving = ref(false)
const selectedKey = ref(null)
const selectedNode = ref(null)



const formRef = ref(null)

const rules = {
  menuKey: {
    required: true,
    validator: (_rule, value) => {
      return (value || "").trim().length > 0
    },
    message: "请输入业务唯一键(menuKey)",
    trigger: ["blur", "input", "change"]
  },
  title: {
    required: true,
    validator: (_rule, value) => {
      return (value || "").trim().length > 0
    },
    message: "请输入菜单名称",
    trigger: ["blur", "input", "change"]
  },
  path: {
    required: true,
    validator: (_rule, value) => {
      if (form.menuType === "group" || form.menuType === "button") {
        if (!value) return true
        return value.startsWith("/")
      }
      return (value || "").startsWith("/")
    },
    message: "路径必须以 / 开头",
    trigger: ["blur", "input", "change"]
  },
  component: {
    required: true,
    validator: (_rule, value) => {
      if (form.menuType === "group" || form.menuType === "button") return true
      if (!value) return false
      return availableComponents.includes(value)
    },
    message: "必须选择一个有效的前端页面组件",
    trigger: ["blur", "change"]
  },
}

// 上级树形菜单选项过滤（排除自身，根据节点类型过滤可挂载的父节点）
const parentTreeOptions = computed(() => {
  if (form.menuType === "button") {
    // 按钮的父级必须是普通菜单/页面
    const pages = menus.value.filter(
      (item) => item.component !== "__group__" && item.component !== "__button__" && item.menuKey !== form.menuKey
    )
    return pages.map((item) => ({
      key: item.menuKey,
      value: item.menuKey,
      label: item.title,
    }))
  }

  // 菜单页面或子目录的上级必须是目录/分组
  const groups = menus.value.filter(
    (item) => item.component === "__group__" && item.menuKey !== form.menuKey
  )
  
  const map = new Map()
  for (const item of groups) {
    map.set(item.menuKey, {
      key: item.menuKey,
      value: item.menuKey,
      label: item.title,
      parentKey: item.parentKey,
      children: [],
    })
  }
  
  const roots = []
  for (const node of map.values()) {
    const parent = node.parentKey ? map.get(node.parentKey) : null
    if (parent) {
      parent.children.push(node)
    } else {
      roots.push(node)
    }
  }
  
  return roots
})

onMounted(loadMenus)

async function loadMenus() {
  loading.value = true
  try {
    menus.value = await fetchMenuList({ include_disabled: true })
    if (selectedKey.value) {
      const found = menus.value.find((item) => item.menuKey === selectedKey.value)
      if (found) selectNode(found)
      else resetForm()
    } else if (menus.value.length) {
      selectNode(menus.value[0])
    }
  } catch (error) {
    message.error("加载菜单列表失败")
  } finally {
    loading.value = false
  }
}

// 将扁平结构转为 NTree 树状组件可渲染的数据
const menuTree = computed(() => {
  const map = new Map()
  menus.value.forEach((item) => {
    const isGroup = item.component === "__group__"
    const isButton = item.component === "__button__"
    map.set(item.menuKey, {
      key: item.menuKey,
      label: item.title,
      isGroup: isGroup,
      isButton: isButton,
      isLeaf: isButton, // 按钮是叶子节点，不能有子节点（menu 类型根据实际子节点决定）
      raw: item,
      children: isButton ? undefined : [], // 目录与菜单可以有子节点
    })
  })
  const roots = []
  map.forEach((node) => {
    const parentKey = node.raw.parentKey
    if (parentKey && map.has(parentKey)) {
      if (map.get(parentKey).children) {
        map.get(parentKey).children.push(node)
      }
    } else {
      roots.push(node)
    }
  })
  
  const sortRec = (nodes) => {
    if (!nodes) return
    nodes.sort((a, b) => (a.raw.sort || 0) - (b.raw.sort || 0))
    nodes.forEach((node) => {
      if (node.children) sortRec(node.children)
    })
  }
  sortRec(roots)

  // 后处理：没有子节点的非 group 节点标记为叶子，去掉多余的展开三角
  const finalizeLeaf = (nodes) => {
    nodes.forEach((node) => {
      if (node.children !== undefined) {
        if (node.children.length === 0) {
          // 没有子节点：如果是 group 保留空 children（可新增子节点），否则标为叶子
          if (!node.isGroup) {
            node.isLeaf = true
            node.children = undefined
          }
        } else {
          finalizeLeaf(node.children)
        }
      }
    })
  }
  finalizeLeaf(roots)

  return roots
})

function selectNode(rawNode) {
  selectedNode.value = rawNode
  selectedKey.value = rawNode.menuKey
  
  form.id = rawNode.id
  form.menuKey = rawNode.menuKey
  form.parentKey = rawNode.parentKey
  form.title = rawNode.title
  form.path = rawNode.path
  form.component = rawNode.component
  form.menuType = rawNode.component === "__group__" ? "group" : (rawNode.component === "__button__" ? "button" : "menu")
  form.icon = rawNode.icon || "default"
  form.sort = rawNode.sort || 0
  form.hidden = Boolean(rawNode.hidden)
  form.cacheable = Boolean(rawNode.cacheable)
  form.enabled = Boolean(rawNode.enabled)
}

function handleTreeSelect(keys, optionList) {
  if (!keys.length) return
  const rawNode = optionList[0]?.raw
  if (rawNode) selectNode(rawNode)
}

function resetForm() {
  selectedNode.value = null
  selectedKey.value = null
  Object.assign(form, {
    id: null,
    menuType: "menu",
    menuKey: "",
    parentKey: null,
    title: "",
    path: "",
    component: "",
    icon: "default",
    sort: 0,
    hidden: false,
    cacheable: false,
    enabled: true,
  })
}

function openCreateRoot() {
  resetForm()
  form.menuKey = ""
  form.title = "新根菜单"
  form.path = "/"
  form.component = ""
}

function openCreateChild() {
  if (!selectedNode.value) return
  const parentKey = selectedNode.value.menuKey
  const parentComp = selectedNode.value.raw.component
  
  resetForm()
  form.parentKey = parentKey
  if (parentComp !== "__group__" && parentComp !== "__button__") {
    // 父级是普通菜单页面，子级自动填充为操作按钮
    form.menuType = "button"
    form.component = "__button__"
    form.hidden = true
    form.title = "新操作按钮"
  } else {
    // 父级是目录，子级为菜单页面
    form.menuType = "menu"
    form.title = "新子菜单"
  }
}

function generateRandomKeySuffix() {
  const rand = Math.random().toString(36).substring(2, 6);
  if (form.menuKey) {
    const match = form.menuKey.match(/(.*)_[a-z0-9]{4}$/);
    const oldBase = match ? match[1] : form.menuKey;
    form.menuKey = `${oldBase}_${rand}`;
    
    if (form.path && form.path !== "/") {
      const pathMatch = form.path.match(/(.*)_[a-z0-9]{4}$/);
      const oldPathBase = pathMatch ? pathMatch[1] : form.path;
      form.path = `${oldPathBase}_${rand}`;
    }
  } else {
    form.menuKey = `menu_${rand}`;
    if (!form.path || form.path === "/") {
      form.path = `/menu_${rand}`;
    }
  }
}

async function handleSave() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  
  const body = {
    menuKey: form.menuKey,
    parentKey: form.parentKey,
    title: form.title,
    path: form.menuType === "group" ? `/group:${form.menuKey}` : (form.menuType === "button" ? "" : form.path),
    component: form.menuType === "group" ? "__group__" : (form.menuType === "button" ? "__button__" : form.component),
    icon: form.icon,
    sort: form.sort,
    hidden: form.menuType === "button" ? true : form.hidden,
    cacheable: form.menuType === "button" ? false : form.cacheable,
    enabled: form.enabled,
  }
  
  saving.value = true
  try {
    if (form.id) {
      await updateMenu(form.id, body)
      message.success("菜单更新成功")
    } else {
      const res = await createMenu(body)
      selectedKey.value = res.menuKey
      message.success("新建菜单成功")
    }
    await loadMenus()
  } catch (error) {
    message.error(error?.response?.data?.msg || error?.message || "保存菜单失败")
  } finally {
    saving.value = false
  }
}

function confirmDelete() {
  if (!form.id) return
  dialog.warning({
    title: "删除菜单",
    content: `删除菜单【${form.title}】会清理关联角色的授权，如果存在子菜单请先处理，确认删除？`,
    positiveText: "删除",
    negativeText: "取消",
    onPositiveClick: handleDelete,
  })
}

async function handleDelete() {
  saving.value = true
  try {
    await deleteMenu(form.id)
    message.success("菜单已删除")
    selectedKey.value = null
    resetForm()
    await loadMenus()
  } catch (error) {
    message.error(error?.response?.data?.msg || error?.message || "删除菜单失败")
  } finally {
    saving.value = false
  }
}

// 目录图标：VSCode 风格蓝色描边文件夹
const FolderIcon = () => h('svg', {
  width: '15',
  height: '15',
  viewBox: '0 0 24 24',
  fill: 'none',
  style: 'margin-right: 6px; vertical-align: -2px; display: inline-block; flex-shrink: 0;'
}, [
  h('path', {
    d: 'M3 7a2 2 0 0 1 2-2h4.172a2 2 0 0 1 1.414.586l1.414 1.414A2 2 0 0 0 13.414 7.5H19a2 2 0 0 1 2 2V18a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z',
    fill: 'none',
    stroke: '#6cb3f0',
    strokeWidth: '1.6',
    strokeLinejoin: 'round'
  })
])

// 页面图标：VSCode 风格灰色描边文件
const FileIcon = () => h('svg', {
  width: '14',
  height: '14',
  viewBox: '0 0 24 24',
  fill: 'none',
  style: 'margin-right: 6px; vertical-align: -2px; display: inline-block; flex-shrink: 0;'
}, [
  h('path', {
    d: 'M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9l-7-7z',
    fill: 'none',
    stroke: '#c5c5c5',
    strokeWidth: '1.6',
    strokeLinejoin: 'round'
  }),
  h('path', {
    d: 'M13 2v7h7',
    fill: 'none',
    stroke: '#c5c5c5',
    strokeWidth: '1.6',
    strokeLinejoin: 'round'
  })
])

// 按钮/权限图标：橙色描边圆角矩形
const ButtonIcon = () => h('svg', {
  width: '15',
  height: '15',
  viewBox: '0 0 24 24',
  fill: 'none',
  style: 'margin-right: 6px; vertical-align: -2px; display: inline-block; flex-shrink: 0;'
}, [
  h('rect', { x: '2', y: '6', width: '20', height: '12', rx: '3', fill: 'none', stroke: '#f0a020', strokeWidth: '1.8' }),
  h('path', { d: 'M8 12h8', stroke: '#f0a020', strokeWidth: '1.8', strokeLinecap: 'round' })
])

function renderLabel({ option }) {
  const isEnabled = option.raw?.enabled !== false
  const isHidden = option.raw?.hidden === true
  const isGroup = option.isGroup
  const isButton = option.isButton
  
  return h("span", { 
    class: "menu-tree-label",
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: "6px",
      whiteSpace: "nowrap"
    }
  }, [
    isGroup ? FolderIcon() : (isButton ? ButtonIcon() : FileIcon()),
    h("span", { 
      style: {
        color: !isEnabled ? "var(--c-text-faint)" : "inherit",
        textDecoration: !isEnabled ? "line-through" : "none"
      }
    }, option.label),
    isButton ? h(NTag, { size: "tiny", bordered: false, type: "warning", style: "margin-left: 6px" }, { default: () => option.raw.menuKey }) : null,
    !isEnabled ? h(NTag, { size: "tiny", bordered: false, type: "error", style: "margin-left: 6px" }, { default: () => "禁用" }) : null,
    (isHidden && !isButton) ? h(NTag, { size: "tiny", bordered: false, type: "default", style: "margin-left: 6px" }, { default: () => "隐藏" }) : null,
  ])
}
</script>

<style scoped>
.menu-tree-label {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.menu-tree-label svg {
  flex-shrink: 0;
  display: inline-block;
}

.admin-page {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.menu-layout {
  display: grid;
  grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
  gap: var(--sp-4);
  min-height: 580px;
}

.menu-tree-pane,
.menu-detail-pane {
  border: 1px solid var(--c-border);
  border-radius: var(--r-xl);
  background: var(--c-surface);
  padding: var(--sp-4);
  box-shadow: var(--sh-1);
  display: flex;
  flex-direction: column;
}

.pane-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--sp-3);
  min-height: 32px;
  margin-bottom: var(--sp-4);
  font-weight: var(--fw-bold);
  color: var(--c-text-primary);
  border-bottom: 1px dashed var(--c-border);
  padding-bottom: var(--sp-3);
}

.tree-container {
  flex: 1;
  overflow-y: auto;
  max-height: 520px;
}

.form-container {
  flex: 1;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--sp-3) var(--sp-5);
  margin-bottom: var(--sp-2);
}

@media (max-width: 640px) {
  .form-grid {
    grid-template-columns: 1fr;
    gap: var(--sp-3);
  }
}

.switch-grid {
  display: flex;
  gap: var(--sp-6);
  background: var(--c-surface-sunken);
  padding: var(--sp-3) var(--sp-4);
  border-radius: var(--r-md);
  border: 1px solid var(--c-border);
  margin-top: var(--sp-4);
  margin-bottom: var(--sp-5);
  flex-wrap: wrap;
}

.switch-grid :deep(.n-form-item) {
  --n-label-font-size: var(--fs-sm);
  margin-bottom: 0;
}

.form-submit-row {
  display: flex;
  gap: var(--sp-2);
  border-top: 1px solid var(--c-border);
  padding-top: var(--sp-4);
}

.header-actions {
  display: flex;
  gap: var(--sp-1);
}

.save-btn {
  font-weight: var(--fw-semibold);
  padding-left: var(--sp-5);
  padding-right: var(--sp-5);
}

@media (max-width: 900px) {
  .menu-layout {
    grid-template-columns: 1fr;
  }
}
</style>
