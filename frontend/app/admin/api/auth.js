/** 后台认证 API */
import { request, publicRequest } from "./fetch.js"

export const authApi = {
  /** POST /api/v1/auth/login {email, password} — 用 publicRequest 避免密码错误时被拦截到登录页 */
  login:  (email, password) => publicRequest.post("/api/v1/auth/login", { email, password }),
  /** GET  /api/v1/auth/me */
  me:     ()                 => request.get("/api/v1/auth/me"),
  /** POST /api/v1/auth/logout */
  logout: ()                 => request.post("/api/v1/auth/logout", null),
}
