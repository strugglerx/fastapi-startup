import { definePage } from "#/admin/shared/define-page.js"

export default definePage({
  menuKey: "system:role",
  title: "角色与权限",
  parentKey: "g:system",
  path: "/system/role",
  component: "system/role/index",
  icon: "Shield",
  sort: 11,
  cacheable: false,
})
