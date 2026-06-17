/** 后台账号 CRUD（users 表，admin + member 后台登录账号） */
import { request } from "./fetch.js"

export const adminApi = {
  list:   (params)     => request.get("/api/v1/admins", params),
  create: (body)       => request.post("/api/v1/admins", body),
  update: (id, body)   => request.put(`/api/v1/admins/${id}`, body),
  resetPassword: (id, newPassword) =>
    request.post(`/api/v1/admins/${id}/reset-password`, { new_password: newPassword }),
  delete: (id)         => request.delete(`/api/v1/admins/${id}`),
}
