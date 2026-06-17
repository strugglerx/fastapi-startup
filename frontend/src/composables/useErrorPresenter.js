function stringifyRaw(value) {
  if (!value) return "";
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function compactMessage(value) {
  if (!value) return "";
  if (typeof value === "string") return value;
  if (typeof value === "object") {
    return value.msg || value.message || value.summary || "";
  }
  return String(value);
}

function summarizeValidationErrors(errors = []) {
  return errors.slice(0, 3).map((item) => `${item.path || "$"}: ${item.message || "字段不合法"}`);
}

function humanizeSummary(message, details) {
  const raw = `${message || ""} ${stringifyRaw(details)}`.toLowerCase();
  if (raw.includes("/presets") && raw.includes("404")) return "当前服务未部署预设能力，请先升级后端服务。";
  if (raw.includes("preset_management")) return "当前服务缺少预设能力字段，请检查后端版本是否一致。";
  if (raw.includes("payload validation failed")) return "模板字段校验未通过，请检查输入结构。";
  if (raw.includes("json")) return "JSON 格式不合法，请先修正语法。";
  if (raw.includes("download") && raw.includes("image")) return "图片下载失败，已跳过部分图片。";
  if (raw.includes("preview")) return "模板预览失败，请检查模板语法或字段标签。";
  if (raw.includes("upload")) return "模板上传失败，请检查文件格式与命名。";
  return message || "请求失败，请稍后重试。";
}

export function useErrorPresenter(state, { setStatus, notify }) {
  const showError = ({ title = "操作失败", summary = "请求失败，请稍后重试。", details = [], raw = "" }) => {
    const _details = Array.isArray(details) ? details : [];
    if (notify) {
      notify({ title, summary, details: _details, raw });
    } else {
      state.error = { visible: true, title, summary, details: _details, raw };
    }
  };

  const showSimpleError = (summary, raw = "", title = "操作失败") => {
    showError({ title, summary, raw });
  };

  const normalizeApiError = (operation, err, fallbackSummary = "请求失败，请稍后重试。") => {
    const detail = err?.detail;
    const validationErrors = detail?.summary?.errors || [];
    const details = validationErrors.length ? summarizeValidationErrors(validationErrors) : [];
    const raw = stringifyRaw(err);
    const message = compactMessage(detail) || compactMessage(err) || fallbackSummary;
    const summary = details.length ? "模板字段校验未通过，请检查输入结构。" : humanizeSummary(message, detail || err);
    return {
      title: `${operation}失败`,
      summary,
      details,
      raw
    };
  };

  return {
    showError,
    showSimpleError,
    normalizeApiError
  };
}
