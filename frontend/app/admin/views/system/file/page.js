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
  buttons: [
    { menuKey: "system:file:upload", title: "上传文件", sort: 1 },
    { menuKey: "system:file:delete", title: "删除文件", sort: 2 },
  ]
})
