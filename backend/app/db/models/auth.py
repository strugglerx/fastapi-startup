"""账号 / AccessKey / RefreshToken。"""
import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, Integer, String, Text, Boolean, DateTime

from app.core.time import now_cn as _now
from .base import (
    Base,
    SfPk,
    _BIGINT_UNSIGNED,
)


class AccessKey(Base):
    __tablename__ = "access_keys"

    id          = SfPk()
    secret_key  = Column(String(255), unique=True, nullable=False, comment="密钥内容")
    description = Column(String(255), comment="密钥描述")
    max_qps     = Column(Integer, default=10, comment="最大每秒请求数")
    expires_at  = Column(sa.DateTime(timezone=True), nullable=True, comment="过期时间（NULL=永不过期）")
    is_active   = Column(Boolean, default=True, nullable=False, server_default=sa.text("1"), comment="启用 True / 禁用 False")
    created_by  = Column(_BIGINT_UNSIGNED, nullable=True, index=True, comment="创建用户ID")
    created_at  = Column(sa.DateTime(timezone=True), default=_now, comment="创建时间")
    updated_at  = Column(sa.DateTime(timezone=True), onupdate=_now, comment="更新时间")
    deleted_at  = Column(sa.DateTime(timezone=True), nullable=True, comment="删除时间")


class User(Base):
    """后台账号表（内部人员：admin / member）

    用账号密码登录，是本项目唯一的账号体系。
    role:    admin | member（自由字符串，结合 sys_role 表）
    fixed:   True 表示系统种子账号，不可删除/不可降级
    """
    __tablename__ = "users"

    id              = SfPk()
    username        = Column(String(50),  unique=True, nullable=False, comment="用户名（登录别名）")
    email           = Column(String(120), unique=True, nullable=True,  comment="邮箱（前端主登录标识）")
    full_name       = Column(String(80),  nullable=True, comment="显示名")
    role            = Column(String(32),  default="member", nullable=False, comment="admin | member")
    hashed_password = Column(String(128), nullable=False, comment="bcrypt 哈希")
    last_login      = Column(sa.DateTime(timezone=True))
    last_login_at   = Column(DateTime, nullable=True, comment="最后登录时间")
    fixed           = Column(Boolean, default=False, comment="系统种子账号（不可删/不可降级）")
    is_active       = Column(Boolean, default=True, nullable=False, comment="启用 True / 禁用 False；fixed admin 永远 True")
    created_at      = Column(sa.DateTime(timezone=True), default=_now)
    updated_at      = Column(sa.DateTime(timezone=True), onupdate=_now)
    deleted_at      = Column(sa.DateTime(timezone=True), nullable=True)


class RefreshToken(Base):
    """Refresh Token 存储。

    设计：
    - access token 是无状态短期 JWT（默认 8h），refresh token 是 opaque 随机串（默认 30d）
    - 落库时存 sha256(token) 不存原文，数据库泄露后无法伪造
    - rotate：每次换发新 access 时同时轮转 refresh 并吊销旧的（防重放）
    - 主动 logout 时吊销当前 refresh
    """
    __tablename__ = "refresh_tokens"

    id          = SfPk()
    user_id     = Column(_BIGINT_UNSIGNED, nullable=False, index=True, comment="用户 ID")
    token_hash  = Column(String(64), nullable=False, unique=True, comment="sha256(refresh_token) hex")
    expires_at  = Column(sa.DateTime(timezone=True), nullable=False, index=True, comment="过期时间")
    revoked_at  = Column(sa.DateTime(timezone=True), nullable=True, index=True, comment="吊销时间（rotate / logout）")
    user_agent  = Column(String(255), nullable=True, comment="登录 UA（审计用）")
    client_ip   = Column(String(64),  nullable=True, comment="登录 IP（审计用）")
    created_at  = Column(sa.DateTime(timezone=True), default=_now, comment="签发时间")

