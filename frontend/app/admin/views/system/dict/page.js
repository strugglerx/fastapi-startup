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
})
