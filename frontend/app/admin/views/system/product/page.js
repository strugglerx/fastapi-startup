import { definePage } from "#/admin/shared/define-page.js"

export default definePage({
  menuKey: "system:product",
  title: "产品管理",
  parentKey: "g:system",
  path: "/system/product",
  component: "system/product/index",
  icon: "Grid",
  sort: 17,
  cacheable: false,
})
