<template>
  <div class="admin-page">
    <AdminPageHeader title="数据字典" subtitle="统一配置和管理系统业务常量值，如订单状态、配置类型，避免硬编码" />

    <section class="dict-layout">
      <!-- 左侧分类列表 -->
      <aside class="dict-category-pane">
        <div class="pane-header">
          <span>字典分类</span>
          <n-button v-auth="'system:dict:update'" type="primary" size="tiny" secondary @click="openCreateCat">新增</n-button>
        </div>
        <div class="category-list-container">
          <n-spin :show="loadingCats">
            <div 
              v-for="cat in categories" 
              :key="cat.id" 
              class="cat-item"
              :class="{ active: selectedCat && selectedCat.code === cat.code }"
              @click="handleSelectCat(cat)"
            >
              <div class="cat-info">
                <span class="cat-name">{{ cat.name }}</span>
                <span class="cat-code font-mono">{{ cat.code }}</span>
              </div>
              <div class="cat-actions" v-auth="'system:dict:update'">
                <n-button size="tiny" quaternary circle @click.stop="openEditCat(cat)">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                </n-button>
                <n-button size="tiny" quaternary circle type="error" @click.stop="confirmDeleteCat(cat)">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/></svg>
                </n-button>
              </div>
            </div>
            <div v-if="categories.length === 0" class="empty-text">暂无字典分类</div>
          </n-spin>
        </div>
      </aside>

      <!-- 右侧明细表格 -->
      <main class="dict-detail-pane">
        <div class="pane-header">
          <span>{{ selectedCat ? `"${selectedCat.name}" 字典明细` : "字典明细" }}</span>
          <n-button 
            v-if="selectedCat" 
            v-auth="'system:dict:update'" 
            type="primary" 
            size="tiny" 
            secondary 
            @click="openCreateItem"
          >
            新增明细
          </n-button>
        </div>
        <div class="detail-container">
          <div v-if="!selectedCat" class="empty-select-tip">
            请从左侧选择一个字典分类以查看或管理其明细项
          </div>
          <n-spin v-else :show="loadingItems">
            <n-data-table
              :columns="columns"
              :data="items"
              :row-key="(row) => row.id"
              size="small"
              class="dict-item-table"
            />
          </n-spin>
        </div>
      </main>
    </section>

    <!-- 分类新增/编辑 Modal -->
    <n-modal v-model:show="showCatModal" preset="card" :title="catForm.id ? '编辑字典分类' : '新建字典分类'" class="dict-modal">
      <n-form ref="catFormRef" :model="catForm" :rules="catRules" label-placement="top">
        <n-form-item label="分类编码 (code)" path="code">
          <n-input v-model:value="catForm.code" :disabled="Boolean(catForm.id)" placeholder="例如 user_status" />
        </n-form-item>
        <n-form-item label="分类名称 (name)" path="name">
          <n-input v-model:value="catForm.name" placeholder="例如 用户状态" />
        </n-form-item>
        <n-form-item label="分类描述 (description)" path="description">
          <n-input v-model:value="catForm.description" type="textarea" placeholder="描述该字典分类对应的业务场景" />
        </n-form-item>
        <n-form-item label="启用状态" path="enabled" v-if="catForm.id">
          <n-switch v-model:value="catForm.enabled" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-actions">
          <n-button @click="showCatModal = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="submitCat">保存</n-button>
        </div>
      </template>
    </n-modal>

    <!-- 明细项新增/编辑 Modal -->
    <n-modal v-model:show="showItemModal" preset="card" :title="itemForm.id ? '编辑字典明细' : '新建字典明细'" class="dict-modal">
      <n-form ref="itemFormRef" :model="itemForm" :rules="itemRules" label-placement="top">
        <n-form-item label="标签名称 (label)" path="label">
          <n-input v-model:value="itemForm.label" placeholder="例如 正常" />
        </n-form-item>
        <n-form-item label="健值 (value)" path="value">
          <n-input v-model:value="itemForm.value" placeholder="例如 active" />
        </n-form-item>
        <n-form-item label="排序值 (sort)" path="sort">
          <n-input-number v-model:value="itemForm.sort" :min="0" style="width: 100%" />
        </n-form-item>
        <n-form-item label="启用状态" path="enabled" v-if="itemForm.id">
          <n-switch v-model:value="itemForm.enabled" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="modal-actions">
          <n-button @click="showItemModal = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="submitItem">保存</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { computed, h, onMounted, reactive, ref } from "vue"
