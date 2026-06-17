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
      <template v-for="field in searchFields" :key="field.key">
        <n-input
          v-if="field.type === 'text' || !field.type"
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
      </template>
      <n-button @click="resetFilters" class="toolbar-btn">重置</n-button>
      <slot name="toolbar-extra"></slot>
    </div>

    <!-- 数据表格 -->
    <div class="admin-data-shell">
      <n-data-table
        remote
        :columns="tableColumns"
        :data="rows"
        :loading="loading"
        :pagination="pagination"
        :row-key="rowKey"
        @update:page="onPageChange"
        @update:page-size="onPageSizeChange"
      />
    </div>

    <!-- 新建/编辑 弹窗 -->
    <n-modal
      v-model:show="showModal"
      preset="card"
      :title="isEdit ? (editTitle || '编辑') : (createTitle || '新建')"
      class="admin-account-modal"
      @after-leave="onModalClosed"
    >
      <n-form
        ref="formRef"
        :model="formModel"
        :rules="formRules"
        label-placement="top"
      >
        <template v-for="field in formFields" :key="field.key">
          <!-- 仅在新建时展示，或编辑时未禁用 -->
          <n-form-item
            v-if="!(isEdit ? field.editDisabled : field.createDisabled)"
            :label="field.label"
            :path="field.key"
          >
            <n-input
              v-if="field.type === 'text' || !field.type"
              v-model:value="formModel[field.key]"
              :placeholder="field.placeholder || `请输入${field.label}`"
              :disabled="isEdit ? field.editReadOnly : false"
            />
            <n-input
              v-else-if="field.type === 'password'"
              v-model:value="formModel[field.key]"
              type="password"
              show-password-on="click"
              :placeholder="field.placeholder || `请输入${field.label}`"
            />
            <n-input
              v-else-if="field.type === 'textarea'"
              v-model:value="formModel[field.key]"
              type="textarea"
              :rows="field.rows || 3"
              :placeholder="field.placeholder || `请输入${field.label}`"
            />
            <n-select
              v-else-if="field.type === 'select'"
              v-model:value="formModel[field.key]"
              :options="field.options"
              :placeholder="field.placeholder || `请选择${field.label}`"
            />
            <n-switch
              v-else-if="field.type === 'switch'"
              v-model:value="formModel[field.key]"
            />
          </n-form-item>
        </template>
        <!-- 弹窗表单附加插槽 -->
        <slot name="form-extra" :form-model="formModel" :is-edit="isEdit"></slot>
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
import { ref, reactive, onMounted, computed, h } from 'vue'
import { useDialog, useMessage, NButton } from 'naive-ui'
import AdminPageHeader from './AdminPageHeader.vue'

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
  rowKey: {
    type: Function,
    default: (row) => row.id
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
  
  if (hasEdit || hasDelete) {
    customCols.push({
      title: '操作',
      key: 'actions',
      width: 150,
      render(row) {
        const actionButtons = []
        
        if (hasEdit) {
          actionButtons.push(
            h(
              NButton,
              {
                size: 'tiny',
                type: 'primary',
                ghost: true,
                style: 'margin-right: 8px',
                onClick: () => openEdit(row)
              },
              { default: () => '编辑' }
            )
          )
        }
        
        if (hasDelete) {
          actionButtons.push(
            h(
              NButton,
              {
                size: 'tiny',
                type: 'error',
                ghost: true,
                onClick: () => handleDelete(row)
              },
              { default: () => '删除' }
            )
          )
        }
        
        return h('div', { class: 'action-buttons' }, actionButtons)
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
    // 移除空值查询条件
    Object.keys(params).forEach(key => {
      if (params[key] === null || params[key] === '') {
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
        pagination.itemCount = res.total || 0
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

function resetFilters() {
  if (props.searchFields) {
    props.searchFields.forEach(field => {
      filters[field.key] = field.defaultValue !== undefined ? field.defaultValue : null
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
      model[field.key] = row[field.key] !== undefined ? row[field.key] : null
    })
  }
  formModel.value = model
  showModal.value = true
}

function onModalClosed() {
  formModel.value = {}
  saving.value = false
}

// 提交表单
function submitForm() {
  formRef.value?.validate(async (errors) => {
    if (errors) return
    
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
  formModel
})

onMounted(() => {
  loadRows()
})
</script>

<style scoped>
.admin-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
  padding: 14px;
  background: var(--card-bg, rgba(255, 255, 255, 0.6));
  border: 1px solid var(--border-color, rgba(0, 0, 0, 0.08));
  border-radius: 8px;
}

.toolbar-search {
  max-width: 260px;
}

.toolbar-select {
  width: 160px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
