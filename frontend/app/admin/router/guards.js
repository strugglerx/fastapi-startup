import { getToken, getCachedAdminProfile } from "../api/base.js"
import { useMenuStore } from "../stores/menu.js"

// 路径白名单——仅 admin / fixed 可访问；非 admin 命中时跳到他的第一个授权菜单
const ADMIN_ONLY_PATHS = new Set(["/dashboard"])

function isAdminUser() {
  const u = getCachedAdminProfile()
  if (!u) return false
  if (u.fixed) return true
  if (u.role === "admin") return true
  if (Array.isArray(u.permissions) && u.permissions.includes("*")) return true
  return false
}

function firstAuthorizedPath(menu, { excludeAdminOnly = false } = {}) {
  for (const m of menu.rawList.value) {
    if (m.component === "__group__") continue
    if (!m.path) continue
    if (excludeAdminOnly && ADMIN_ONLY_PATHS.has(m.path)) continue
    return m.path
  }
  return null
}

export function setupGuards(router) {
  router.beforeEach(async (to) => {
    if (!getToken()) {
      const hash = window.location.hash || "#/"
      window.location.assign("/login/?redirect=" + encodeURIComponent(hash))
      return false
    }

    const menu = useMenuStore()
    if (!menu.registered.value) {
      try {
        await menu.load()
        return { ...to, replace: true }
      } catch (error) {
        // menu.load 内部失败（如 401）由 fetch.js 拦截器统一跳登录，这里不再重定向到 /404，避免卡死
        console.error("[guards] menu load failed", error)
        menu.reset()
        return false
      }
    }

    const admin = isAdminUser()

    // 非 admin 撞到 admin-only 路径——跳"第一个非 admin-only 授权菜单"，
    // 没有就停在 /404，避免回到自己造成无限重定向
    if (ADMIN_ONLY_PATHS.has(to.path) && !admin) {
      const fallback = firstAuthorizedPath(menu, { excludeAdminOnly: true })
      if (!fallback) return to.path === "/404" ? true : { path: "/404" }
      return { path: fallback }
    }

    // /、/404 入口跳到当前用户第一个可访问菜单（admin 可走 admin-only，非 admin 必须跳过）
    if (to.path === "/" || to.path === "/404") {
      const fallback = firstAuthorizedPath(menu, { excludeAdminOnly: !admin })
      if (fallback && fallback !== to.path) {
        return { path: fallback }
      }
      // 没有可用菜单时停在 /404（如果不是 /404 才跳，避免 / → /404 → / 循环）
      if (!fallback && to.path !== "/404") return { path: "/404" }
    }

    if (to.matched.length === 0) return { path: "/404" }
    return true
  })
}
