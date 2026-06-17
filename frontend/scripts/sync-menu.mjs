import { globby } from "globby"
import fs from "node:fs/promises"
import path from "node:path"
import { pathToFileURL } from "node:url"
import { fileURLToPath } from "node:url"

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const ROOT = path.resolve(__dirname, "../app/admin/views")
const DEFINE_PAGE_URL = pathToFileURL(path.resolve(__dirname, "../app/admin/shared/define-page.js")).href

const SYNC_ENDPOINT = process.env.SYNC_ENDPOINT || "http://127.0.0.1:8000/api/menu/sync"
const SYNC_TOKEN = process.env.SYNC_TOKEN || ""

async function importPage(file) {
  const source = await fs.readFile(file, "utf8")
  const patched = source.replaceAll(
    'from "#/admin/shared/define-page.js"',
    `from "${DEFINE_PAGE_URL}"`,
  )
  const url = `data:text/javascript;charset=utf-8,${encodeURIComponent(patched)}`
  return import(url)
}

async function loadAllPages() {
  const files = await globby(["**/page.js"], { cwd: ROOT, absolute: true })
  const result = []
  for (const file of files) {
    const mod = await importPage(file)
    const meta = mod.default
    if (!meta || !meta.menuKey) {
      throw new Error(`[sync:menu] ${file} 缺少 menuKey`)
    }
    result.push({ ...meta, __file: file })
  }
  return result
}

async function validate(pages) {
  const seen = new Set()
  for (const page of pages) {
    if (seen.has(page.menuKey)) {
      throw new Error(`[sync:menu] menuKey 冲突：${page.menuKey}`)
    }
    seen.add(page.menuKey)
    if (!page.path.startsWith("/")) {
      throw new Error(`[sync:menu] path 必须以 / 开头：${page.menuKey}`)
    }
    if (page.component !== "__group__") {
      const componentFile = path.resolve(ROOT, `${page.component}.vue`)
      try {
        await fs.access(componentFile)
      } catch {
        throw new Error(`[sync:menu] component 不存在：${page.menuKey} -> views/${page.component}.vue`)
      }
    }
  }

  const keys = new Set(pages.map((page) => page.menuKey))
  for (const page of pages) {
    if (page.parentKey && !page.parentKey.startsWith("g:") && !keys.has(page.parentKey)) {
      throw new Error(`[sync:menu] parentKey 不存在：${page.menuKey} -> ${page.parentKey}`)
    }
  }
}

async function pushToBackend(pages) {
  const body = pages.map(({ __file, ...page }) => page)
  const res = await fetch(SYNC_ENDPOINT, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      ...(SYNC_TOKEN ? { authorization: `Bearer ${SYNC_TOKEN}` } : {}),
    },
    body: JSON.stringify({ pages: body }),
  })
  if (!res.ok) throw new Error(`[sync:menu] 上送失败 ${res.status} ${await res.text()}`)
  const json = await res.json()
  console.log("[sync:menu] OK", json?.data || json)
}

;(async () => {
  const pages = await loadAllPages()
  await validate(pages)
  await pushToBackend(pages)
})().catch((error) => {
  console.error(error?.message || error)
  process.exit(1)
})
