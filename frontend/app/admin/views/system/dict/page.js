import { definePage } from "#/admin/shared/define-page.js"

export default definePage({
  menuKey: "system:dict",
  title: "数据字典",
  parentKey: "g:system",
  path: "/system/dict",
  component: "system/dict/index",
  icon: "BookOpen",
  sort: 16,
  cacheable: false,
  buttons: [
    { menuKey: "system:dict:create", title: "新建字典", sort: 1 },
    { menuKey: "system:dict:update", title: "修改字典", sort: 2 },
    { menuKey: "system:dict:delete", title: "删除字典", sort: 3 },
  ]
})
