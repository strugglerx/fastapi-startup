import { definePage } from "#/admin/shared/define-page.js"

export default definePage({
  menuKey: "system:audit",
  title: "审计日志",
  parentKey: "g:system",
  path: "/system/audit",
  component: "system/audit/index",
  icon: "FileText",
  sort: 14,
  cacheable: false,
})
