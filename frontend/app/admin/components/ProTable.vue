<template>
  <div class="admin-page">
    <!-- 头部区域 -->
    <AdminPageHeader :title="title" :subtitle="subtitle">
      <template #actions>
        <slot name="header-actions">
          <n-button 
            v-if="createApi"
            v-auth="permissionPrefix ? `${permissionPrefix}:create` : ''"
            type="primary" 
            size="small" 
            @click="openCreate"
          >
            {{ createTitle || '新建' }}
          </n-button>
        </slot>
      </template>
    </AdminPageHeader>

    <!-- 搜索栏 -->
    <div v-if="searchFields && searchFields.length" class="admin-toolbar">
      <div
        v-for="field in searchFields"
        :key="field.key"
        class="toolbar-filter"
        :class="`toolbar-filter-${field.type || 'text'}`"
      >
        <span class="toolbar-filter-label">{{ field.label }}</span>
        <n-input
          v-if="field.type === 'text' || field.type === 'input' || !field.type"
          v-model:value="filters[field.key]"
          clearable
          :placeholder="field.placeholder || `请输入${field.label}...`"
          @input="handleSearch"
          class="toolbar-search"
        />
        <n-select
          v-else-if="field.type === 'select'"
          v-model:value="filters[field.key]"
          clearable
          :placeholder="field.placeholder || `选择${field.label}`"
          :options="field.options"
          @update:value="handleSearch"
          class="toolbar-select"
        />
        <n-input-number
          v-else-if="field.type === 'number'"
          v-model:value="filters[field.key]"
          clearable
          :placeholder="field.placeholder || field.label"
          :min="field.min"
          :max="field.max"
          :show-button="false"
          @update:value="handleSearch"
          class="toolbar-number"
        />
        <!-- 时间范围：NDatePicker daterange 双向绑定一个 [startMs, endMs] 数组。
             我们拆成两个 filter key（field.startKey / field.endKey）传给后端，方便和 query 参数对齐。 -->
        <n-date-picker
          v-else-if="field.type === 'daterange'"
          :value="filters[field.key]"
          type="daterange"
          clearable
          :placeholder="field.placeholder || field.label"
          @update:value="(val) => onDateRangeChange(field, val)"
          class="toolbar-daterange"
        />
      </div>
      <n-button @click="resetFilters" class="toolbar-btn">重置</n-button>
      <slot name="toolbar-extra"></slot>
    </div>

    <!-- 数据表格 -->
    <div class="admin-data-shell">
      <n-data-table
        remote
        flex-height
        :scroll-x="scrollX"
        :columns="tableColumns"
        :data="rows"
        :loading="loading"
        :pagination="pagination"
        :row-key="rowKey"
        @update:page="onPageChange"
        @update:page-size="onPageSizeChange"
      />
    </div>

    <!-- 新建/编辑 抽屉模式 -->
    <n-drawer
      v-if="formType === 'drawer'"
      v-model:show="showModal"
      :width="drawerWidth"
      placement="right"
      :class="['admin-account-drawer', modalClass]"
      :style="modalStyle"
      @after-leave="onModalClosed"
    >
      <n-drawer-content
        :title="isEdit ? (editTitle || '编辑') : (createTitle || '新建')"
        closable
        :body-content-style="{ padding: '16px 20px', display: 'flex', flexDirection: 'column', flex: '1 1 0', minHeight: 0, height: '100%', overflow: 'hidden' }"
        :footer-style="{ padding: '12px 24px', borderTop: '1px solid var(--n-border-color)' }"
      >
        <n-form
          ref="formRef"
          :model="formModel"
          :rules="formRules"
          label-placement="top"
          style="flex: 1; display: flex; flex-direction: column; min-height: 0;"
        >
          <slot
            name="form"
            :form-model="formModel"
            :is-edit="isEdit"
            :editing-row-id="editingRowId"
          >
            <!-- 多 tab 模式：formFields 至少一个带 field.tab -->
            <n-tabs
              v-if="hasTabs"
              v-model:value="activeTab"
              type="line"
              animated
              pane-style="padding-top: 14px"
            >
              <n-tab-pane
                v-for="tabName in tabNames"
                :key="tabName"
                :name="tabName"
                :tab="tabName"
                display-directive="show"
              >
                <ProTableFormField
                  v-for="field in fieldsByTab[tabName]"
                  :key="field.key"
                  :field="field"
                  :form-model="formModel"
                  :is-edit="isEdit"
                >
                  <template #[`form-${field.key}`]>
                    <slot
                      :name="`form-${field.key}`"
                      :field="field"
                      :form-model="formModel"
                      :is-edit="isEdit"
                    />
                  </template>
                </ProTableFormField>
              </n-tab-pane>
            </n-tabs>

            <!-- 无 tab 退化 -->
            <template v-else>
              <ProTableFormField
                v-for="field in formFields"
                :key="field.key"
                :field="field"
                :form-model="formModel"
                :is-edit="isEdit"
              >
                <template #[`form-${field.key}`]>
                  <slot
                    :name="`form-${field.key}`"
                    :field="field"
                    :form-model="formModel"
                    :is-edit="isEdit"
                  />
                </template>
              </ProTableFormField>
            </template>

            <slot
              name="form-extra"
              :form-model="formModel"
              :is-edit="isEdit"
              :editing-row-id="editingRowId"
            ></slot>
          </slot>
        </n-form>

        <template #footer>
          <div class="modal-actions">
            <n-button @click="showModal = false">取消</n-button>
            <n-button type="primary" :loading="saving" @click="submitForm">确定</n-button>
          </div>
        </template>
      </n-drawer-content>
    </n-drawer>

    <!-- 新建/编辑 弹窗模式 -->
    <n-modal
      v-else
      v-model:show="showModal"
      preset="card"
      :title="isEdit ? (editTitle || '编辑') : (createTitle || '新建')"
      :class="['admin-account-modal', modalClass]"
      :style="[
        {
          width: 'min(800px, calc(100vw - 32px))',
          maxHeight: 'min(900px, 90vh)',
          display: 'flex',
          flexDirection: 'column'
        },
        modalStyle
      ]"
      :content-style="{
        flex: 1,
        overflowY: 'auto',
        minHeight: 0
      }"
      @after-leave="onModalClosed"
    >
      <n-form
        ref="formRef"
        :model="formModel"
        :rules="formRules"
        label-placement="top"
      >
        <slot
          name="form"
          :form-model="formModel"
          :is-edit="isEdit"
          :editing-row-id="editingRowId"
        >
          <!-- 多 tab 模式：formFields 至少一个带 field.tab -->
          <n-tabs
            v-if="hasTabs"
            v-model:value="activeTab"
            type="line"
            animated
            pane-style="padding-top: 8px"
          >
            <n-tab-pane
              v-for="tabName in tabNames"
              :key="tabName"
              :name="tabName"
              :tab="tabName"
              display-directive="show"
            >
              <ProTableFormField
                v-for="field in fieldsByTab[tabName]"
                :key="field.key"
                :field="field"
                :form-model="formModel"
                :is-edit="isEdit"
              >
                <template #[`form-${field.key}`]>
                  <slot
                    :name="`form-${field.key}`"
                    :field="field"
                    :form-model="formModel"
                    :is-edit="isEdit"
                  />
                </template>
              </ProTableFormField>
            </n-tab-pane>
          </n-tabs>

          <!-- 无 tab 退化：完全保持旧行为，所有字段铺平 -->
          <template v-else>
            <ProTableFormField
              v-for="field in formFields"
              :key="field.key"
              :field="field"
              :form-model="formModel"
              :is-edit="isEdit"
            >
              <template #[`form-${field.key}`]>
                <slot
                  :name="`form-${field.key}`"
                  :field="field"
                  :form-model="formModel"
                  :is-edit="isEdit"
                />
              </template>
            </ProTableFormField>
          </template>

          <!-- 弹窗表单附加插槽（永远在 tab 之外，比如批量按钮） -->
          <slot
            name="form-extra"
            :form-model="formModel"
            :is-edit="isEdit"
            :editing-row-id="editingRowId"
          ></slot>
        </slot>
      </n-form>

      <template #footer>
        <div class="modal-actions">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" :loading="saving" @click="submitForm">确定</n-button>
        </div>
      </template>
    </n-modal>

    <!-- 其他额外插槽（比如其他特定用途的弹窗） -->
    <slot name="extra"></slot>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, h, watch, nextTick } from 'vue'
