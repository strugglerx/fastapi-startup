/**
 * base.js —— token / 缓存用户资料 / 跳登录的统一管理（localStorage）
 *
 * 参考 miniapp-rebuild/admin-frontend/src/utils/base.js，做了三处适配：
 *   1. sessionStorage → localStorage  (关 tab 不丢登录，体验更好)
 *   2. key 改成 smartai_admin_*       (跟 LoginCard.vue / apiFetch.js 现有约定一致)
 *   3. 去掉 wx miniprogram 分支       (我们只跑 Web)
 */
import { debounce } from "lodash-es"

const TOKEN_KEY    = "smartai_admin_token"
const USER_KEY     = "smartai_admin_user"
const REMEMBER_KEY = "smartai_admin_remember"
const ROLE_KEY     = "smartai_admin_active_role"

function _read(key, fallback = "") {
  try { return localStorage.getItem(key) || fallback } catch { return fallback }
}
function _write(key, value) {
  try { localStorage.setItem(key, value) } catch {}
}
function _remove(...keys) {
  keys.forEach((k) => { try { localStorage.removeItem(k) } catch {} })
}
function _readJson(key, fallback) {
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) : fallback
  } catch { return fallback }
}
function _writeJson(key, value) {
  _write(key, JSON.stringify(value ?? null))
}

// ── Token ──────────────────────────────────────────────────────
export const getToken    = () => _read(TOKEN_KEY)
export const setToken    = (t) => _write(TOKEN_KEY, t || "")
export const clearToken  = () => _remove(TOKEN_KEY)

// ── 缓存的当前用户资料 ─────────────────────────────────────────
export const getCachedAdminProfile = () => _readJson(USER_KEY, null)
export const setCachedAdminProfile = (u) => _writeJson(USER_KEY, u || null)
export const clearCachedAdminProfile = () => _remove(USER_KEY)

// ── 多角色管理员切换（可选；当前 admin/member 两角色，先留接口） ──
export const getAdminActiveRole = () => _read(ROLE_KEY) || ""
export const setAdminActiveRole = (r) => _write(ROLE_KEY, r || "")
export const clearAdminActiveRole = () => _remove(ROLE_KEY)

// ── 记住我（登录页用） ─────────────────────────────────────────
export const getRememberMe = () => _readJson(REMEMBER_KEY, null)
export const setRememberMe = (v) => _writeJson(REMEMBER_KEY, v)
export const clearRememberMe = () => _remove(REMEMBER_KEY)

// ── 跳登录 ─────────────────────────────────────────────────────
function _toLogin(querys) {
  const tail = querys ? "?" + new URLSearchParams(querys).toString() : ""
  window.location.assign("/login" + tail)
}
export const toLogin = debounce(_toLogin, 200)

// ── 退出（清状态 + 跳登录）─────────────────────────────────────
export function logoutAndRedirect(querys) {
  _remove(TOKEN_KEY, USER_KEY, ROLE_KEY)
  toLogin(querys)
}
