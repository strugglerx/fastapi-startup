const modules = import.meta.glob("../views/**/page.js", { eager: true })

export function getLocalPages() {
  const pages = []
  for (const filePath in modules) {
    const meta = modules[filePath]?.default
    if (meta && meta.menuKey) pages.push(meta)
  }
  return pages
}
