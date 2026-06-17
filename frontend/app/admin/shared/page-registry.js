const modules = import.meta.glob("../views/**/page.js", { eager: true })

export function getLocalPages() {
  const pages = []
  for (const filePath in modules) {
    const meta = modules[filePath]?.default
    if (meta && meta.menuKey) {
      pages.push(meta)
      if (meta.buttons && Array.isArray(meta.buttons)) {
        meta.buttons.forEach((btn) => {
          pages.push({
            menuKey: btn.menuKey,
            parentKey: meta.menuKey,
            title: btn.title,
            path: "",
            component: "__button__",
            hidden: true,
            sort: btn.sort || 99,
            cacheable: false,
          })
        })
      }
    }
  }
  return pages
}

