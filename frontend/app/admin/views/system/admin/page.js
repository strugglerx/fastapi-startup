import { definePage } from "#/admin/shared/define-page.js"

export default definePage({
  menuKey: "system:admin",
  title: "账号管理",
  parentKey: "g:system",
  path: "/system/admin",
  component: "system/admin/index",
  icon: "Users",
  sort: 10,
  cacheable: true,
})
