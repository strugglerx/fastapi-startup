/**
 * 时间戳解析与格式化的统一出口。
 *
 * 背景：SQLite 不存 timezone，SQLAlchemy 的 DateTime(timezone=True) 在 SQLite
 * 上仍然存为裸字符串 "2026-06-10 15:01:34.000000"，读回是 naive datetime，
 * Pydantic 序列化时不带 +00:00 偏移。前端 new Date(iso) 把这种串当本地时间
 * 解析，结果展示比真实时间慢 / 快 N 小时（中国时区下差 8h）。
 *
 * 解决：parseTimestamp 统一在前端补齐 —— 检测到字符串没有时区信息时
 * 默认按 UTC 处理。所有 formatXxx 都基于它。
 */

const PAD = (n) => String(n).padStart(2, "0")
const HAS_TZ_RE = /[zZ]|[+-]\d{2}:?\d{2}$/

export function parseTimestamp(iso) {
  if (!iso) return null
  const s = String(iso).trim()
  if (!s) return null
  const normalized = HAS_TZ_RE.test(s) ? s : `${s.replace(" ", "T")}Z`
  const d = new Date(normalized)
  return isNaN(d.getTime()) ? null : d
}

/** "2026-06-11 14:06" —— 完整时间，浏览器本地时区。 */
export function formatTime(iso) {
  const d = parseTimestamp(iso)
  if (!d) return iso ? String(iso) : "—"
  return `${d.getFullYear()}-${PAD(d.getMonth() + 1)}-${PAD(d.getDate())} ${PAD(d.getHours())}:${PAD(d.getMinutes())}`
}

/** "14:06"（今天）或 "06/11 14:06"（非今天）—— 紧凑显示。 */
export function formatTimeShort(iso) {
  const d = parseTimestamp(iso)
  if (!d) return iso ? String(iso) : "—"
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  if (isToday) return `${PAD(d.getHours())}:${PAD(d.getMinutes())}`
  return `${PAD(d.getMonth() + 1)}/${PAD(d.getDate())} ${PAD(d.getHours())}:${PAD(d.getMinutes())}`
}

/** "2026-06-11" —— 仅日期。 */
export function formatDate(iso) {
  const d = parseTimestamp(iso)
  if (!d) return iso ? String(iso) : "—"
  return `${d.getFullYear()}-${PAD(d.getMonth() + 1)}-${PAD(d.getDate())}`
}
