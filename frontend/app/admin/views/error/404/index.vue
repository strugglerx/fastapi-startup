<template>
  <div class="not-found">
    <div class="not-found-emoji">🤔</div>
    <h1 class="not-found-title">页面不存在</h1>
    <p class="not-found-desc">当前地址没有匹配的后台页面。</p>
    <n-button type="primary" @click="goHome">回到工作台</n-button>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router"
import { NButton } from "naive-ui"

defineOptions({ name: "NotFoundView" })

const router = useRouter()
function goHome() {
  router.push({ name: "dashboard" }).catch(() => router.push("/"))
}
</script>

<style scoped>
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 80px 24px;
}
.not-found-emoji {
  font-size: 64px;
  line-height: 1;
}
.not-found-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--c-text-primary);
  margin: 0;
}
.not-found-desc {
  color: var(--c-text-muted);
  margin: 0 0 12px;
}
</style>
