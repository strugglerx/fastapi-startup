/**
 * feedback.js —— 统一错误 / 成功提示
 *
 * 用 naive-ui 的 createDiscreteApi：可在组件 setup 之外（如 fetch 拦截器里）
 * 直接调用 message / dialog，无需 NMessageProvider 上下文。
 * 复制自参考项目 miniapp-rebuild/admin-frontend/src/utils/feedback.js
 */
import { h } from "vue"
import { createDiscreteApi, zhCN, dateZhCN } from "naive-ui"

const { message, dialog } = createDiscreteApi(["message", "dialog"], {
  configProviderProps: {
    locale: zhCN,
    dateLocale: dateZhCN,
  },
})

export function notifyError(text) {
  message.error(text || "操作失败")
}

export function notifySuccess(text) {
  message.success(text || "操作成功")
}

export function notifyInfo(text) {
  message.info(text || "")
}

export function notifyWarning(text) {
  message.warning(text || "")
}

export function confirmAction({
  title = "确认操作",
  content = "确定继续当前操作吗？",
  positiveText = "确认",
  negativeText = "取消",
  type = "warning",
} = {}) {
  return new Promise((resolve) => {
    const open = dialog[type] || dialog.warning
    open({
      title,
      content,
      positiveText,
      negativeText,
      maskClosable: false,
      closeOnEsc: true,
      onPositiveClick: () => resolve(true),
      onNegativeClick: () => resolve(false),
      onClose: () => resolve(false),
    })
  })
}

export function showDetailDialog({
  title = "处理结果",
  lines = [],
  positiveText = "知道了",
  type = "info",
} = {}) {
  const open = dialog[type] || dialog.info
  open({
    title,
    positiveText,
    maskClosable: true,
    content: () =>
      h(
        "div",
        { style: "white-space: pre-wrap; font-size: 13px; line-height: 1.7; color: #475569;" },
        Array.isArray(lines) ? lines.join("\n") : String(lines || ""),
      ),
  })
}

export { message as $message, dialog as $dialog }
