import { http } from "./http.js"

/**
 * @returns {Promise<import("../shared/define-page.js").MenuItem[]>}
 */
export function fetchMenuList(params) {
  return http.get("/api/menu/list", { params }).then((r) => r.data?.data ?? r.data)
}

/**
 * @param {import("../shared/define-page.js").PageMeta[]} pages
 */
export function syncMenus(pages) {
  return http.post("/api/menu/sync", { pages }).then((r) => r.data?.data ?? r.data)
}

export function fetchRoleGrants(role) {
  return http.get("/api/menu/role-grants", { params: { role } }).then((r) => r.data?.data ?? r.data)
}

export function setRoleGrants(role, menuKeys) {
  return http.put("/api/menu/role-grants", { role, menuKeys }).then((r) => r.data?.data ?? r.data)
}

export function updateMenuMeta(menuKey, payload) {
  return http.patch(`/api/menu/${encodeURIComponent(menuKey)}`, payload).then((r) => r.data?.data ?? r.data)
}

export function createMenuGroup(payload) {
  return http.post("/api/menu/groups", payload).then((r) => r.data?.data ?? r.data)
}

export function createMenu(body) {
  return http.post("/api/menu/", body).then((r) => r.data?.data ?? r.data)
}

export function updateMenu(id, body) {
  return http.put(`/api/menu/${id}`, body).then((r) => r.data?.data ?? r.data)
}

export function deleteMenu(id) {
  return http.delete(`/api/menu/${id}`).then((r) => r.data?.data ?? r.data)
}
