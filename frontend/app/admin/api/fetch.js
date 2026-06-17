/**
 * fetch.js —— axios 工厂 + 拦截器
 *
 * 参考 miniapp-rebuild/admin-frontend/src/utils/fetch.js，做了适配：
 *   1. Token 头用 `Token: xxx`（匹配后端 deps.get_current_user Header alias）
 *      —— 不用 `Authorization: Bearer xxx`，避免改后端
 *   2. baseURL 默认空（走 vite proxy 到 :8000）
 *   3. 业务码非 0 时自动 notifyError + reject
 *   4. 401 自动 toLogin（除非传 skipAuthRedirect=true）
 *
 * 用法：
 *   import createFetch from "./fetch.js"
 *   const req = createFetch()
 *   const data = await req.get("/api/v1/agents", { page: 1 })
 *   // data 已经是 res.body.data（解过 {code, data} 包装）
 */
import axios from "axios"

import { getToken, getAdminActiveRole, toLogin } from "./base.js"
import { notifyError } from "./feedback.js"

class Fetch {
  /**
   * @param {object} options
   * @param {string}  options.baseURL          自定义 baseURL（默认空，走 vite proxy）
   * @param {boolean} options.withToken        是否自动注入 Token 头（默认 true）
   * @param {boolean} options.skipAuthRedirect 401 时是否跳登录（登录接口本身设 true）
   * @param {boolean} options.silent           业务错误是否静默（不弹 notifyError，由 view 自己处理）
   */
  constructor({ baseURL = "", withToken = true, skipAuthRedirect = false, silent = false } = {}) {
    this._withToken = withToken
    this._skipAuthRedirect = skipAuthRedirect
    this._silent = silent
    this._instance = axios.create({ baseURL, timeout: 60000 })
    this._initial(this._instance)
  }

  _initial(instance) {
    instance.interceptors.request.use(
      (config) => {
        if (this._withToken) {
          const token = getToken()
          if (token) config.headers.Token = token

          const activeRole = getAdminActiveRole()
          if (activeRole) config.headers["X-Active-Role"] = activeRole
        }
        return config
      },
      (error) => Promise.reject(error),
    )

    instance.interceptors.response.use(
      (res) => {
        const body = res.data || {}
        const httpStatus = res.status

        // HTTP 401 → 登录态失效（后端返回 {code: 401, msg: "..."}）
        if (httpStatus === 401 || body.code === 401) {
          if (!this._skipAuthRedirect) toLogin()
          return Promise.reject(new Error(body.msg || "登录已失效"))
        }

        // 业务码非 0 → 弹错 + reject（后端成功返回 code: 0）
        if (body.code !== 0 && body.code !== undefined) {
          const msg = body.msg || "服务器异常"
          if (!this._silent) notifyError(msg)
          return Promise.reject(Object.assign(new Error(msg), { code: body.code, raw: body }))
        }

        // 标准 {code: 0, data} 解出 data；裸响应则原样返回
        return body.data !== undefined ? body.data : body
      },
      (error) => {
        const status = error?.response?.status
        if (status === 401) {
          if (!this._skipAuthRedirect) toLogin()
          return Promise.reject(new Error(error?.response?.data?.msg || "登录已失效"))
        }
        const msg = error?.response?.data?.msg || error.message || "网络异常"
        if (!this._silent) notifyError(msg)
        return Promise.reject(error)
      },
    )
  }

  get(url, params, extend)  { return this._instance({ method: "get",    url, params, ...extend }) }
  post(url, data, extend)   { return this._instance({ method: "post",   url, data,   ...extend }) }
  put(url, data, extend)    { return this._instance({ method: "put",    url, data,   ...extend }) }
  patch(url, data, extend)  { return this._instance({ method: "patch",  url, data,   ...extend }) }
  delete(url, data, extend) { return this._instance({ method: "delete", url, data,   ...extend }) }
}

/** 工厂：默认带 Token + 401 跳登录 + 业务错自动 toast */
export default function createFetch(options) {
  return new Fetch(options)
}

/** 全局默认实例（带鉴权） */
export const request = new Fetch()

/** 给登录页用的实例：401 不跳转（避免密码错误触发跳转） */
export const publicRequest = new Fetch({ withToken: false, skipAuthRedirect: true })

/** 静默实例：不弹错误 toast，不跳登录（用于后台自动请求） */
export const silentRequest = new Fetch({ silent: true, skipAuthRedirect: true })