import { NButton, NDataTable, NForm, NFormItem, NInput, NInputNumber, NModal, NSelect, NSpace, NSwitch, NSpin, useDialog, useMessage } from "naive-ui"
import AdminPageHeader from "../../../components/AdminPageHeader.vue"
import { dictApi } from "../../../api/dict.js"
import { hasPermission } from "../../../shared/auth.js"
import { notifySuccess, notifyError } from "../../../api/feedback.js"

defineOptions({ name: "SystemDict" })

const message = useMessage()
const dialog = useDialog()
const loadingCats = ref(false)
const loadingItems = ref(false)
const saving = ref(false)

const categories = ref([])
const items = ref([])
const selectedCat = ref(null)

// 分类 Modal 控制
const showCatModal = ref(false)
const catFormRef = ref(null)
const catForm = reactive({
  id: null,
  code: "",
  name: "",
  description: "",
  enabled: true
})
const catRules = {
  code: { required: true, message: "分类编码不能为空", trigger: ["blur", "input"] },
  name: { required: true, message: "分类名称不能为空", trigger: ["blur", "input"] }
}

// 明细项 Modal 控制
const showItemModal = ref(false)
const itemFormRef = ref(null)
const itemForm = reactive({
  id: null,
  label: "",
  value: "",
  sort: 0,
  enabled: true
})
const itemRules = {
  label: { required: true, message: "标签名称不能为空", trigger: ["blur", "input"] },
  value: { required: true, message: "键值不能为空", trigger: ["blur", "input"] }
}

const columns = [
  { title: "明细 ID", key: "id", width: 80 },
  { title: "字典标签 (Label)", key: "label", minWidth: 150 },
  { title: "字典键值 (Value)", key: "value", minWidth: 150, render: (row) => h("code", { class: "code-value" }, row.value) },
  { title: "排序", key: "sort", width: 80 },
  {
    title: "状态",
    key: "enabled",
    width: 100,
    render(row) {
      return h(NSwitch, {
        value: Boolean(row.enabled),
        disabled: !hasPermission("system:dict:update"),
        "onUpdate:value": (val) => updateItemEnabled(row, val)
      })
    }
  },
  {
    title: "操作",
    key: "actions",
    width: 150,
    render(row) {
      const btns = []
      if (hasPermission("system:dict:update")) {
        btns.push(h(NButton, {
          size: "small",
          quaternary: true,
          onClick: () => openEditItem(row)
        }, { default: () => "编辑" }))
        btns.push(h(NButton, {
          size: "small",
          quaternary: true,
          type: "error",
          onClick: () => confirmDeleteItem(row)
        }, { default: () => "删除" }))
      }
      return h(NSpace, { size: 6 }, { default: () => btns })
    }
  }
]

async function loadCategories() {
  loadingCats.value = true
  try {
    categories.value = await dictApi.list()
    if (categories.value.length && !selectedCat.value) {
      // 默认选择第一个分类
      handleSelectCat(categories.value[0])
    }
  } catch (err) {
    notifyError(err.message || "加载分类失败")
  } finally {
    loadingCats.value = false
  }
}

async function handleSelectCat(cat) {
  selectedCat.value = cat
  loadingItems.value = true
  try {
    items.value = await dictApi.listItems(cat.code)
  } catch (err) {
    notifyError(err.message || "加载字典明细失败")
  } finally {
    loadingItems.value = false
  }
}

// ─────────────────────────────────────────────────────────────────────────
// 分类增删改
// ─────────────────────────────────────────────────────────────────────────

function openCreateCat() {
  catForm.id = null
  catForm.code = ""
  catForm.name = ""
  catForm.description = ""
  catForm.enabled = true
  showCatModal.value = true
}

function openEditCat(cat) {
  catForm.id = cat.id
  catForm.code = cat.code
  catForm.name = cat.name
  catForm.description = cat.description || ""
  catForm.enabled = cat.enabled
  showCatModal.value = true
}

async function submitCat() {
  catFormRef.value?.validate(async (errors) => {
    if (errors) return
    saving.value = true
    try {
      if (catForm.id) {
        await dictApi.update(catForm.id, {
          name: catForm.name,
          description: catForm.description,
          enabled: catForm.enabled
        })
        message.success("修改字典分类成功")
      } else {
        await dictApi.create({
          code: catForm.code,
          name: catForm.name,
          description: catForm.description
        })
        message.success("新增字典分类成功")
      }
      showCatModal.value = false
      await loadCategories()
    } catch (err) {
      notifyError(err.message || "操作失败")
    } finally {
      saving.value = false
    }
  })
}

