<template>
  <div class="admin-page">
    <AdminPageHeader title="系统设置" subtitle="管理和同步平台底层菜单、权限及系统级运维功能" />

    <div class="admin-card settings-card">
      <div class="admin-card__eyebrow">数据运维</div>
      <h2 class="admin-card__title">菜单数据同步</h2>
      <p class="settings-card-desc">
        将代码中定义的页面字段同步到 sys_menu。标题、图标、父级、排序和隐藏状态不会被代码覆盖，请在“菜单管理”中维护。
      </p>

      <div class="stats-row">
        <div class="stat-box">
          <span class="stat-box__title">已注册菜单</span>
          <span class="stat-box__value">{{ menuStats.total }}</span>
        </div>
        <div class="stat-box">
          <span class="stat-box__title">隐藏/白名单</span>
          <span class="stat-box__value">{{ menuStats.hidden }}</span>
        </div>
        <div class="stat-box stat-box--warning">
          <span class="stat-box__title">已禁用菜单</span>
          <span class="stat-box__value">{{ menuStats.disabled }}</span>
        </div>
      </div>

      <div class="sync-status">
        <div class="sync-status__item">
          <span class="status-label">当前运行环境：</span>
          <span class="admin-code-chip">{{ envName }}</span>
        </div>
        <div class="sync-status__item">
          <span class="status-label">上次同步时间：</span>
          <span class="status-value">{{ lastSyncText }}</span>
        </div>
      </div>

      <div class="card-actions">
        <n-button type="primary" :loading="syncing" class="sync-btn" @click="syncCurrentMenus">
          同步当前代码到菜单库
        </n-button>

        <transition name="fade">
          <div v-if="syncResult" class="sync-result-alert">
            <span class="alert-icon">✓</span>
            <span class="alert-text">
              同步完成！新增 <strong>{{ syncResult.added }}</strong> 项 / 更新
              <strong>{{ syncResult.updated }}</strong> 项 / 禁用
              <strong>{{ syncResult.disabled }}</strong> 项。刷新页面后侧边栏将同步反映。
            </span>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue"
import { NButton, useMessage } from "naive-ui"
import { fetchMenuList, syncMenus } from "../../../api/menu.js"
import AdminPageHeader from "../../../components/AdminPageHeader.vue"
import { getLocalPages } from "../../../shared/page-registry.js"

defineOptions({ name: "SystemSettings" })

const message = useMessage()
const syncing = ref(false)
const lastSyncAt = ref(null)
const syncResult = ref(null)
const menuStats = reactive({ total: 0, hidden: 0, disabled: 0 })

const envName = computed(() =>
  import.meta.env.MODE === "development" ? "开发环境 (development)" : "生产环境 (production)",
)

const lastSyncText = computed(() => formatTime(lastSyncAt.value) || "暂无记录")

onMounted(loadMenuStats)

async function loadMenuStats() {
  const rows = await fetchMenuList({ include_disabled: true })
  menuStats.total = rows.length
  menuStats.hidden = rows.filter((item) => item.hidden).length
  menuStats.disabled = rows.filter((item) => item.enabled === false).length
}

async function syncCurrentMenus() {
  syncing.value = true
  syncResult.value = null
  try {
    const result = await syncMenus(getLocalPages())
    syncResult.value = {
      added: result.added || 0,
      updated: result.updated || 0,
      disabled: result.disabled || 0,
    }
    lastSyncAt.value = new Date().toISOString()
    await loadMenuStats()
    message.success(`菜单同步成功：新增 ${syncResult.value.added} / 更新 ${syncResult.value.updated} / 禁用 ${syncResult.value.disabled}`)
  } catch (error) {
    message.error(error?.response?.data?.msg || error?.message || "同步菜单失败")
  } finally {
    syncing.value = false
  }
}

function formatTime(value) {
  if (!value) return ""
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString("zh-CN", { hour12: false })
}
</script>

<style scoped>
.admin-page {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.settings-card {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.settings-card-desc {
  font-size: var(--fs-base);
  line-height: var(--lh-loose);
  color: var(--c-text-secondary);
  margin: 0;
  max-width: 840px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: var(--sp-3);
  margin: var(--sp-2) 0;
}

.stat-box {
  background: var(--c-surface-sunken);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  padding: var(--sp-4);
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.stat-box--warning {
  border-left: 3px solid var(--c-warning-dot);
}

.stat-box__title {
  font-size: var(--fs-sm);
  color: var(--c-text-muted);
}

.stat-box__value {
  font-size: 24px;
  font-weight: var(--fw-bold);
  color: var(--c-text-primary);
  font-variant-numeric: tabular-nums;
  line-height: 1;
}

.sync-status {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-6);
  padding: var(--sp-3) var(--sp-4);
  background: var(--c-surface-sunken);
  border-radius: var(--r-md);
  border: 1px solid var(--c-border);
}

.sync-status__item {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
  font-size: var(--fs-base);
}

.status-label {
  color: var(--c-text-muted);
}

.status-value {
  color: var(--c-text-secondary);
  font-weight: var(--fw-medium);
}

.card-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--sp-3);
  margin-top: var(--sp-2);
}

.sync-btn {
  font-weight: var(--fw-semibold);
}

.sync-result-alert {
  display: flex;
  align-items: flex-start;
  gap: var(--sp-3);
  background-color: var(--c-success-bg);
  border: 1px solid var(--c-success-border);
  border-radius: var(--r-md);
  padding: var(--sp-3) var(--sp-4);
  color: var(--c-success-text);
  font-size: var(--fs-base);
  line-height: var(--lh-base);
  width: 100%;
  box-sizing: border-box;
}

.alert-icon {
  font-weight: var(--fw-bold);
  font-size: 16px;
  line-height: 1;
}

.alert-text strong {
  font-weight: var(--fw-bold);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--motion-base) var(--ease-out);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
