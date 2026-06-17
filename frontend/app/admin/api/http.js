import axios from "axios"
import { getToken, getAdminActiveRole, toLogin } from "./base.js"

export const http = axios.create({ timeout: 60000 })

http.interceptors.request.use((config) => {
  const token = getToken()
  if (token) config.headers.Token = token
  const activeRole = getAdminActiveRole()
  if (activeRole) config.headers["X-Active-Role"] = activeRole
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) toLogin()
    return Promise.reject(error)
  },
)
