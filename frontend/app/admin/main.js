import "../../src/style.css"
import "./styles/admin-tokens.css"
import "./styles/admin-shared.css"
import { createApp } from "vue"
import naive from "naive-ui"
import App from "./App.vue"
import router from "./router/index.js"

const app = createApp(App)
app.use(router)
app.use(naive)
app.mount("#app")
