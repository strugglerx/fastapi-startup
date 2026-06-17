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
  buttons: [
    { menuKey: "system:admin:create", title: "新建账号", sort: 1 },
    { menuKey: "system:admin:update", title: "修改账号", sort: 2 },
    { menuKey: "system:admin:delete", title: "删除账号", sort: 3 },
    { menuKey: "system:admin:password", title: "重置密码", sort: 4 },
  ]
})