import { useDialog, useMessage, NButton, NSpace, NDatePicker, NInputNumber, NTabs, NTabPane, NDrawer, NDrawerContent } from 'naive-ui'
import AdminPageHeader from './AdminPageHeader.vue'
import ProTableFormField from './ProTableFormField.vue'

const props = defineProps({
  title: String,
  subtitle: String,
  columns: {
    type: Array,
    required: true
  },
  searchFields: Array,
  formFields: Array,
  formRules: Object,
  listApi: {
    type: Function,
    required: true
  },
  createApi: Function,
  updateApi: Function,
  deleteApi: Function,
  permissionPrefix: String,
  createTitle: String,
  editTitle: String,
  formType: {
    type: String,
    default: 'modal' // 'modal' | 'drawer'
  },
  drawerWidth: {
    type: [Number, String],
    default: 'min(980px, 90vw)'
  },
  modalStyle: {
    type: [Object, String],
    default: () => ({})
  },
  modalClass: {
    type: [String, Array, Object],
    default: ''
  },
  rowKey: {
    type: Function,
    default: (row) => row.id
  },
  rowActions: Function,
  canEdit: {
    type: Function,
    default: () => true
  },
  shouldShowEdit: {
    type: Function,
    default: () => true
  },
  canDelete: {
    type: Function,
    default: () => true
  },
  shouldShowDelete: {
    type: Function,
    default: () => true
  },
  actionsWidth: {
    type: [Number, String],
    default: 160
  },
  scrollX: {
    type: [Number, String],
    default: undefined
  }
})

