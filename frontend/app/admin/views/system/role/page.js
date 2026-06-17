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
  buttons: [
    { menuKey: "system:role:create", title: "新建角色", sort: 1 },
    { menuKey: "system:role:update", title: "修改角色", sort: 2 },
    { menuKey: "system:role:delete", title: "删除角色", sort: 3 },
    { menuKey: "system:role:grant", title: "角色授权", sort: 4 },
  ]
})
