import { router } from "./index.js"

const modules = import.meta.glob("../views/**/*.vue")

export const availableComponents = Object.keys(modules)
  .map((key) => key.replace("../views/", "").replace(".vue", ""))
  .filter((name) => !name.startsWith("error/") && !name.includes("/components/"))

function resolveLoader(component) {
  const key = `../views/${component}.vue`
  const loader = modules[key]
  if (!loader) {
    console.warn(`[router] 组件文件不存在，已跳过：${key}（请检查数据库菜单或执行同步）`)
    return null
  }
  return loader
}

export function buildDynamicRoutes(menus) {
  return menus
    .filter((item) => item.enabled && item.component !== "__group__" && item.component !== "__button__")
    .map((item) => {
      const loader = resolveLoader(item.component)
      if (!loader) return null  // 组件不存在，跳过注册此路由
      return {
        path: item.path,
        name: item.menuKey,
        component: loader,
        meta: {
          title: item.title,
          icon: item.icon,
          hidden: item.hidden,
          cacheable: item.cacheable,
          cacheKey: item.menuKey,
        },
      }
    })
    .filter(Boolean)  // 过滤掉 null 项
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