const emit = defineEmits(['register-actions', 'success'])

const message = useMessage()
const dialog = useDialog()

// 状态定义
const loading = ref(false)
const saving = ref(false)
const rows = ref([])
const showModal = ref(false)
const isEdit = ref(false)
const editingRowId = ref(null)

const formRef = ref(null)
const formModel = ref({})

// ─── 多 tab 字段分组：field.tab 触发，否则保持旧的铺平 ───
const hasTabs = computed(() =>
  Array.isArray(props.formFields) && props.formFields.some((f) => f && f.tab),
)
const fieldsByTab = computed(() => {
  const groups = {}
  for (const f of (props.formFields || [])) {
    const tab = f.tab || "其他"
    if (!groups[tab]) groups[tab] = []
    groups[tab].push(f)
  }
  return groups
})
const tabNames = computed(() => {
  // 按 fields 中首次出现的顺序保 tab 顺序
  const seen = []
  for (const f of (props.formFields || [])) {
    const tab = f.tab || "其他"
    if (!seen.includes(tab)) seen.push(tab)
  }
  return seen
})
const activeTab = ref("")
// 打开弹窗时把 activeTab 重置到首个 tab，避免上次切到末尾下次再开还在那
watch(showModal, (open) => {
  if (open && tabNames.value.length) activeTab.value = tabNames.value[0]
})

// 搜索条件
const filters = reactive({})
// 初始化搜索条件默认值
if (props.searchFields) {
  props.searchFields.forEach(field => {
    filters[field.key] = field.defaultValue !== undefined ? field.defaultValue : null
  })
}

// 分页状态
const pagination = reactive({
  page: 1,
  pageSize: 10,
  itemCount: 0,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  prefix({ itemCount }) {
    return `共 ${itemCount} 条数据`
  }
})

// 表格列自动添加编辑/删除操作列（如果配置了权限前缀，则会自动套用 v-auth）
const tableColumns = computed(() => {
  const customCols = [...props.columns]
  
  // 检查是否需要操作列
  const hasEdit = !!props.updateApi
  const hasDelete = !!props.deleteApi
  const hasCustomActions = !!props.rowActions
  
  if (hasEdit || hasDelete || hasCustomActions) {
    customCols.push({
      title: '操作',
      key: 'actions',
      width: props.actionsWidth,
      fixed: props.scrollX ? 'right' : undefined,
      render(row) {
        const actionButtons = []
        
        if (hasEdit && props.shouldShowEdit(row)) {
          actionButtons.push(
            h(
              NButton,
              {
                size: 'tiny',
                quaternary: true,
                disabled: !props.canEdit(row),
                onClick: () => openEdit(row)
              },
              { default: () => '编辑' }
            )
          )
        }

        if (hasCustomActions) {
          const extraActions = props.rowActions(row, {
            openEdit,
            refresh: loadRows,
            handleDelete,
          })
          if (Array.isArray(extraActions)) {
            actionButtons.push(...extraActions.filter(Boolean))
          }
        }
        
        if (hasDelete && props.shouldShowDelete(row)) {
          actionButtons.push(
            h(
              NButton,
              {
                size: 'tiny',
                quaternary: true,
                type: 'error',
                disabled: !props.canDelete(row),
                onClick: () => handleDelete(row)
              },
              { default: () => '删除' }
            )
          )
        }
        
        return h(NSpace, { size: 12, class: 'admin-row-actions' }, { default: () => actionButtons })
      }
    })
  }
  
  return customCols
})

