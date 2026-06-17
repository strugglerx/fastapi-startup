import { getToken } from "../api/base.js"
import { useMenuStore } from "../stores/menu.js"

// 路由访问由 SysRoleMenu 授权决定（未授权 → 路由未注册 → 自然 404）。
// 路径白名单/admin-only 硬编码已退役；管理员侧栏显隐改由菜单字段 adminSidebarHidden 控制，
// 见 stores/menu.js 与菜单管理 UI。

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

    // /、/404 入口跳到当前用户第一个授权菜单
    if (to.path === "/" || to.path === "/404") {
      const fallback = firstAuthorizedPath(menu)
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
