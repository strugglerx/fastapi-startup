import { computed, ref } from "vue"
import { fetchMenuList } from "../api/menu.js"
import { silentRequest } from "../api/fetch.js"
import { registerDynamicRoutes } from "../router/dynamic.js"
import { getLocalPages } from "../shared/page-registry.js"


const DEBUG_KEY = "smartai_admin_menu_debug_show_all"

const registered = ref(false)
const rawList = ref([])
const debugShowAll = ref(sessionStorage.getItem(DEBUG_KEY) === "true")
let _loading = null

function _isAdminUser() {
  try {
    const u = JSON.parse(localStorage.getItem("smartai_admin_user") || "null")
    if (!u) return false
    if (u.fixed) return true
    if (u.role === "admin") return true
    if (Array.isArray(u.permissions) && u.permissions.includes("*")) return true
    return false
  } catch {
    return false
  }
}

function toTree(items) {
  const map = new Map()
  items.forEach((item) => map.set(item.menuKey, { ...item, children: [] }))

  const roots = []
  map.forEach((node) => {
    if (node.parentKey && map.has(node.parentKey)) {
      map.get(node.parentKey).children.push(node)
    } else {
      roots.push(node)
    }
  })

  const sortRec = (nodes) => {
    nodes.sort((a, b) => a.sort - b.sort)
    nodes.forEach((node) => sortRec(node.children))
  }
  sortRec(roots)
  return roots
}

// 计算侧栏可见的菜单（按 hidden + 管理员侧栏隐藏 + 调试开关过滤）
const tree = computed(() => {
  const admin = _isAdminUser()
  const list = rawList.value.filter((item) => {
    if (item.hidden) return false
    if (admin && item.adminSidebarHidden && !debugShowAll.value) return false
    return true
  })
  return toTree(list)
})

async function load() {
  if (registered.value) return
  if (_loading) return _loading

  _loading = (async () => {
    let list = await fetchMenuList()

    // 菜单表为空（首次部署）→ 自动同步一次，失败则静默跳过
    if (list.length === 0) {
      try {
        await silentRequest.post("/api/menu/sync", { pages: getLocalPages() })
        list = await fetchMenuList()
      } catch {
        // 非 admin 用户或后端拒绝时静默忽略，加载空菜单继续
      }
    }

    rawList.value = list
    registerDynamicRoutes(list)
    registered.value = true
  })().finally(() => {
    _loading = null
  })

  return _loading
}

function reset() {
  registered.value = false
  rawList.value = []
}

function setDebugShowAll(v) {
  const next = Boolean(v)
  debugShowAll.value = next
  if (next) sessionStorage.setItem(DEBUG_KEY, "true")
  else sessionStorage.removeItem(DEBUG_KEY)
}

export function useMenuStore() {
  return {
    registered: computed(() => registered.value),
    rawList: computed(() => rawList.value),
    tree,
    debugShowAll: computed(() => debugShowAll.value),
    setDebugShowAll,
    load,
    reset,
  }
}
