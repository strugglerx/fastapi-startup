import { ref } from "vue"
import { request } from "./fetch.js"

const _cache = ref([])
let _loaded = false

export function fetchRoles() {
  return request.get("/api/v1/role")
}

export function createRole(payload) {
  return request.post("/api/v1/role", payload).then((data) => {
    invalidateRoles()
    return data
  })
}

export function updateRole(id, payload) {
  return request.put(`/api/v1/role/${id}`, payload).then((data) => {
    invalidateRoles()
    return data
  })
}

export function deleteRole(id) {
  return request.delete(`/api/v1/role/${id}`).then((data) => {
    invalidateRoles()
    return data
  })
}

export function invalidateRoles() {
  _loaded = false
  _cache.value = []
}

export function useRoles() {
  async function loadRoles({ force = false } = {}) {
    if (_loaded && !force) return _cache.value
    _cache.value = await fetchRoles()
    _loaded = true
    return _cache.value
  }

  return {
    roles: _cache,
    loadRoles,
    invalidateRoles,
  }
}
