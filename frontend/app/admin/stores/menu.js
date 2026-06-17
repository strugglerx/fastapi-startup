import { computed, ref } from "vue"
import { fetchMenuList, syncMenus } from "../api/menu.js"
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

async function autoSync() {
  const pages = getLocalPages()
  if (!pages.length) return
  try {
    const result = await syncMenus(pages)
    if (result) console.info("[menu] auto-sync", result)
  } catch (e) {
    // 生产环境若配了 SYNC_TOKEN，前端无 token 会 403 —— 此时降级，只读 DB
    console.warn("[menu] auto-sync skipped:", e?.response?.status || e?.message || e)
  }
}

async function load() {
  if (registered.value) return
  if (_loading) return _loading

  _loading = (async () => {
    await autoSync()
    const list = await fetchMenuList()
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
