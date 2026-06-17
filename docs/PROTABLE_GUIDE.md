# ProTable 统一 CRUD 组件开发指南

`ProTable` 是本脚手架封装的**低代码高阶表格组件**，位于 [frontend/app/admin/components/ProTable.vue](file:///Users/struggler/Documents/project/front-project/智慧幕墙/smart-ai/frontend/app/admin/components/ProTable.vue)。它的设计初衷是通过 JSON Schema 配置，自动渲染标准的**数据表格、搜索条件、弹窗表单、分页、角色权限校验**，免去 80% 重复编写模板代码的工作。

如果在开发中感觉“代码生成器生成的效果不好”或“不够精细”，通常是因为仅使用了最基础的静态配置。通过本指南，你可以掌握 `ProTable` 的高级自定义用法，使其满足各种复杂的业务交互。

---

## 📂 快速导航
- [1. 基础配置参数 (Props)](#1-基础配置参数-props)
- [2. 高级列定义与 Render 自定义渲染](#2-高级列定义与-render-自定义渲染)
- [3. 插槽机制 (Slots) - 定制复杂组件](#3-插槽机制-slots---定制复杂组件)
- [4. 实例方法 (defineExpose)](#4-实例方法-defineexpose)
- [5. 最佳实践与避坑指南](#5-最佳实践与避坑指南)

---

## 1. 基础配置参数 (Props)

### 组件参数列表 (API)

| 参数名 | 类型 | 是否必填 | 默认值 | 说明 |
| :--- | :--- | :---: | :---: | :--- |
| `title` | `String` | 否 | - | 页面主标题 |
| `subtitle` | `String` | 否 | - | 页面副标题（说明文本） |
| `columns` | `Array` | **是** | - | 表格列定义，详见 Naive UI DataTable Columns |
| `searchFields` | `Array` | 否 | `[]` | 搜索栏表单字段配置 |
| `formFields` | `Array` | 否 | `[]` | 弹窗表单字段配置 |
| `formRules` | `Object` | 否 | - | 弹窗表单校验规则，详见 Naive UI Form Rules |
| `listApi` | `Function` | **是** | - | 获取数据 API 函数，必须返回 `{ items, total }` 或数组 |
| `createApi` | `Function` | 否 | - | 新增保存 API 函数，有此属性时会自动渲染“新建”按钮 |
| `updateApi` | `Function` | 否 | - | 修改保存 API 函数，有此属性时操作列会自动渲染“编辑” |
| `deleteApi` | `Function` | 否 | - | 删除 API 函数，有此属性时操作列会自动渲染“删除” |
| `permissionPrefix` | `String` | 否 | - | 权限前缀。配置后，新建自动绑定 `<prefix>:create`，编辑绑定 `<prefix>:update`，删除绑定 `<prefix>:delete` |
| `createTitle` | `String` | 否 | `'新建'` | 新建弹窗的标题 |
| `editTitle` | `String` | 否 | `'编辑'` | 编辑弹窗的标题 |
| `rowKey` | `Function` | 否 | `(row) => row.id` | 表格行的 Key 生成函数 |

### 🔍 `searchFields` 检索字段配置项
```javascript
{
  key: 'status',               // 接口请求参数字段名
  label: '状态',                // 表单 Label
  type: 'select',              // 类型: 'text' (默认) | 'select'
  placeholder: '请选择状态',     // 占位符 (可选)
  options: [],                 // 下拉框选项: [{ label, value }] (仅在 select 类型生效)
  defaultValue: null           // 默认值 (可选)
}
```

### 📝 `formFields` 表单字段配置项
```javascript
{
  key: 'username',             // 实体字段名
  label: '用户名',              // 表单 Label
  type: 'text',                // 类型: 'text' | 'password' | 'textarea' | 'select' | 'switch'
  placeholder: '请输入用户名',   // 占位符 (可选)
  options: [],                 // 选项数组 (仅在 select 类型生效)
  defaultValue: null,          // 默认值 (可选)
  createDisabled: false,       // 是否在新建时隐藏
  editDisabled: false,         // 是否在编辑时隐藏
  editReadOnly: false          // 是否在编辑时置为只读
}
```

---

## 2. 高级列定义与 Render 自定义渲染

`ProTable` 底层使用 Naive UI 的 `n-data-table`。当我们需要渲染状态标签、头像、开关或操作链接时，可以通过 Naive UI 的 `render()` 函数，使用 Vue 3 的 `h` 渲染函数来动态生成 DOM。

### 常用渲染范例

#### ① 渲染为 Tag (标签)
适合“状态”、“类型”等分类字段展示：
```javascript
import { h } from 'vue'
import { NTag } from 'naive-ui'

const columns = [
  {
    title: '状态',
    key: 'status',
    render(row) {
      const isEnabled = row.status === 1
      return h(
        NTag,
        {
          type: isEnabled ? 'success' : 'error',
          bordered: false,
          size: 'small'
        },
        { default: () => (isEnabled ? '正常' : '禁用') }
      )
    }
  }
]
```

#### ② 渲染为文本截断或提示 (Tooltip / Code)
```javascript
import { h } from 'vue'
import { NText } from 'naive-ui'

const columns = [
  {
    title: '标识码',
    key: 'code',
    render(row) {
      return h(NText, { depth: 3, code: true }, { default: () => row.code })
    }
  }
]
```

---

## 3. 插槽机制 (Slots) - 定制复杂组件

当默认表单满足不了需求（例如需要使用时间选择器、上传组件、多选框、或者是树形控件）时，我们需要利用 **插槽 (Slots)** 进行高程度的个性化定制。

### 插槽概览

| 插槽名 | 作用位置 | 暴露的参数 | 常用场景 |
| :--- | :--- | :--- | :--- |
| `header-actions` | 页面标题右侧 | - | 替换/追加自定义操作按钮（如“导出 Excel”、“批量审核”） |
| `toolbar-extra` | 搜索栏最右侧 | - | 增加额外的检索项，如“时间区间选择器” |
| `form-extra` | 弹窗表单最底部 | `{ formModel, isEdit }` | 在弹窗中加入不支持的复杂表单项（如附件上传、部门选择树） |
| `extra` | 组件根结点下 | - | 加入页面私有的独立 Drawer、自定义 Modal 容器等 |

### 🛠️ 实战演练：在弹窗中使用时间选择器与插槽

```html
<template>
  <pro-table
    title="活动管理"
    api-path="/api/v1/campaigns"
    :columns="columns"
    :form-fields="baseFormFields"
    :form-rules="rules"
    :list-api="listCampaigns"
    :create-api="createCampaign"
    :update-api="updateCampaign"
  >
    <!-- 1. 自定义搜索栏：增加日期范围选择 -->
    <template #toolbar-extra>
      <n-date-picker 
        v-model:value="searchDateRange" 
        type="daterange" 
        clearable 
        @update:value="onDateRangeChange"
      />
    </template>

    <!-- 2. 自定义表单弹窗：增加富文本或日期选择器 -->
    <template #form-extra="{ formModel, isEdit }">
      <n-form-item label="活动起止时间" path="time_range">
        <!-- 动态向 formModel 里注入 ProTable 声明以外的字段 -->
        <n-date-picker
          v-model:value="formModel.time_range"
          type="datetimerange"
          clearable
        />
      </n-form-item>
    </template>
  </pro-table>
</template>

<script setup>
import { ref } from 'vue'
import ProTable from '@/components/ProTable.vue'

// 基础字段定义
const baseFormFields = [
  { key: 'title', label: '活动名称', type: 'text' },
  { key: 'budget', label: '活动预算', type: 'text' }
]

// 搜索栏日期临时变量
const searchDateRange = ref(null)

function onDateRangeChange(val) {
  // 可以在此处直接调用后台做数据重载或通过 refs 刷新 ProTable
}
</script>
```

---

## 4. 实例方法 (defineExpose)

如果需要从父页面手动控制 `ProTable` 的行为，可以通过 Vue `ref` 获取实例并调用以下暴露的方法：

```html
<template>
  <n-button @click="triggerRefresh">手动刷新</n-button>
  
  <pro-table ref="tableRef" :columns="columns" :list-api="myListApi" />
</template>

<script setup>
import { ref } from 'vue'

const tableRef = ref(null)

// 1. 手动触发数据重载
function triggerRefresh() {
  tableRef.value?.refresh()
}

// 2. 外部直接打开新建弹窗
function openCreateModal() {
  tableRef.value?.openCreate()
}

// 3. 甚至可以直接操作弹窗的表单响应式模型
function presetFormData() {
  if (tableRef.value) {
    tableRef.value.formModel.some_key = 'preset_value'
  }
}
</script>
```

---

## 5. 最佳实践与避坑指南

> [!TIP]
> 1. **宽度分配**：至少给某一列不设宽度，或者将表格其中一列设为 `ellipsis: true`，这样表格在大屏和窄屏下都能自适应延伸，避免出现横向滚动条时的布局空白。
> 2. **异步 Options**：如果 `formFields` 的下拉框选项需要从后台字典接口动态获取，不要直接写死静态数组。建议在父组件的 `onMounted` 中通过接口获取完，再赋值给对应的 `options`。
> 3. **敏感操作拦截**：删除、禁用等操作在 `ProTable` 内已经集成了 Naive UI 的 `dialog.warning` 确认框，无需在 `deleteApi` 接口回调中自己再手写二次弹出拦截。
> 4. **`v-auth` 按钮鉴权细节**：只要传递了 `permissionPrefix="system:role"`，ProTable 内自动生成的“新建”、“编辑”、“删除”按钮会分别绑定权限 `'system:role:create'`、`'system:role:update'` 和 `'system:role:delete'`。请确保您在“菜单管理”中录入的资源码与此严格对应。
