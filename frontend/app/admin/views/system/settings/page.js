import { definePage } from "#/admin/shared/define-page.js"

export default definePage({
  menuKey: "system:settings",
  title: "系统设置",
  parentKey: "g:system",
  path: "/system/settings",
  component: "system/settings/index",
  icon: "Settings",
  sort: 13,
  cacheable: false,
})
