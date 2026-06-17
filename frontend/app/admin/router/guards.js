import { getToken } from "../api/base.js"
import { useMenuStore } from "../stores/menu.js"

const WHITE_PATHS = new Set(["/404"])

export function setupGuards(router) {
  router.beforeEach(async (to) => {
    if (WHITE_PATHS.has(to.path)) return true

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
        console.error("[guards] menu load failed", error)
        menu.reset()
        return { path: "/404" }
      }
    }

    if (to.matched.length === 0 || to.path === "/" || to.path === "/dashboard") {
      const firstPage = menu.rawList.value.find((item) => item.component !== "__group__" && item.path)
      if (firstPage && firstPage.path !== to.path && (to.path === "/" || to.path === "/dashboard" || to.path === "/404")) {
        return { path: firstPage.path }
      }
    }

    if (to.matched.length === 0) return { path: "/404" }
    return true
  })
}
