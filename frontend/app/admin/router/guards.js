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

function firstAuthorizedPath(menu) {
  const item = menu.rawList.value.find((m) => m.component !== "__group__" && m.path)
  return item ? item.path : null
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

    // 非 admin 不允许进 admin-only 路径
    if (ADMIN_ONLY_PATHS.has(to.path) && !isAdminUser()) {
      const fallback = firstAuthorizedPath(menu)
      return fallback ? { path: fallback } : { path: "/404" }
    }

    // /、/404 入口跳到当前用户第一个授权菜单（admin 通常是 dashboard）
    if (to.path === "/" || to.path === "/404") {
      const fallback = firstAuthorizedPath(menu)
      if (fallback && fallback !== to.path) {
        return { path: fallback }
      }
    }

    if (to.matched.length === 0) return { path: "/404" }
    return true
  })
}
