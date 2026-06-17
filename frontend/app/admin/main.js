import "../../src/style.css"
import "./styles/admin-tokens.css"
import "./styles/admin-shared.css"
import { createApp } from "vue"
import naive from "naive-ui"
import App from "./App.vue"
import router from "./router/index.js"
import { hasPermission } from "./shared/auth.js"

const app = createApp(App)

// 注册 v-auth 权限指令
app.directive("auth", {
  mounted(el, binding) {
    const { value } = binding
    if (value) {
      if (!hasPermission(value)) {
        el.parentNode && el.parentNode.removeChild(el)
      }
    }
  }
})

// 挂载到全局属性，可在 template 中直接通过 $hasPermission('xxx') 校验
app.config.globalProperties.$hasPermission = hasPermission

app.use(router)
app.use(naive)
app.mount("#app")
