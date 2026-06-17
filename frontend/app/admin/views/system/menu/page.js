import { definePage } from "#/admin/shared/define-page.js"

export default definePage({
  menuKey: "system:menu",
  title: "菜单管理",
  parentKey: "g:system",
  path: "/system/menu",
  component: "system/menu/index",
  icon: "Settings",
  sort: 12,
  cacheable: true,
})
