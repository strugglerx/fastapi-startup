import { definePage } from "#/admin/shared/define-page.js"

export default definePage({
  menuKey: "dashboard",
  title: "控制台",
  path: "/dashboard",
  component: "dashboard/index",
  icon: "LayoutDashboard",
  sort: 1,
  cacheable: true,
})
