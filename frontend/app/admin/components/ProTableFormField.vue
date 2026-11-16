<template>
  <n-form-item
    v-if="!(isEdit ? field.editDisabled : field.createDisabled)"
    :label="field.label"
    :path="field.key"
    :class="'form-item-' + field.key"
  >
    <slot
      :name="`form-${field.key}`"
      :field="field"
      :form-model="formModel"
      :is-edit="isEdit"
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
        :rows="field.autosize ? undefined : (field.rows || 3)"
        :autosize="field.autosize || false"
        :placeholder="field.placeholder || `请输入${field.label}`"
      />
      <n-select
        v-else-if="field.type === 'select'"
        v-model:value="formModel[field.key]"
        :options="field.options"
        :placeholder="field.placeholder || `请选择${field.label}`"
      />
      <n-input-number
        v-else-if="field.type === 'number'"
        v-model:value="formModel[field.key]"
        :placeholder="field.placeholder || `请输入${field.label}`"
        :disabled="isEdit ? field.editReadOnly : false"
        style="width: 100%"
      />
      <n-switch
        v-else-if="field.type === 'switch'"
        v-model:value="formModel[field.key]"
      />
    </slot>
  </n-form-item>
</template>

<script setup>
import { NFormItem, NInput, NSelect, NInputNumber, NSwitch } from "naive-ui"

defineProps({
  field: { type: Object, required: true },
  formModel: { type: Object, required: true },
  isEdit: { type: Boolean, default: false },
})
</script>

