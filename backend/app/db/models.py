"""SmartAI Database Models

约定：
- 加列不加 FK 约束（项目用 ALTER TABLE 自动迁移，不写 alembic）
- 关联用 *_id + index 即可
- 仅保留：后台账号 User / AccessKey / 动态菜单 sys_menu
"""
import pytz
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import DeclarativeBase

EAST_8_TIMEZONE = pytz.timezone("Asia/Shanghai")


def _now():
    return datetime.now(EAST_8_TIMEZONE).replace(microsecond=0)


class Base(DeclarativeBase):
    pass


# ─────────────────────────────────────────────────────────────────────────
# 后台账号 / AccessKey
# ─────────────────────────────────────────────────────────────────────────
class AccessKey(Base):
    __tablename__ = "access_keys"

    id          = Column(Integer, primary_key=True)
    secret_key  = Column(String(100), unique=True, nullable=False, comment="密钥内容")
    description = Column(String(255), comment="密钥描述")
    max_qps     = Column(Integer, default=10, comment="最大每秒请求数")
    created_by  = Column(Integer, nullable=True, index=True, comment="创建用户ID")
    created_at  = Column(sa.DateTime(timezone=True), default=_now, comment="创建时间")
    updated_at  = Column(sa.DateTime(timezone=True), onupdate=_now, comment="更新时间")
    deleted_at  = Column(sa.DateTime(timezone=True), nullable=True, comment="删除时间")


class User(Base):
    """后台账号表（内部人员：admin / member）

    用账号密码登录，是本项目唯一的账号体系。
    role:    admin | member（自由字符串，不再有 sys_role 表）
    fixed:   True 表示系统种子账号，不可删除/不可降级
    """
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True)
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


# ─────────────────────────────────────────────────────────────────────────
# 动态菜单（Admin Platform MVP）—— 代码优先，sync:menu 写入
# ─────────────────────────────────────────────────────────────────────────
class SysMenu(Base):
    __tablename__ = "sys_menu"
    __table_args__ = (
        sa.UniqueConstraint("menu_key", name="uk_menu_key"),
        sa.Index("idx_parent_key", "parent_key"),
        sa.Index("idx_enabled_sort", "enabled", "sort"),
        {"comment": "动态菜单"},
    )

    id         = Column(BigInteger().with_variant(mysql.BIGINT(unsigned=True), "mysql"), primary_key=True, autoincrement=True)
    menu_key   = Column(String(128), nullable=False, comment="业务唯一键，如 system:user")
    parent_key = Column(String(128), nullable=True, comment="父菜单 key，根节点为 NULL")
    title      = Column(String(128), nullable=False, comment="菜单标题")
    path       = Column(String(255), nullable=False, comment="路由 path")
    component  = Column(String(255), nullable=False, comment="逻辑组件键")
    icon       = Column(String(64), nullable=True)
    sort       = Column(Integer, nullable=False, default=0)
    hidden     = Column(Boolean, nullable=False, default=False)
    cacheable  = Column(Boolean, nullable=False, default=False)
    source     = Column(String(16), nullable=False, default="code", comment="code=代码同步页面，ui=UI 创建分组")
    enabled    = Column(Boolean, nullable=False, default=True, comment="0=代码已删除，软禁用")
    created_at = Column(sa.DateTime(timezone=True), default=_now, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at = Column(sa.DateTime(timezone=True), default=_now, onupdate=_now, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False)


class SysRoleMenu(Base):
    __tablename__ = "sys_role_menu"
    __table_args__ = (
        sa.UniqueConstraint("role", "menu_key", name="uk_role_menu"),
    )

    id         = Column(BigInteger().with_variant(mysql.BIGINT(unsigned=True), "mysql"), primary_key=True, autoincrement=True)
    role       = Column(String(64), nullable=False, index=True, comment="硬编码角色：admin / member")
    menu_key   = Column(String(128), nullable=False, comment="授权菜单 key")
    created_at = Column(DateTime, server_default=sa.func.now())
    updated_at = Column(DateTime, server_default=sa.func.now(), onupdate=sa.func.now())


class SysRole(Base):
    __tablename__ = "sys_role"

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    code        = Column(String(64), nullable=False, unique=True)
    name        = Column(String(64), nullable=False)
    description = Column(String(255), nullable=True)
    enabled     = Column(Boolean, nullable=False, default=True)
    builtin     = Column(Boolean, nullable=False, default=False)
    sort        = Column(Integer, nullable=False, default=0)
    created_at  = Column(DateTime, server_default=sa.func.now())
    updated_at  = Column(DateTime, server_default=sa.func.now(), onupdate=sa.func.now())


class SysAuditLog(Base):
    __tablename__ = "sys_audit_log"
    __table_args__ = (
        sa.Index("idx_audit_user_id", "user_id"),
        sa.Index("idx_audit_created_at", "created_at"),
        {"comment": "操作审计日志"},
    )

    id           = Column(BigInteger().with_variant(mysql.BIGINT(unsigned=True), "mysql"), primary_key=True, autoincrement=True)
    user_id      = Column(Integer, nullable=True, comment="操作用户ID")
    username     = Column(String(64), nullable=True, comment="操作用户名")
    action       = Column(String(100), nullable=False, comment="操作动作编码")
    description  = Column(String(255), nullable=True, comment="操作描述")
    method       = Column(String(16), nullable=False, comment="请求方法")
    path         = Column(String(255), nullable=False, comment="请求路径")
    query_params = Column(Text, nullable=True, comment="查询参数")
    request_body = Column(Text, nullable=True, comment="请求体参数")
    status_code  = Column(Integer, nullable=False, comment="HTTP状态码")
    ip_address   = Column(String(45), nullable=True, comment="IP地址")
    user_agent   = Column(String(512), nullable=True, comment="浏览器UserAgent")
    cost_time    = Column(Integer, nullable=False, comment="耗时(ms)")
    created_at   = Column(sa.DateTime(timezone=True), default=_now, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False)