// 加载数据
async function loadRows() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.pageSize,
      ...filters
    }
    // 移除空值查询条件 + daterange 数组（已被拆成 startKey/endKey，原 key 不该再发后端）
    Object.keys(params).forEach(key => {
      const v = params[key]
      if (v === null || v === undefined || v === '' || Array.isArray(v)) {
        delete params[key]
      }
    })

    const res = await props.listApi(params)
    if (res) {
      // 兼容两种返回格式: { items, total } 或 { list, total } 或 直接是 res 数组
      if (Array.isArray(res)) {
        rows.value = res
        pagination.itemCount = res.length
      } else {
        rows.value = res.items || res.list || []
        // fallback: 后端没返回 total（例如简单 list 接口只返 {list: [...]}）时，
        // 用实际行数兜底，避免底部出现"共 0 条数据"但表格有数据的尴尬
        pagination.itemCount = res.total ?? rows.value.length
      }
    }
  } catch (err) {
    message.error(err.message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

// 搜索与分页操作
let timer = null
function handleSearch() {
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => {
    pagination.page = 1
    loadRows()
  }, 300)
}

// daterange 把 [startMs, endMs] 拆成 field.startKey / field.endKey 两条传给后端，
// 同时仍把数组形式保留在 filters[field.key]，让 NDatePicker 受控。
function onDateRangeChange(field, range) {
  filters[field.key] = range
  if (Array.isArray(range) && range.length === 2) {
    filters[field.startKey] = range[0]
    filters[field.endKey] = range[1]
  } else {
    filters[field.startKey] = null
    filters[field.endKey] = null
  }
  handleSearch()
}

function resetFilters() {
  if (props.searchFields) {
    props.searchFields.forEach(field => {
      filters[field.key] = field.defaultValue !== undefined ? field.defaultValue : null
      // daterange 还要清掉拆分出去的 startKey / endKey
      if (field.type === 'daterange') {
        filters[field.startKey] = null
        filters[field.endKey] = null
      }
    })
  }
  pagination.page = 1
  loadRows()
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

// 新建与编辑弹窗操作
function initFormModel() {
  const model = {}
  if (props.formFields) {
    props.formFields.forEach(field => {
      model[field.key] = field.defaultValue !== undefined ? field.defaultValue : null
    })
  }
  formModel.value = model
}

function openCreate() {
  isEdit.value = false
  editingRowId.value = null
  initFormModel()
  showModal.value = true
}

function openEdit(row) {
  isEdit.value = true
  editingRowId.value = props.rowKey(row)

  const model = {}
  if (props.formFields) {
    props.formFields.forEach(field => {
      // clearOnEdit 字段在编辑时清空 —— 用于 password / secret 类
      // 避免脱敏字符串（如 ab****cd）回填表单后被当作真值提交
      if (field.clearOnEdit) {
        model[field.key] = ""
      } else {
        model[field.key] = row[field.key] !== undefined ? row[field.key] : null
      }
    })
  }
  formModel.value = model
  showModal.value = true
}

function onModalClosed() {
  formModel.value = {}
  saving.value = false
}

async function showValidationErrors(errors) {
  const flattened = (Array.isArray(errors) ? errors.flat(Infinity) : [errors]).filter(Boolean)
  const first = flattened[0] || {}
  const rawField = Array.isArray(first.field) ? first.field[0] : (first.field || first.path || "")
  const fieldKey = String(rawField || "")
  const targetField = (props.formFields || []).find((field) => field.key === fieldKey)
  if (targetField?.tab) activeTab.value = targetField.tab

  const messages = [...new Set(flattened
    .map((item) => item?.message)
    .filter(Boolean))]
  message.warning(messages.length ? `请先完善：${messages.slice(0, 3).join("；")}` : "请检查必填项")

  await nextTick()
  const selector = fieldKey ? `.form-item-${CSS.escape(fieldKey)}` : ".n-form-item--error"
  const element = formRef.value?.$el?.querySelector?.(selector)
  element?.scrollIntoView?.({ behavior: "smooth", block: "center" })
  element?.querySelector?.("input, textarea")?.focus?.()
}

// 提交表单
function submitForm() {
  formRef.value?.validate(async (errors) => {
    if (errors) {
      await showValidationErrors(errors)
      return
    }
    
    saving.value = true
    try {
      if (isEdit.value) {
        if (props.updateApi) {
          await props.updateApi(editingRowId.value, formModel.value)
          message.success('保存成功')
        }
      } else {
        if (props.createApi) {
          await props.createApi(formModel.value)
          message.success('创建成功')
        }
      }
      showModal.value = false
      loadRows()
      emit('success', { type: isEdit.value ? 'edit' : 'create', model: formModel.value })
    } catch (err) {
      message.error(err.message || '操作失败')
    } finally {
      saving.value = false
    }
  })
}

// 删除操作
function handleDelete(row) {
  if (!props.canDelete(row)) return
  const id = props.rowKey(row)
  const displayName = row.title || row.name || row.username || id
  
  dialog.warning({
    title: '确认删除',
    content: `是否确认删除「${displayName}」？此操作不可撤销。`,
    positiveText: '确认删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await props.deleteApi(id)
        message.success('删除成功')
        // 如果当前页只有一条数据且不是第一页，则删除后页码减一
        if (rows.value.length === 1 && pagination.page > 1) {
          pagination.page -= 1
        }
        loadRows()
        emit('success', { type: 'delete', id })
      } catch (err) {
        message.error(err.message || '删除失败')
      }
    }
  })
}

