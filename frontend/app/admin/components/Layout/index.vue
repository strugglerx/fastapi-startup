<template>
  <router-view v-slot="{ Component, route: activeRoute }">
    <keep-alive :include="keepAlive.cachedViews.value">
      <component :is="Component" :key="activeRoute.meta?.cacheKey || activeRoute.path" />
    </keep-alive>
  </router-view>
</template>

<script setup>
import { watch } from "vue"
import { useRoute } from "vue-router"
import { useKeepAliveStore } from "../../stores/keep-alive.js"

defineOptions({ name: "RootLayout" })

const route = useRoute()
const keepAlive = useKeepAliveStore()

watch(
  () => route.meta,
  (meta) => {
    const key = meta?.cacheKey
    if (key && meta?.cacheable) keepAlive.add(key)
  },
  { immediate: true },
)
</script>
