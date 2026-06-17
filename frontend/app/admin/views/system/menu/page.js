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
  buttons: [
    { menuKey: "system:menu:create", title: "新建菜单", sort: 1 },
    { menuKey: "system:menu:update", title: "修改菜单", sort: 2 },
    { menuKey: "system:menu:delete", title: "删除菜单", sort: 3 },
  ]
})
