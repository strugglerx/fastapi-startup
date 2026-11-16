"""统一东八区时间辅助。

业务里大量 `datetime.now(tz)` / `_now_cn()` 散落在各 service，集中到这里：
- `CN_TZ`：单例 `ZoneInfo("Asia/Shanghai")`
- `now_cn()`：tz-aware now，剥掉微秒以匹配项目里 DateTime 字段精度
"""
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

CN_TZ = ZoneInfo("Asia/Shanghai")


def now_cn() -> datetime:
    """获取当前东八区时间，去掉微秒"""
    return datetime.now(CN_TZ).replace(microsecond=0)


def is_past(value: Optional[datetime]) -> bool:
    if value is None:
        return False
    if value.tzinfo is None:
        value = value.replace(tzinfo=CN_TZ)
    return value < now_cn()


def ensure_cn_aware(value: datetime) -> datetime:
    """把从 DB 读回的 datetime 强制成 tz-aware CN。

    背景：models 里列声明是 `DateTime(timezone=True)` 但 MySQL 底层用 `DATETIME`（不存 tz）。
    写入时 tz-aware CN datetime 被剥 tz 留 CN 字面值，读回是 naive。naive = CN 本地时间，
    绝不能当 UTC 处理（会导致凭空产生 8 小时时差）。
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=CN_TZ)
    return value

