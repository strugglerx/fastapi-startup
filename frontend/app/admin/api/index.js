/**
 * app/admin/api —— admin 后台所有 endpoint 的统一封装。
 *
 * 使用：
 *   import { adminApi, menuApi } from "../api"
 *   const list = await adminApi.list({ page: 1, size: 20 })
 *
 * 全局工具：
 *   import { notifyError, notifySuccess, confirmAction } from "../api/feedback"
 *   import { getToken, getCachedAdminProfile, logoutAndRedirect } from "../api/base"
 *
 * 底层（一般不直接用，view 走 *Api 命名空间）：
 *   import { request, publicRequest } from "../api/fetch"
 */
export { default as createFetch, request, publicRequest } from "./fetch.js"
export * from "./feedback.js"
export * from "./base.js"

export { authApi }         from "./auth.js"
export { adminApi }        from "./admin.js"
export *                   from "./menu.js"
export *                   from "./role.js"

import { authApi }         from "./auth.js"
import { adminApi }        from "./admin.js"

export default {
  auth:         authApi,
  admin:        adminApi,
}
