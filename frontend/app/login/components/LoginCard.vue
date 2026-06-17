<template>
  <div class="login-container">
    <div class="glass-card login-card" ref="loginCard">
      <div class="card-header">
        <h1 class="login-title">登录智慧AI探索平台</h1>
        <p class="login-subtitle">
          欢迎回来，进入你的 AI 工作台与探索空间。
        </p>
      </div>

      <form v-if="mode === 'login'" class="promax-form" @submit.prevent="handleLogin" novalidate>
        <div class="form-item">
          <label>邮箱或账号</label>
          <input v-model="username" type="text" placeholder="输入邮箱或账号" required :disabled="loading" />
        </div>

        <div class="form-item">
          <div class="label-row">
            <label>密码</label>
            <a href="#" class="forgot-link" @click.prevent="enterForgotMode">忘记密码？</a>
          </div>
          <div class="input-with-icon">
            <input v-model="password" :type="showPwd ? 'text' : 'password'" placeholder="••••••••" required :disabled="loading" />
            <button type="button" class="icon-btn" @click="showPwd = !showPwd">
              <svg v-if="showPwd" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><line x1="1" y1="1" x2="23" y2="23" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
              <svg v-else viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="12" r="3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
            </button>
          </div>
        </div>

        <div class="form-item checkbox-item">
          <label class="promax-checkbox">
            <input type="checkbox" v-model="rememberMe" />
            <span class="box">
              <svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="3" fill="none"><polyline points="20 6 9 17 4 12"/></svg>
            </span>
            <span class="text">记住我 30 天</span>
          </label>
        </div>

        <Transition name="fade">
          <div v-if="errorMsg" class="alert error">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            {{ errorMsg }}
          </div>
        </Transition>

        <Transition name="fade">
          <div v-if="successMsg" class="alert success">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            {{ successMsg }}
          </div>
        </Transition>

        <button type="submit" class="promax-btn primary" :disabled="loading || !canSubmit">
          <span v-if="loading" class="spinner"></span>
          <span>{{ loading ? '验证中...' : '登 录' }}</span>
          <svg v-if="!loading" viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" stroke-width="2" class="btn-arrow"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
        </button>
      </form>

      <!-- 忘记密码：第 1 步——发送邮箱验证码 -->
      <form v-else-if="mode === 'forgot-send'" class="promax-form" @submit.prevent="handleSendCode" novalidate>
        <div class="form-item">
          <label>邮箱</label>
          <input v-model="forgotEmail" type="email" placeholder="输入注册邮箱" required :disabled="loading" autocomplete="email" />
        </div>

        <p class="hint-text">系统将向你的注册邮箱发送 6 位验证码（10 分钟内有效）。</p>

        <Transition name="fade">
          <div v-if="errorMsg" class="alert error">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            {{ errorMsg }}
          </div>
        </Transition>

        <button type="submit" class="promax-btn primary" :disabled="loading || !forgotEmail">
          <span v-if="loading" class="spinner"></span>
          <span>{{ loading ? '发送中...' : '发送验证码' }}</span>
        </button>
        <button type="button" class="link-btn" @click="exitForgotMode">返回登录</button>
      </form>

      <!-- 忘记密码：第 2 步——输入验证码 + 新密码 -->
      <form v-else-if="mode === 'forgot-reset'" class="promax-form" @submit.prevent="handleResetPassword" novalidate>
        <div class="form-item">
          <label>邮箱</label>
          <input :value="forgotEmail" type="email" disabled />
        </div>
        <div class="form-item">
          <label>验证码</label>
          <input v-model="forgotCode" type="text" maxlength="6" inputmode="numeric" placeholder="6 位验证码" required :disabled="loading" />
        </div>
        <div class="form-item">
          <label>新密码</label>
          <input v-model="forgotNewPwd" type="password" placeholder="至少 8 位，含字母+数字" required :disabled="loading" autocomplete="new-password" />
          <p class="hint-text">密码长度 ≥ 8 位，必须包含至少 1 个字母 + 1 个数字。</p>
        </div>

        <Transition name="fade">
          <div v-if="errorMsg" class="alert error">
            <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" fill="none" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
            {{ errorMsg }}
          </div>
        </Transition>

        <button type="submit" class="promax-btn primary" :disabled="loading || !forgotCode || !forgotNewPwd">
          <span v-if="loading" class="spinner"></span>
          <span>{{ loading ? '提交中...' : '重置密码' }}</span>
        </button>
        <button type="button" class="link-btn" @click="exitForgotMode">返回登录</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from "vue"
import gsap from "gsap"

const TOKEN_KEY = "smartai_admin_token"
const USER_KEY  = "smartai_admin_user"
const REMEMBER_KEY = "smartai_admin_remember"

const username = ref("")
const password = ref("")
const showPwd  = ref(false)
const rememberMe = ref(false)
const loading  = ref(false)
const errorMsg = ref("")
const successMsg = ref("")
const loginCard = ref(null)

