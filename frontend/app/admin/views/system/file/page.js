import { definePage } from "#/admin/shared/define-page.js"

export default definePage({
  menuKey: "system:file",
  title: "文件管理",
  parentKey: "g:system",
  path: "/system/file",
  component: "system/file/index",
  icon: "FolderOpen",
  sort: 15,
  cacheable: false,
})
