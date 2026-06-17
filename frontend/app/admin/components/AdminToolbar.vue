<template>
  <div class="admin-toolbar">
    <!-- Search input -->
    <label v-if="searchable" class="admin-search-box">
      <svg class="admin-search-box__icon" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input
        class="admin-search-box__input"
        :value="searchValue"
        :placeholder="searchPlaceholder"
        @input="$emit('update:searchValue', $event.target.value)"
      />
    </label>

    <!-- Filter chips. Built as <button>, never <option>. -->
    <div v-if="filters && filters.length" class="admin-filter-chips">
      <button
        v-for="f in filters"
        :key="f.key === undefined ? f.label : String(f.key)"
        type="button"
        class="admin-filter-chip"
        :class="{ 'is-active': isActive(f) }"
        @click="onChipClick(f)"
      >
        {{ f.label }}<span v-if="f.count != null" class="filter-count">&nbsp;{{ f.count }}</span>
      </button>
    </div>

    <!-- Right-side: free slot (custom controls) then optional count. -->
    <div v-if="$slots.right" class="toolbar-right">
      <slot name="right" />
    </div>
    <span v-if="count != null" class="admin-toolbar__count">{{ countPrefix }}{{ count }}{{ countSuffix }}</span>
  </div>
</template>

<script setup>
import { computed } from "vue"

/**
 * AdminToolbar — unified search + filter-chips + counter row.
 *
 * Filter model: filters is an array of { key, label, count? }.
 * activeKey is what the parent owns; chips emit `update:activeKey`.
 * "全部" / null chip resets directly (no toggle-off).
 *
 * Usage:
 *   <AdminToolbar
 *     v-model:searchValue="search"
 *     v-model:activeKey="statusFilter"
 *     :filters="STATUS_FILTERS"
 *     :count="filtered.length"
 *   />
 */
const props = defineProps({
  searchable:        { type: Boolean, default: true },
  searchValue:       { type: String,  default: "" },
  searchPlaceholder: { type: String,  default: "搜索…" },
  filters:           { type: Array,   default: () => [] },
  activeKey:         { default: null },
  count:             { type: Number,  default: null },
  countPrefix:       { type: String,  default: "共 " },
  countSuffix:       { type: String,  default: " 条" },
})

const emit = defineEmits(["update:searchValue", "update:activeKey"])

const _active = computed(() => props.activeKey)
function isActive(f) { return _active.value === f.key }
function onChipClick(f) { emit("update:activeKey", f.key) }
</script>

<style scoped>
.filter-count {
  font-variant-numeric: tabular-nums;
  font-weight: var(--fw-medium);
  color: inherit;
  opacity: 0.7;
}
.toolbar-right { display: inline-flex; align-items: center; gap: var(--sp-2); margin-left: auto; }
.toolbar-right + .admin-toolbar__count { margin-left: var(--sp-3); }
</style>