// "login" | "forgot-send" | "forgot-reset"
const mode = ref("login")
const forgotEmail  = ref("")
const forgotCode   = ref("")
const forgotNewPwd = ref("")

function enterForgotMode() {
  errorMsg.value = ""
  successMsg.value = ""
  // 把当前登录输入的内容当成邮箱预填，免得用户重输
  forgotEmail.value = username.value.trim()
  forgotCode.value = ""
  forgotNewPwd.value = ""
  mode.value = "forgot-send"
}

function exitForgotMode() {
  errorMsg.value = ""
  mode.value = "login"
}

async function _post(path, body) {
  const res = await fetch(path, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(body),
  })
  const json = await res.json().catch(() => ({}))
  if (!res.ok || (json && json.code && json.code !== 0)) {
    const msg = json?.msg || json?.detail || `请求失败 (${res.status})`
    return { __error: true, msg, status: res.status }
  }
  return _unwrap(json)
}

async function handleSendCode() {
  if (!forgotEmail.value) return
  errorMsg.value = ""
  loading.value = true
  try {
    const r = await _post("/api/v1/auth/forgot-password", { email: forgotEmail.value.trim() })
    if (r?.__error) {
      errorMsg.value = r.msg
      return
    }
    mode.value = "forgot-reset"
  } catch {
    errorMsg.value = "网络异常，请稍后再试。"
  } finally {
    loading.value = false
  }
}

async function handleResetPassword() {
  errorMsg.value = ""
  loading.value = true
  try {
    const r = await _post("/api/v1/auth/reset-password", {
      email: forgotEmail.value.trim(),
      code: forgotCode.value.trim(),
      new_password: forgotNewPwd.value,
    })
    if (r?.__error) {
      errorMsg.value = r.msg
      return
    }
    // 重置成功——回登录页 + 提示
    mode.value = "login"
    successMsg.value = "密码已重置，请用新密码登录。"
    password.value = ""
    forgotCode.value = ""
    forgotNewPwd.value = ""
  } catch {
    errorMsg.value = "网络异常，请稍后再试。"
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  const saved = localStorage.getItem(REMEMBER_KEY)
  if (saved) {
    try {
      const data = JSON.parse(saved)
      if (data.username) username.value = data.username
      if (data.password) password.value = data.password
      rememberMe.value = data.remember
    } catch (e) {}
  }

  if (!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
    gsap.fromTo(loginCard.value,
      { opacity: 0, y: 18, scale: 0.99 },
      { opacity: 1, y: 0, scale: 1, duration: 0.65, ease: "power3.out", delay: 0.05 }
    )
  }
})

const canSubmit = computed(() => {
  return !!username.value.trim() && !!password.value
})

function normalizeRedirect(value) {
  if (!value) return "/#/"
  if (value.startsWith("#")) return "/" + value
  if (value.startsWith("/#")) return value
  return "/#/"
}

const redirectTo = normalizeRedirect(new URLSearchParams(window.location.search).get("redirect"))

function _unwrap(j) {
  if (j && typeof j === "object" && j.code === 0 && "data" in j) return j.data
  return j
}

async function _tryV1Login(identifier, pwd) {
  const res = await fetch("/api/v1/auth/login", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({ email: identifier, password: pwd }),
  })
  if (!res.ok) {
    if (res.status === 429 || res.status === 403) {
      const body = await res.json().catch(() => ({}))
      const msg = body?.msg || body?.detail || (res.status === 429 ? "登录尝试过多，请稍后再试" : "账号已停用")
      return { __error: true, msg }
    }
    return null
  }
  return _unwrap(await res.json())
}

async function _tryLegacyLogin(identifier, pwd) {
  const res = await fetch("/api/auth/login", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({
      username: identifier.trim().toLowerCase(),
      password: pwd,
    }),
  })
  if (!res.ok) return null
  return await res.json()
}

