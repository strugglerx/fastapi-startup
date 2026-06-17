import { computed, ref } from "vue"
import { fetchMenuList } from "../api/menu.js"
import { silentRequest } from "../api/fetch.js"
import { registerDynamicRoutes } from "../router/dynamic.js"
import { getLocalPages } from "../shared/page-registry.js"


const registered = ref(false)
const rawList = ref([])
const tree = ref([])
let _loading = null

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
    tree.value = toTree(list.filter((item) => !item.hidden))
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
  tree.value = []
}

export function useMenuStore() {
  return {
    registered: computed(() => registered.value),
    rawList: computed(() => rawList.value),
    tree: computed(() => tree.value),
    load,
    reset,
  }
}
