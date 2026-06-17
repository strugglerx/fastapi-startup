import { computed, ref } from "vue"

const cachedViews = ref([])

function add(key) {
  if (!key) return
  if (!cachedViews.value.includes(key)) cachedViews.value.push(key)
}

function remove(key) {
  cachedViews.value = cachedViews.value.filter((item) => item !== key)
}

function clear() {
  cachedViews.value = []
}

export function useKeepAliveStore() {
  return {
    cachedViews: computed(() => cachedViews.value),
    add,
    remove,
    clear,
  }
}
