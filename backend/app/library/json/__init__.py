import json as _stdjson
from typing import Any

try:
    import orjson
except ImportError:
    orjson = None

# JS Number.MAX_SAFE_INTEGER。Python int 是无限精度，JSON spec 也允许任意大整数，
# 但 JS 客户端把超 2^53-1 的整数 parse 后会丢精度。雪花 ID 全部超界，必须以 string
# 形式落到 wire，前端拿到的就是 "123456789012345678"。
JS_MAX_SAFE_INT = 9007199254740991  # 2**53 - 1


def omit_empty(value):
    if value is None:
        raise TypeError("omitted")
    return value


def dumps_clean(data: Any) -> str:
    """过滤 None 值的快速 JSON 序列化"""
    if isinstance(data, str) and orjson:
        data = orjson.loads(data)

    def clean(obj):
        if isinstance(obj, dict):
            return {k: clean(v) for k, v in obj.items() if v is not None}
        if isinstance(obj, list):
            return [clean(v) for v in obj]
        return obj

    cleaned = clean(data)
    if orjson:
        return orjson.dumps(
            cleaned,
            option=orjson.OPT_NAIVE_UTC
        ).decode()
    return _stdjson.dumps(cleaned, ensure_ascii=False)


def _jssafe(obj: Any) -> Any:
    """递归把所有 int > 2^53-1 转 string，避免 JS 丢精度。

    边界处理：
    - `bool` 是 `int` 子类，必须先排除（True/False 不能变 "True"/"False"）
    - 业务时间戳（ms 自 1970）~1.8e12 远低于阈值，不会误转
    - 仅 PK 与外键引用字段（雪花 ID ~2e15+）会触发
    """
    if isinstance(obj, bool):
        return obj
    if isinstance(obj, int) and abs(obj) > JS_MAX_SAFE_INT:
        return str(obj)
    if isinstance(obj, dict):
        return {k: _jssafe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_jssafe(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_jssafe(v) for v in obj)
    return obj


def dumps_jssafe(data: Any) -> str:
    """序列化为 JS 安全的 JSON 字符串（int > 2^53-1 转 string）。

    用于 setup_stand_response 中间件统一包装：
        from app.library.json import dumps_jssafe
        return Response(content=dumps_jssafe(data), media_type="application/json")
    """
    return _stdjson.dumps(_jssafe(data), ensure_ascii=False)
