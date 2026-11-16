/**
 * 跨环境的剪贴板复制 —— 兼容 HTTP / HTTPS、modal 内部 / 普通页面 等多种场景。
 *
 * 三道路径，按优先级降级：
 *  1. navigator.clipboard.writeText  —— HTTPS / localhost / 已授权
 *  2. document.execCommand('copy')   —— HTTP 老接口（关键：textarea 必须真实可见可 select）
 *  3. 失败兜底返回 false             —— UI 层 fallback 显示"请手动复制"
 */

function _execCommandCopy(text) {
  const ta = document.createElement("textarea")
  ta.value = text
  ta.style.position = "fixed"
  ta.style.top = "0"
  ta.style.left = "0"
  ta.style.width = "2em"
  ta.style.height = "2em"
  ta.style.padding = "0"
  ta.style.border = "0"
  ta.style.outline = "none"
  ta.style.boxShadow = "none"
  ta.style.background = "transparent"
  ta.style.zIndex = "2147483647"
  ta.setAttribute("readonly", "")
  ta.setAttribute("aria-hidden", "true")

  document.body.appendChild(ta)
  const prevActive = document.activeElement

  let ok = false
  try {
    ta.focus({ preventScroll: true })
    ta.select()
    ta.setSelectionRange(0, ta.value.length)
    ok = document.execCommand("copy")
  } catch (e) {
    console.error("[clipboard] execCommand 异常:", e)
    ok = false
  } finally {
    document.body.removeChild(ta)
    if (prevActive && typeof prevActive.focus === "function") {
      try {
        prevActive.focus({ preventScroll: true })
      } catch {
        /* ignore */
      }
    }
  }
  return ok
}

export async function copyToClipboard(text) {
  if (!text) return false

  if (typeof navigator !== "undefined" && navigator.clipboard && navigator.clipboard.writeText) {
    try {
      await navigator.clipboard.writeText(text)
      return true
    } catch (e) {
      console.warn("[clipboard] navigator.clipboard 失败，回退 execCommand:", e)
    }
  }

  return _execCommandCopy(text)
}

export async function copyWithToast(text, message, successText = "已复制") {
  if (!text) {
    message?.warning?.("没有可复制的内容")
    return false
  }
  const ok = await copyToClipboard(text)
  if (ok) {
    message?.success?.(successText)
  } else {
    message?.warning?.("自动复制失败，请手动选中复制")
    try {
      console.warn("[clipboard] copy failed; content logged for manual copy:", text)
    } catch {
      /* ignore */
    }
  }
  return ok
}

