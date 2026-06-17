import { ref } from "vue"
import { http } from "./http.js"

const _cache = ref([])
let _loaded = false

function unwrap(res) {
  return res.data?.data ?? res.data
}

export function fetchRoles() {
  return http.get("/api/v1/role").then((r) => unwrap(r))
}

export function createRole(payload) {
  return http.post("/api/v1/role", payload).then((r) => {
    invalidateRoles()
    return unwrap(r)
  })
}

export function updateRole(id, payload) {
  return http.put(`/api/v1/role/${id}`, payload).then((r) => {
    invalidateRoles()
    return unwrap(r)
  })
}

export function deleteRole(id) {
  return http.delete(`/api/v1/role/${id}`).then((r) => {
    invalidateRoles()
    return unwrap(r)
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
