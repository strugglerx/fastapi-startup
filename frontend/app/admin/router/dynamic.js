import { router } from "./index.js"

const modules = import.meta.glob("../views/**/*.vue")

export const availableComponents = Object.keys(modules)
  .map((key) => key.replace("../views/", "").replace(".vue", ""))
  .filter((name) => !name.startsWith("error/") && !name.includes("/components/"))

function resolveLoader(component) {
  const key = `../views/${component}.vue`
  const loader = modules[key]
  if (!loader) {
    throw new Error(`[router] 找不到组件：${key}`)
  }
  return loader
}

export function buildDynamicRoutes(menus) {
  return menus
    .filter((item) => item.enabled && item.component !== "__group__")
    .map((item) => ({
      path: item.path,
      name: item.menuKey,
      component: resolveLoader(item.component),
      meta: {
        title: item.title,
        icon: item.icon,
        hidden: item.hidden,
        cacheable: item.cacheable,
        cacheKey: item.menuKey,
      },
    }))
}

export function registerDynamicRoutes(menus) {
  const routes = buildDynamicRoutes(menus)
  for (const route of routes) {
    if (!router.hasRoute(route.name)) router.addRoute("Root", route)
  }
  if (!router.hasRoute("AdminCatchAll")) {
    router.addRoute({ path: "/:pathMatch(.*)*", name: "AdminCatchAll", redirect: "/404" })
  }
}