async function handleLogin() {
  if (!canSubmit.value) return
  loading.value  = true
  errorMsg.value = ""

  try {
    const id = username.value.trim()
    let payload = await _tryV1Login(id, password.value)
    if (payload?.__error) {
      errorMsg.value = payload.msg
      password.value = ""
      return
    }
    if (!payload) payload = await _tryLegacyLogin(id, password.value)

    if (!payload) {
      errorMsg.value = "邮箱或密码错误。"
      password.value = ""
      return
    }

    localStorage.setItem(TOKEN_KEY, payload.token)
    if (payload.user) {
      localStorage.setItem(USER_KEY, JSON.stringify(payload.user))
    } else {
      localStorage.removeItem(USER_KEY)
    }

    if (rememberMe.value) {
      localStorage.setItem(REMEMBER_KEY, JSON.stringify({
        username: username.value,
        password: password.value,
        remember: true
      }))
    } else {
      localStorage.removeItem(REMEMBER_KEY)
    }

    window.location.assign(redirectTo)
  } catch {
    errorMsg.value = "网络异常，请稍后再试。"
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
@media (min-width: 1024px) {
  .login-container {
    flex: none;
    width: 50vw;
  }
}

.glass-card {
  position: relative;
  background: rgba(16, 16, 18, 0.88);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 18px;
  width: 100%;
  max-width: 440px;
  padding: 48px;
  box-shadow: 0 24px 56px rgba(0, 0, 0, 0.42), inset 0 1px 0 rgba(255,255,255,0.08);
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.glass-card:hover {
  transform: translateY(-6px);
  border-color: rgba(167, 139, 250, 0.3);
  box-shadow: 
    0 32px 72px rgba(0, 0, 0, 0.8), 
    inset 0 1px 0 rgba(255,255,255,0.3), 
    0 0 60px rgba(139, 92, 246, 0.4), 
    0 0 100px rgba(52, 211, 153, 0.15);
}

.card-header {
  margin-bottom: 40px;
  text-align: center;
}
.login-title {
  font-size: 24px;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin-bottom: 8px;
}
.login-subtitle {
  font-size: 14px;
  color: #A1A1AA;
}

/* Form Styles */
.promax-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.form-item label {
  font-size: 13px;
  font-weight: 500;
  color: #A1A1AA;
}
.forgot-link {
  font-size: 13px;
  color: #A1A1AA;
  text-decoration: none;
  transition: color 0.2s;
}
.forgot-link:hover {
  color: #FFFFFF;
}

.form-item input[type="text"],
.form-item input[type="password"] {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px 16px;
  font-size: 14px;
  color: #FFFFFF;
  font-family: inherit;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.form-item input::placeholder {
  color: rgba(255, 255, 255, 0.2);
}
.form-item input:focus {
  outline: none;
  border-color: #A78BFA;
  box-shadow: 0 0 0 4px rgba(167, 139, 250, 0.25), 0 0 30px rgba(167, 139, 250, 0.45);
  background: rgba(0, 0, 0, 0.6);
  transform: scale(1.01);
}

.input-with-icon {
  position: relative;
  display: flex;
  align-items: center;
}
.input-with-icon input {
  width: 100%;
  padding-right: 40px;
}
.icon-btn {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  color: #A1A1AA;
  cursor: pointer;
  display: flex;
  padding: 4px;
  transition: color 0.2s;
}
.icon-btn:hover {
  color: #FFFFFF;
}

/* Custom Checkbox */
.checkbox-item {
  margin-top: -4px;
}
.promax-checkbox {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}
.promax-checkbox input { display: none; }
.promax-checkbox .box {
  width: 16px;
  height: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.2);
  transition: all 0.2s;
}
.promax-checkbox .box svg {
  opacity: 0;
  transform: scale(0.5);
  transition: all 0.2s;
  color: #000000;
}
.promax-checkbox input:checked ~ .box {
  background: #FFFFFF;
  border-color: #FFFFFF;
}
.promax-checkbox input:checked ~ .box svg {
  opacity: 1;
  transform: scale(1);
}
.promax-checkbox .text {
  font-size: 13px;
  color: #A1A1AA;
  font-weight: 500;
}

/* Alerts */
.alert {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
}
.alert.error {
  background: rgba(239, 68, 68, 0.1);
  color: #F87171;
  border: 1px solid rgba(239, 68, 68, 0.2);
}
.alert.success {
  background: rgba(16, 185, 129, 0.1);
  color: #34D399;
  border: 1px solid rgba(16, 185, 129, 0.2);
}
.alert.info {
  background: rgba(96, 165, 250, 0.1);
  color: #93C5FD;
  border: 1px solid rgba(96, 165, 250, 0.2);
}

/* Buttons */
.promax-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: 8px;
}
.promax-btn.primary {
  position: relative;
  overflow: hidden;
  background: #FFFFFF;
  color: #000000;
  border: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 14px rgba(0,0,0,0.2);
}
.promax-btn.primary::after {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 50%; height: 100%;
  background: linear-gradient(to right, transparent, rgba(167, 139, 250, 0.6), transparent);
  transform: skewX(-20deg);
  pointer-events: none;
}
.promax-btn.primary:hover:not(:disabled) {
  background: #FFFFFF;
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 10px 30px rgba(255, 255, 255, 0.5), 0 0 20px rgba(167, 139, 250, 0.8);
}
.promax-btn.primary:hover:not(:disabled)::after {
  left: 200%;
  transition: left 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}
.promax-btn:active:not(:disabled) {
  transform: scale(0.96);
}
.promax-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-arrow {
  transition: transform 0.2s;
}
.promax-btn:hover .btn-arrow {
  transform: translateX(4px);
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(0,0,0,0.1);
  border-top-color: #000;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.hint-text {
  font-size: 12px;
  color: #A1A1AA;
  margin: 4px 0 0;
  line-height: 1.5;
}

.link-btn {
  background: none;
  border: none;
  color: #A1A1AA;
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  padding: 4px;
  margin: 0 auto;
  transition: color 0.2s;
}
.link-btn:hover {
  color: #FFFFFF;
}

@media (max-width: 768px) {
  .glass-card { padding: 32px 24px; border-radius: 16px; }
}
</style>
