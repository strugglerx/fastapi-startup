<template>
  <ProTable
    :title="title"
    :subtitle="subtitle"
    :columns="columns"
    :search-fields="searchFields"
    :form-fields="formFields"
    :form-rules="formRules"
    :list-api="fetchProductList"
    :create-api="createProduct"
    :update-api="updateProduct"
    :delete-api="deleteProduct"
    permission-prefix="system:product"
  />
</template>

<script setup>
import { ref } from 'vue'
import ProTable from '@/components/ProTable.vue'
import {
  fetchProductList,
  createProduct,
  updateProduct,
  deleteProduct
} from '#/admin/api/product.js'

const title = '产品管理'
const subtitle = '产品管理数据的查看、新建、修改与删除'

const columns = [
  { title: '产品名称', key: 'name', minWidth: 120 },
  { title: '产品单价', key: 'price', minWidth: 120 },
  { title: '状态', key: 'status', minWidth: 120 },
  { title: '描述', key: 'description', minWidth: 120 },
]

const searchFields = [
  { label: '产品名称', key: 'name', type: 'text', placeholder: '按产品名称搜索...' },
  { label: '描述', key: 'description', type: 'text', placeholder: '按描述搜索...' },
]

const formFields = [
  { label: '产品名称', key: 'name', type: 'text' },
  { label: '产品单价', key: 'price', type: 'text' },
  { label: '状态', key: 'status', type: 'text' },
  { label: '描述', key: 'description', type: 'textarea' },
]

const formRules = {
  name: { required: true, message: '请输入产品名称', trigger: 'blur' },
}
</script>
