"""核心工具测试：Snowflake ID / Crypto 加解密 / Time 时区 / JSON JS 安全序列化。"""
import time
from app.core import snowflake, crypto
from app.core import time as ctime
from app.library.json import dumps_jssafe, JS_MAX_SAFE_INT


def test_snowflake_id_generation():
    ids = [snowflake.next_id() for _ in range(1000)]
    # 严格递增且无重复
    assert len(set(ids)) == 1000
    assert ids == sorted(ids)

    # 验证结构解析
    parsed = snowflake.parse(ids[0])
    assert "ts_ms" in parsed
    assert "worker" in parsed
    assert "seq" in parsed
    assert parsed["ts_ms"] > 1735689600000  # > 2025-01-01


def test_crypto_encrypt_and_decrypt():
    plain = "SuperSecret_API_KEY_12345"
    encrypted = crypto.encrypt_secret(plain)
    assert encrypted != plain
    decrypted = crypto.decrypt_secret(encrypted)
    assert decrypted == plain

    # 历史明文兼容测试（解密失败应返回原值）
    assert crypto.decrypt_secret("plain_legacy_key") == "plain_legacy_key"
    assert crypto.decrypt_secret("") == ""

    # 脱敏掩码测试
    assert crypto.mask_secret("1234567890", head=2, tail=2) == "12******90"
    assert crypto.mask_secret("short", head=3, tail=3) == "*****"


def test_time_now_cn_and_awareness():
    now = ctime.now_cn()
    assert now.tzinfo is not None
    assert str(now.tzinfo) == "Asia/Shanghai"

    # ensure_cn_aware
    from datetime import datetime
    naive = datetime(2026, 1, 1, 12, 0, 0)
    aware = ctime.ensure_cn_aware(naive)
    assert aware.tzinfo is not None
    assert str(aware.tzinfo) == "Asia/Shanghai"


def test_jssafe_json_serialization():
    data = {
        "normal_int": 12345,
        "bool_val": True,
        "small_float": 3.14,
        "huge_snowflake_id": JS_MAX_SAFE_INT + 100,
        "nested": {
            "big_id": 247986912683757568
        },
        "id_list": [1, JS_MAX_SAFE_INT + 2, True]
    }
    json_str = dumps_jssafe(data)
    assert '"huge_snowflake_id":"9007199254741091"' in json_str or '"huge_snowflake_id": "9007199254741091"' in json_str
    assert '"big_id":"247986912683757568"' in json_str or '"big_id": "247986912683757568"' in json_str
    # bool 绝不能被转成 string
    assert '"bool_val":true' in json_str or '"bool_val": true' in json_str
    assert '"normal_int":12345' in json_str or '"normal_int": 12345' in json_str

