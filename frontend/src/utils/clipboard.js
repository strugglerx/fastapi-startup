/**
 * Copy text to the user's clipboard.
 *
 * Prefers the async Clipboard API (available only in secure contexts: HTTPS or
 * localhost). Automatically falls back to the legacy textarea + execCommand
 * approach for non-secure origins such as http://0.0.0.0 used in local dev.
 *
 * Errors are propagated so callers can choose to handle or ignore them.
 *
 * @param {string} text  The text to copy.
 * @returns {Promise<void>}
 */
export async function copyToClipboard(text) {
  const value = String(text ?? "");

  // Modern Clipboard API — only works in secure contexts (HTTPS / localhost).
  // navigator.clipboard is undefined on http://0.0.0.0, so guard explicitly.
  if (typeof navigator !== "undefined" && navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(value);
      return;
    } catch {
      // Clipboard API present but rejected (focus/permissions issue).
      // Fall through to the execCommand fallback below.
    }
  }

  // Legacy fallback via textarea + execCommand.
  // Deprecated but universally supported and works on non-secure origins.
  return copyViaExecCommand(value);
}

/**
 * Copy text using the textarea + document.execCommand('copy') trick.
 * Restores the prior focus and selection state so the operation is invisible
 * to the user.
 *
 * @param {string} text
 * @returns {Promise<void>}
 */
function copyViaExecCommand(text) {
  if (typeof document === "undefined" || !document.body) {
    return Promise.reject(new Error("Clipboard fallback requires a browser document."));
  }

  // Snapshot focus and selection state so we can restore it afterward.
  const prevActive = document.activeElement;
  const selection  = document.getSelection?.();
  const prevRange  =
    selection && selection.rangeCount > 0
      ? selection.getRangeAt(0).cloneRange()
      : null;

  const el = document.createElement("textarea");
  el.value = text;
  el.setAttribute("readonly", "");
  // Place the element off-screen — must be in the DOM for execCommand to work,
  // but should be invisible and non-interactive.
  el.style.cssText = "position:absolute;left:-9999px;top:-9999px;margin:0;padding:0;border:0;";

  let targetParent = document.body;
  if (prevActive && prevActive !== document.body) {
    const modalContainer = prevActive.closest('.n-modal, .n-drawer, [role="dialog"]');
    if (modalContainer) {
      targetParent = modalContainer;
    } else if (prevActive.parentElement) {
      targetParent = prevActive.parentElement;
    }
  }

  try {
    targetParent.appendChild(el);
    el.focus({ preventScroll: true });
    el.select();
    el.setSelectionRange(0, text.length); // Required on iOS

    const ok = document.execCommand("copy");
    if (!ok) throw new Error("document.execCommand('copy') returned false");

    return Promise.resolve();
  } finally {
    // Always remove the temporary element — we own its lifecycle.
    el.remove();

    // Best-effort: restore prior focus and text selection so the copy
    // operation is invisible to the user. Wrapped in try/catch so that a
    // restoration failure (e.g. detached element) never swallows the actual
    // copy result or turns a successful operation into a rejected Promise.
    try {
      if (prevRange && selection) {
        selection.removeAllRanges();
        selection.addRange(prevRange);
      }
      if (prevActive?.focus) {
        prevActive.focus({ preventScroll: true });
      }
    } catch {
      // Non-critical — silently ignore restoration failures.
    }
  }
}
