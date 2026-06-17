import { request } from "./fetch.js"

export const fileApi = {
  list: (params) => request.get("/api/v1/files", params),
  delete: (id) => request.delete(`/api/v1/files/${id}`),
}
