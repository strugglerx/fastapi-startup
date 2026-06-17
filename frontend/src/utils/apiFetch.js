/**
 * Central fetch wrapper that automatically injects X-Admin-Token header.
 * The token is loaded from localStorage on first use so page refreshes work.
 */

const TOKEN_KEY = "smartai_admin_token"
let _token = ""

export function setGlobalAdminToken(token) {
  _token = token || ""
}

export function getGlobalAdminToken() {
  if (!_token) {
    // Hydrate from localStorage on first call after page load
    _token = localStorage.getItem(TOKEN_KEY) || ""
  }
  return _token
}

/**
 * Drop-in replacement for fetch() that injects the admin token.
 *
 * Extra options:
 *   authRedirect {boolean} – when true (default), a 401 that used a real
 *                            token clears the session and redirects to /login.
 *                            Pass false on public endpoints to avoid spurious
 *                            logouts.
 *   adminToken   {string}  – override the token for this single call.
 *                            Pass "" to intentionally make an unauthenticated
 *                            request without triggering the 401 redirect.
 */
export async function apiFetch(url, options = {}) {
  const { authRedirect = true, adminToken = getGlobalAdminToken(), ...fetchOptions } = options
  const headers = { ...(fetchOptions.headers || {}) }
  // 后端 deps 用 Header(alias="Token")
  if (adminToken && !headers["Token"]) {
    headers["Token"] = adminToken
  }

  const res = await fetch(url, { ...fetchOptions, headers })

  // Only clear session + redirect when we actually sent a token and it was
  // rejected (expired JWT).  Unauthenticated calls returning 401 are normal.
  if (authRedirect && res.status === 401 && adminToken) {
    setGlobalAdminToken("")
    localStorage.removeItem(TOKEN_KEY)
    if (!window.location.pathname.startsWith("/login")) {
      // Preserve the full current URL (path + search + hash) so we can return after re-login.
      // Previously only hash was preserved, which broke history-mode routes like /admin/storage?tab=s3.
      const currentPath =
        window.location.pathname + window.location.search + window.location.hash
      window.location.replace(
        "/login" +
          (currentPath && currentPath !== "/" ? "?redirect=" + encodeURIComponent(currentPath) : ""),
      )
    }
  }

  return res
}
