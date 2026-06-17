import { request } from "./fetch.js"

export const dictApi = {
  list: () => request.get("/api/v1/dicts"),
  create: (data) => request.post("/api/v1/dicts", data),
  update: (id, data) => request.put(`/api/v1/dicts/${id}`, data),
  delete: (id) => request.delete(`/api/v1/dicts/${id}`),
  
  listItems: (dictCode) => request.get(`/api/v1/dicts/${dictCode}/items`),
  createItem: (dictCode, data) => request.post(`/api/v1/dicts/${dictCode}/items`, data),
  updateItem: (itemId, data) => request.put(`/api/v1/dicts/items/${itemId}`, data),
  deleteItem: (itemId) => request.delete(`/api/v1/dicts/items/${itemId}`),
  
  getOptions: (dictCode) => request.get(`/api/v1/dicts/options/${dictCode}`),
}
