import { request } from "./fetch.js"

export const auditApi = {
  list: (params) => request.get("/api/v1/audit/list", params),
}
