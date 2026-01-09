from typing import Any

import orjson


def omit_empty(value):
    if value is None:
        raise TypeError("omitted")
    return value

def dumps_clean(data: Any) -> str:
    if type(data) == str:
        data = orjson.loads(data)
    """性能更强的None值过滤（需安装orjson）"""
    def clean(obj):
        if isinstance(obj, dict):
            return {k: v for k, v in obj.items() if v is not None}
        return obj
    
    return orjson.dumps(
        clean(data),
        option=orjson.OPT_NAIVE_UTC | orjson.OPT_SERIALIZE_NUMPY
    ).decode()