// 暴露 API 供外部调用
defineExpose({
  refresh: loadRows,
  openCreate,
  openEdit,
  formModel,
  showModal,
  editingRowId
})

onMounted(() => {
  loadRows()
})
</script>

<style scoped>
.admin-page {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4, 16px);
  height: calc(100vh - 180px);
  min-height: 500px;
}

.admin-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 12px;
  align-items: end;
  flex-shrink: 0;
}

.toolbar-filter {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 180px;
  max-width: 260px;
}

.toolbar-filter-text {
  flex: 1.4;
  min-width: 220px;
  max-width: 320px;
}

.toolbar-filter-select,
.toolbar-filter-number {
  min-width: 150px;
  max-width: 190px;
}

.toolbar-filter-daterange {
  flex: 1.6;
  min-width: 260px;
  max-width: 360px;
}

.toolbar-filter-label {
  font-size: 12px;
  line-height: 1;
  color: var(--c-text-muted, #64748b);
  font-weight: 600;
  padding-left: 2px;
}

.toolbar-search {
  width: 100%;
}

.toolbar-select {
  width: 100%;
}

.toolbar-btn {
  flex-shrink: 0;
}

.admin-data-shell {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--c-surface, #ffffff);
  border: 1px solid var(--c-border, #e5e7eb);
  border-radius: var(--r-xl, 12px);
  padding: var(--sp-4, 16px);
  box-shadow: var(--sh-1, 0 1px 3px 0 rgba(0, 0, 0, 0.05));
}

.admin-data-shell :deep(.n-data-table) {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.admin-data-shell :deep(.n-data-table-wrapper) {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.admin-data-shell :deep(.n-pagination) {
  flex-shrink: 0;
  margin-top: var(--sp-3, 12px);
  justify-content: flex-end;
}

/* action-buttons 由 NSpace 替代，保留空规则兼容旧引用 */

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--sp-2, 8px);
}

:deep(.admin-account-drawer .n-drawer-body-content-wrapper),
:deep(.admin-account-drawer .n-drawer-body) {
  display: flex;
  flex-direction: column;
  flex: 1 1 0;
  min-height: 0;
  height: 100%;
}
</style>
