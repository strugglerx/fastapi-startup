/**
 * token-refresh.js —— Token 临近过期时主动续期
 *
 * 策略：fetch.js 的 request 拦截器在每次请求前调用 maybeRefreshToken()
 *   - 若当前 token 剩余 > 10 分钟：不动
 *   - 若剩余 ≤ 10 分钟且 > 0：在后台调一次 /api/v1/auth/refresh 换发新 token
 *   - 若已过期：不刷新，让原请求拿到 401 触发 toLogin
 *   - 并发请求共用同一个 in-flight Promise，避免 N 次 refresh
 */
import axios from "axios"
import { getToken, setToken } from "./base.js"

const REFRESH_WINDOW_MS = 10 * 60 * 1000   // 临近过期阈值：10 分钟
const REFRESH_URL = "/api/v1/auth/refresh"

let _refreshing = null  // in-flight Promise，串行化并发调用

function _parseJwtExpMs(token) {
  if (!token || typeof token !== "string") return null
  const parts = token.split(".")
  if (parts.length !== 3) return null
  try {
    // base64url → base64
    const payload = parts[1].replace(/-/g, "+").replace(/_/g, "/")
    const padded = payload + "===".slice((payload.length + 3) % 4)
    const json = JSON.parse(atob(padded))
    if (typeof json.exp !== "number") return null
    return json.exp * 1000
  } catch {
    return null
  }
}

/** 当前 token 剩余毫秒数；无 token / 解析失败返回 null */
export function tokenRemainingMs() {
  const token = getToken()
  const expMs = _parseJwtExpMs(token)
  if (expMs == null) return null
  return expMs - Date.now()
}

/**
 * 主动刷新：如果临近过期且未过期，调一次 /auth/refresh 换 token。
 * 不抛错；任何失败都静默——原请求继续走拦截器，401 由现有机制兜底。
 *
 * @param {string} [requestUrl] 当前请求 URL；若是 refresh 接口本身则跳过避免递归
 * @returns {Promise<void>}
 */
export async function maybeRefreshToken(requestUrl) {
  if (requestUrl && requestUrl.includes(REFRESH_URL)) return
  const remaining = tokenRemainingMs()
  if (remaining == null) return       // 无 token 或非 JWT 格式（兜底）
  if (remaining <= 0) return          // 已过期：让原请求拿 401，触发 toLogin
  if (remaining > REFRESH_WINDOW_MS) return  // 还远没到期

  if (!_refreshing) {
    _refreshing = (async () => {
      try {
        const token = getToken()
        if (!token) return
        // 不走 default request 实例——避免该拦截器再触发自己
        const res = await axios.post(
          REFRESH_URL,
          null,
          { headers: { Token: token }, timeout: 10000 },
        )
        const body = res?.data || {}
        const data = body.data || body
        const next = data?.token || data?.access_token
        if (next) setToken(next)
      } catch (e) {
        // 静默：原请求会带旧 token 继续，401 时拦截器会跳登录
        console.debug("[token-refresh] failed:", e?.message || e)
      } finally {
        _refreshing = null
      }
    })()
  }
  await _refreshing
}
