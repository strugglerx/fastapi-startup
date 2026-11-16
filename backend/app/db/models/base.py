"""ORM 基类、雪花主键工厂与共享列类型（JSON / MEDIUMTEXT）。"""
import json
import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, Text, TypeDecorator
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import DeclarativeBase

from app.core.snowflake import next_id as _sf


# ─────────────────────────────────────────────────────────────────────────
# 主键 / 外键引用通用工厂（雪花 ID）
#
# - 全部用 BIGINT UNSIGNED（雪花 ID 63 位 < 2^63，安全）
# - PK 默认值用 snowflake.next_id；不再仅依赖 autoincrement
# - 列出口 JSON 时由 app.library.json.dumps_jssafe 转 string，前端无感
# ─────────────────────────────────────────────────────────────────────────
_BIGINT_UNSIGNED = BigInteger().with_variant(mysql.BIGINT(unsigned=True), "mysql")


def SfPk():
    """雪花主键列。"""
    return Column(_BIGINT_UNSIGNED, primary_key=True, default=_sf)


class Base(DeclarativeBase):
    pass


class FlexibleJSONType(TypeDecorator):
    """自动处理字典和字符串的混合类型字段"""
    impl = Text  # 底层存储为 TEXT 类型
    # SQLAlchemy 2.0 要求 TypeDecorator 显式声明 cache 安全性；纯函数式无状态序列化
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, str):
            return value  # 字符串直接存储
        return json.dumps(value, ensure_ascii=False)  # 字典/列表等转为 JSON 字符串

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return json.loads(value)  # 尝试解析为 JSON
        except json.JSONDecodeError:
            return value  # 解析失败则返回原始字符串


class FlexibleMediumJSONType(FlexibleJSONType):
    """MySQL 下使用 MEDIUMTEXT，其他数据库保持 TEXT。"""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "mysql":
            return dialect.type_descriptor(mysql.MEDIUMTEXT())
        return dialect.type_descriptor(Text())


class MediumText(TypeDecorator):
    """MySQL 下使用 MEDIUMTEXT（~16MB），其他数据库保持 TEXT。

    用于存全文 / 章节原文 / 大工具结果等可能超 TEXT(65KB) 的纯文本字段。
    与 FlexibleMediumJSONType 区别：本类型不做 JSON 序列化，直接存字符串。
    """
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "mysql":
            return dialect.type_descriptor(mysql.MEDIUMTEXT())
        return dialect.type_descriptor(Text())