function confirmDeleteCat(cat) {
  const d = dialog.warning({
    title: "确认删除分类",
    content: `确定要删除分类 "${cat.name}" (${cat.code}) 吗？这会连带删除旗下所有明细项，且不可恢复！`,
    positiveText: "彻底删除",
    negativeText: "取消",
    onPositiveClick: async () => {
      d.loading = true
      try {
        await dictApi.delete(cat.id)
        message.success("删除成功")
        if (selectedCat.value && selectedCat.value.id === cat.id) {
          selectedCat.value = null
          items.value = []
        }
        await loadCategories()
      } catch (err) {
        notifyError(err.message || "删除失败")
      } finally {
        d.loading = false
      }
    }
  })
}

// ─────────────────────────────────────────────────────────────────────────
// 明细项增删改
// ─────────────────────────────────────────────────────────────────────────

function openCreateItem() {
  itemForm.id = null
  itemForm.label = ""
  itemForm.value = ""
  itemForm.sort = 0
  itemForm.enabled = true
  showItemModal.value = true
}

function openEditItem(row) {
  itemForm.id = row.id
  itemForm.label = row.label
  itemForm.value = row.value
  itemForm.sort = row.sort
  itemForm.enabled = row.enabled
  showItemModal.value = true
}

async function submitItem() {
  itemFormRef.value?.validate(async (errors) => {
    if (errors) return
    saving.value = true
    try {
      if (itemForm.id) {
        await dictApi.updateItem(itemForm.id, {
          label: itemForm.label,
          value: itemForm.value,
          sort: itemForm.sort,
          enabled: itemForm.enabled
        })
        message.success("修改明细项成功")
      } else {
        await dictApi.createItem(selectedCat.value.code, {
          label: itemForm.label,
          value: itemForm.value,
          sort: itemForm.sort
        })
        message.success("新增明细项成功")
      }
      showItemModal.value = false
      if (selectedCat.value) {
        handleSelectCat(selectedCat.value)
      }
    } catch (err) {
      notifyError(err.message || "操作明细项失败")
    } finally {
      saving.value = false
    }
  })
}

async function updateItemEnabled(row, enabled) {
  try {
    await dictApi.updateItem(row.id, { enabled })
    message.success(enabled ? "已启用" : "已禁用")
    if (selectedCat.value) {
      handleSelectCat(selectedCat.value)
    }
  } catch (err) {
    notifyError(err.message || "修改状态失败")
  }
}

function confirmDeleteItem(row) {
  const d = dialog.warning({
    title: "确认删除明细",
    content: `确定要删除明细项 "${row.label}" (${row.value}) 吗？`,
    positiveText: "删除",
    negativeText: "取消",
    onPositiveClick: async () => {
      d.loading = true
      try {
        await dictApi.deleteItem(row.id)
        message.success("删除成功")
        if (selectedCat.value) {
          handleSelectCat(selectedCat.value)
        }
      } catch (err) {
        notifyError(err.message || "删除失败")
      } finally {
        d.loading = false
      }
    }
  })
}

onMounted(() => {
  loadCategories()
})
</script>

<style scoped>
.admin-page {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
  height: 100%;
}

.dict-layout {
  display: flex;
  gap: var(--sp-4);
  height: calc(100vh - 180px);
  min-height: 500px;
}

.dict-category-pane {
  width: 280px;
  min-width: 280px;
  background: var(--c-surface);
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.dict-detail-pane {
  flex: 1;
  background: var(--c-surface);
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.pane-header {
  height: 48px;
  padding: 0 var(--sp-4);
  border-bottom: 1px solid rgba(226, 232, 240, 0.8);
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
  color: var(--c-text-primary);
  background: #f9fafb;
}

.category-list-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.cat-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  margin-bottom: 4px;
}

.cat-item:hover {
  background: #f3f4f6;
}

.cat-item.active {
  background: #eef2ff;
  color: var(--c-primary);
}

.cat-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.cat-name {
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cat-code {
  font-size: 11px;
  color: #6b7280;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cat-item.active .cat-code {
  color: #818cf8;
}

.cat-actions {
  display: none;
  gap: 4px;
  margin-left: 8px;
}

.cat-item:hover .cat-actions {
  display: flex;
}

.detail-container {
  flex: 1;
  padding: var(--sp-4);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.empty-select-tip {
  margin: auto;
  font-size: 13px;
  color: #9ca3af;
  text-align: center;
}

.dict-item-table {
  flex: 1;
}

.code-value {
  font-family: monospace;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}

.empty-text {
  padding: var(--sp-8) 0;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
}

:global(.dict-modal) {
  width: min(500px, calc(100vw - 32px));
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.font-mono {
  font-family: monospace;
}
</style>
