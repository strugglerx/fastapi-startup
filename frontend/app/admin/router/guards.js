import { getToken } from "../api/base.js"
import { useMenuStore } from "../stores/menu.js"

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

    if (to.path === "/" || to.path === "/dashboard" || to.path === "/404") {
      const firstPage = menu.rawList.value.find((item) => item.component !== "__group__" && item.path)
      if (firstPage && firstPage.path !== to.path) {
        return { path: firstPage.path }
      }
    }

    if (to.matched.length === 0) return { path: "/404" }
    return true
  })
}
