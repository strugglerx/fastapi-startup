import { createRouter, createWebHashHistory } from "vue-router"
import { constantRoutes } from "./constant-routes.js"
import { setupGuards } from "./guards.js"

export const router = createRouter({
  history: createWebHashHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: constantRoutes,
})

setupGuards(router)

export default router
