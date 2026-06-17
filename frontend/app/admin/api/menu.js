import { request } from "./fetch.js"

/**
 * @returns {Promise<import("../shared/define-page.js").MenuItem[]>}
 */
export function fetchMenuList(params) {
  return request.get("/api/menu/list", params)
}

/**
 * @param {import("../shared/define-page.js").PageMeta[]} pages
 */
export function syncMenus(pages) {
  return request.post("/api/menu/sync", { pages })
}

export function fetchRoleGrants(role) {
  return request.get("/api/menu/role-grants", { role })
}

export function setRoleGrants(role, menuKeys) {
  return request.put("/api/menu/role-grants", { role, menuKeys })
}

export function updateMenuMeta(menuKey, payload) {
  return request.patch(`/api/menu/${encodeURIComponent(menuKey)}`, payload)
}

export function createMenuGroup(payload) {
  return request.post("/api/menu/groups", payload)
}

export function createMenu(body) {
  return request.post("/api/menu/", body)
}

export function updateMenu(id, body) {
  return request.put(`/api/menu/${id}`, body)
}

export function deleteMenu(id) {
  return request.delete(`/api/menu/${id}`)
}
