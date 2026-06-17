import { clearToken } from "../api/base.js"
import { useKeepAliveStore } from "./keep-alive.js"
import { useMenuStore } from "./menu.js"

export function logout() {
  clearToken()
  useMenuStore().reset()
  useKeepAliveStore().clear()
  window.location.assign("/login/")
}
