<template>
  <div class="profile-view">
    <n-spin :show="loading">
      <div class="profile-container">
        <!-- ── 顶部用户卡 ─────────────────────────────── -->
        <div class="profile-hero">
          <div class="profile-avatar">{{ avatarText }}</div>
          <div class="profile-hero-info">
            <div class="profile-hero-name">{{ user.full_name || user.username || "—" }}</div>
            <div class="profile-hero-email">{{ user.email || "—" }}</div>
            <div class="profile-hero-tags">
              <n-tag size="small" :type="roleTagType" round>{{ user.role || "—" }}</n-tag>
              <n-tag size="small" :type="user.is_active ? 'success' : 'error'" round>
                {{ user.is_active ? "启用" : "禁用" }}
              </n-tag>
              <n-tag v-if="user.fixed" size="small" type="warning" round>种子账号</n-tag>
            </div>
          </div>
        </div>

        <!-- ── 基本信息 ───────────────────────────────── -->
        <section class="profile-section">
          <h3 class="profile-section-title">基本信息</h3>
          <div class="profile-grid">
            <div class="profile-field">
              <span class="profile-field__label">用户名</span>
              <span class="profile-field__value">{{ user.username || "—" }}</span>
            </div>
            <div class="profile-field">
              <span class="profile-field__label">显示名</span>
              <span class="profile-field__value">{{ user.full_name || "—" }}</span>
            </div>
            <div class="profile-field">
              <span class="profile-field__label">邮箱</span>
              <span class="profile-field__value">{{ user.email || "—" }}</span>
            </div>
            <div class="profile-field">
              <span class="profile-field__label">角色权限</span>
              <span class="profile-field__value">{{ user.role || "—" }}</span>
            </div>
          </div>
        </section>

        <!-- ── 登录与时间 ─────────────────────────────── -->
        <section class="profile-section">
          <h3 class="profile-section-title">登录与时间</h3>
          <div class="profile-grid">
            <div class="profile-field">
              <span class="profile-field__label">最后登录时间</span>
              <span class="profile-field__value">{{ formatTime(user.last_login_at || user.last_login) }}</span>
            </div>
            <div class="profile-field">
              <span class="profile-field__label">账号注册时间</span>
              <span class="profile-field__value">{{ formatTime(user.created_at) }}</span>
            </div>
            <div class="profile-field">
              <span class="profile-field__label">账号唯一 ID</span>
              <span class="profile-field__value profile-field__value--mono">#{{ user.id || "—" }}</span>
            </div>
            <div class="profile-field">
              <span class="profile-field__label">当前状态</span>
              <span class="profile-field__value">{{ user.is_active ? "启用" : "禁用" }}</span>
            </div>
          </div>
        </section>
      </div>
    </n-spin>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue"
import { NSpin, NTag, useMessage } from "naive-ui"
import { http } from "../api/http.js"

defineOptions({ name: "Profile" })

const emit = defineEmits(["close"])
const message = useMessage()
const loading = ref(false)
const user = ref({})

onMounted(loadMe)

const avatarText = computed(() => {
  const src = user.value.full_name || user.value.username || user.value.email || ""
  return src.trim().charAt(0).toUpperCase() || "U"
})

const roleTagType = computed(() => (user.value.role === "admin" ? "info" : "default"))

function formatTime(value) {
  if (!value) return "—"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString("zh-CN", { hour12: false })
}

async function loadMe() {
  loading.value = true
  try {
    const res = await http.get("/api/v1/auth/me")
    user.value = res.data?.data ?? res.data ?? {}
  } catch {
    message.error("加载用户信息失败")
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.profile-view {
  width: 100%;
}

.profile-container {
  display: flex;
  flex-direction: column;
  gap: var(--sp-4);
}

.profile-hero {
  display: flex;
  align-items: center;
  gap: var(--sp-4);
  padding: var(--sp-4) var(--sp-5);
  background: linear-gradient(135deg, var(--c-surface-sunken) 0%, var(--c-surface) 100%);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
}

.profile-avatar {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--c-primary, #6366f1);
  color: #fff;
  font-size: 20px;
  font-weight: var(--fw-bold);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.profile-hero-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
}

.profile-hero-name {
  font-size: var(--fs-lg);
  font-weight: var(--fw-bold);
  color: var(--c-text-primary);
  line-height: 1.2;
}

.profile-hero-email {
  font-size: var(--fs-sm);
  color: var(--c-text-muted);
}

.profile-hero-tags {
  display: flex;
  gap: var(--sp-2);
  margin-top: var(--sp-1);
  flex-wrap: wrap;
}

.profile-section {
  background: var(--c-surface);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  padding: var(--sp-4) var(--sp-5);
}

.profile-section-title {
  font-size: var(--fs-sm);
  font-weight: var(--fw-bold);
  color: var(--c-text-secondary);
  margin: 0 0 var(--sp-3);
  letter-spacing: 0.02em;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--sp-3) var(--sp-5);
}

.profile-field {
  display: flex;
  flex-direction: column;
  gap: var(--sp-1);
  min-width: 0;
}

.profile-field__label {
  font-size: var(--fs-xs);
  color: var(--c-text-muted);
}

.profile-field__value {
  font-size: var(--fs-base);
  color: var(--c-text-primary);
  font-weight: var(--fw-medium);
  word-break: break-all;
}

.profile-field__value--mono {
  font-family: var(--ff-mono, monospace);
  font-size: var(--fs-sm);
  color: var(--c-text-secondary);
}

@media (max-width: 480px) {
  .profile-grid {
    grid-template-columns: 1fr;
    gap: var(--sp-3);
  }
}
</style>
