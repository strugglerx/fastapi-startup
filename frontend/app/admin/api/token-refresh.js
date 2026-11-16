/**
 * token-refresh.js —— access + refresh 双 token 自动续期
 *
 * fetch.js 的 request 拦截器会在每次请求前 `await maybeRefreshToken(url)`。
 * 本模块按以下优先级处理：
 *
 *   1. access 剩余 > 10 分钟 → 不动
 *   2. access 剩余 0 ~ 10 分钟（即将过期）→ 后台调 /api/v1/auth/refresh
 *      用旧 access 滑动换发新对（兼容老路径）
 *   3. access 已过期 / 不存在 / 非 JWT，且本地有 refresh →
 *      调 /api/v1/auth/refresh-token 用 refresh 换发新对（rotate，旧 refresh 吊销）
 *   4. 上述都失败：什么都不做，让原请求带旧/无 token 走，401 由
 *      fetch.js 的 logoutAndRedirect 兜底（清本地 + 跳登录）
 *
 * 并发用 `_refreshing` 单例 Promise 串行化，多个 tab / 并发请求只刷一次。
 */
import axios from "axios"
import { getToken, setToken, getRefreshToken, setRefreshToken, clearRefreshToken } from "./base.js"

const REFRESH_WINDOW_MS = 10 * 60 * 1000           // access 临近过期阈值
const REFRESH_URL       = "/api/v1/auth/refresh"          // 老路径：access 滑动
const REFRESH_TOKEN_URL = "/api/v1/auth/refresh-token"    // 新路径：refresh 换发

let _refreshing = null  // in-flight Promise（任意一种都共用）

function _parseJwtExpMs(token) {
  if (!token || typeof token !== "string") return null
  const parts = token.split(".")
  if (parts.length !== 3) return null
  try {
    const payload = parts[1].replace(/-/g, "+").replace(/_/g, "/")
    const padded = payload + "===".slice((payload.length + 3) % 4)
    const json = JSON.parse(atob(padded))
    if (typeof json.exp !== "number") return null
    return json.exp * 1000
  } catch {
    return null
  }
}

/** 当前 access token 剩余毫秒数；无 token / 解析失败返回 null */
export function tokenRemainingMs() {
  const token = getToken()
  const expMs = _parseJwtExpMs(token)
  if (expMs == null) return null
  return expMs - Date.now()
}

/** 写入服务端返回的 token 对（兼容多种字段命名）。 */
function _persistTokens(data) {
  if (!data) return false
  const access = data.access_token || data.token
  const refresh = data.refresh_token
  if (access) setToken(access)
  if (refresh) setRefreshToken(refresh)
  return !!access
}

/** access 仍有效（剩余 0~10min）→ 后台滑动续期 */
async function _slideAccessToken() {
  const token = getToken()
  if (!token) return
  try {
    const res = await axios.post(
      REFRESH_URL,
      null,
      { headers: { Authorization: `Bearer ${token}` }, timeout: 10000 },
    )
    const body = res?.data || {}
    _persistTokens(body.data || body)
  } catch (e) {
    console.debug("[token-refresh] slide failed:", e?.message || e)
  }
}

/** access 已过期 → 用 refresh_token rotate 换发新对 */
async function _rotateWithRefreshToken() {
  const refresh = getRefreshToken()
  if (!refresh) return
  try {
    const res = await axios.post(
      REFRESH_TOKEN_URL,
      { refresh_token: refresh },
      { timeout: 10000 },
    )
    const body = res?.data || {}
    const data = body.data || body
    const ok = _persistTokens(data)
    if (!ok) {
      // 后端非预期 schema：清掉 refresh 避免反复尝试
      clearRefreshToken()
    }
  } catch (e) {
    // refresh 过期 / 吊销 / 无效 → 401，直接清掉避免循环 rotate
    if (e?.response?.status === 401) {
      clearRefreshToken()
    }
    console.debug("[token-refresh] rotate failed:", e?.message || e)
  }
}

/**
 * 主动刷新：在每次业务请求前调用。任何失败都静默 —— 让原请求继续走，
 * 走到 401 由 fetch.js 的 logoutAndRedirect 兜底清+跳登录。
 *
 * @param {string} [requestUrl] 当前请求 URL；refresh 自身被排除，避免递归
 * @returns {Promise<void>}
 */
export async function maybeRefreshToken(requestUrl) {
  if (requestUrl && (requestUrl.includes(REFRESH_URL) || requestUrl.includes(REFRESH_TOKEN_URL))) {
    return
  }

  if (_refreshing) {
    await _refreshing
    return
  }

  const remaining = tokenRemainingMs()

  // access 还很活 → 不动
  if (remaining != null && remaining > REFRESH_WINDOW_MS) return

  // access 已过期 / 不存在 → 走 refresh 换发
  if (remaining == null || remaining <= 0) {
    if (!getRefreshToken()) return  // 没 refresh 也没办法，等 401 兜底
    _refreshing = _rotateWithRefreshToken().finally(() => { _refreshing = null })
    await _refreshing
    return
  }

  // access 临近过期 → 滑动续期
  _refreshing = _slideAccessToken().finally(() => { _refreshing = null })
  await _refreshing
}
