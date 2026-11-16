"""系统底层数据模型（菜单、角色、审计日志、文件存储、数据字典）。"""
import sqlalchemy as sa
from sqlalchemy import BigInteger, Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.dialects import mysql

from app.core.time import now_cn as _now
from .base import (
    Base,
    SfPk,
    _BIGINT_UNSIGNED,
    FlexibleJSONType,
)


class SysMenu(Base):
    __tablename__ = "sys_menu"
    __table_args__ = (
        sa.UniqueConstraint("menu_key", name="uk_menu_key"),
        sa.Index("idx_parent_key", "parent_key"),
        sa.Index("idx_enabled_sort", "enabled", "sort"),
        {"comment": "动态菜单"},
    )

    id         = SfPk()
    menu_key   = Column(String(128), nullable=False, comment="业务唯一键，如 system:user")
    parent_key = Column(String(128), nullable=True, comment="父菜单 key，根节点为 NULL")
    title      = Column(String(128), nullable=False, comment="菜单标题")
    path       = Column(String(255), nullable=False, comment="路由 path")
    component  = Column(String(255), nullable=False, comment="逻辑组件键")
    icon       = Column(String(64), nullable=True)
    sort       = Column(Integer, nullable=False, default=0)
    hidden     = Column(Boolean, nullable=False, default=False)
    admin_sidebar_hidden = Column(Boolean, nullable=False, default=False, comment="仅对 admin 隐藏侧栏入口；不影响访问权与角色授权")
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

    id         = SfPk()
    role       = Column(String(64), nullable=False, index=True, comment="角色编码")
    menu_key   = Column(String(128), nullable=False, comment="授权菜单 key")
    created_at = Column(DateTime, server_default=sa.func.now())
    updated_at = Column(DateTime, server_default=sa.func.now(), onupdate=sa.func.now())


class SysRole(Base):
    __tablename__ = "sys_role"

    id          = SfPk()
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

    id           = SfPk()
    user_id      = Column(_BIGINT_UNSIGNED, nullable=True, comment="操作用户ID")
    username     = Column(String(64), nullable=True, comment="操作用户名")
    action       = Column(String(100), nullable=False, comment="操作动作编码")
    description  = Column(String(255), nullable=True, comment="操作描述")
    method       = Column(String(16), nullable=False, comment="请求方法")
    path         = Column(String(255), nullable=False, comment="请求路径")
    query_params = Column(Text, nullable=True, comment="查询参数")
    request_body = Column(Text, nullable=True, comment="请求体参数")
    status_code  = Column(Integer, nullable=False, comment="HTTP状态码")
    ip_address   = Column(String(45), nullable=True, comment="IP地址")
    ip_location  = Column(String(100), nullable=True, comment="IP归属地")
    user_agent   = Column(String(512), nullable=True, comment="浏览器UserAgent")
    cost_time    = Column(Integer, nullable=False, comment="耗时(ms)")
    created_at   = Column(sa.DateTime(timezone=True), default=_now, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False)


class SysFile(Base):
    __tablename__ = "sys_files"
    __table_args__ = (
        sa.Index("idx_file_hash", "hash_md5"),
        {"comment": "系统上传文件记录"},
    )

    id         = SfPk()
    filename   = Column(String(255), nullable=False, comment="原始文件名")
    filepath   = Column(String(512), nullable=False, comment="文件相对存储路径")
    file_size  = Column(Integer, nullable=False, comment="文件大小(字节)")
    mime_type  = Column(String(128), nullable=True, comment="文件MIME类型")
    hash_md5   = Column(String(32), nullable=True, comment="文件MD5哈希值")
    created_by = Column(_BIGINT_UNSIGNED, nullable=True, comment="上传用户ID")
    created_at = Column(sa.DateTime(timezone=True), default=_now, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False)


class SysDict(Base):
    __tablename__ = "sys_dict"
    __table_args__ = (
        {"comment": "数据字典分类"},
    )

    id          = SfPk()
    code        = Column(String(64), unique=True, nullable=False, comment="字典编码")
    name        = Column(String(64), nullable=False, comment="字典名称")
    description = Column(String(255), nullable=True, comment="描述")
    enabled     = Column(Boolean, default=True, nullable=False, comment="是否启用")
    created_at  = Column(sa.DateTime(timezone=True), default=_now, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at  = Column(sa.DateTime(timezone=True), default=_now, onupdate=_now, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False)


class SysDictItem(Base):
    __tablename__ = "sys_dict_item"
    __table_args__ = (
        sa.UniqueConstraint("dict_code", "value", name="uk_dict_code_value"),
        sa.Index("idx_dict_item_code_sort", "dict_code", "sort"),
        {"comment": "数据字典明细"},
    )

    id         = SfPk()
    dict_code  = Column(String(64), nullable=False, comment="所属字典编码")
    label      = Column(String(128), nullable=False, comment="字典标签")
    value      = Column(String(128), nullable=False, comment="字典键值")
    sort       = Column(Integer, default=0, nullable=False, comment="排序号")
    enabled    = Column(Boolean, default=True, nullable=False, comment="是否启用")
    created_at = Column(sa.DateTime(timezone=True), default=_now, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False)
    updated_at = Column(sa.DateTime(timezone=True), default=_now, onupdate=_now, server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False)


class StorageConfig(Base):
    """存储配置表"""
    __tablename__ = "storage_config"

    id         = SfPk()
    provider   = Column(String(32), nullable=False, default="local", comment="local | qiniu | s3")
    config     = Column(FlexibleJSONType, nullable=True, comment="配置详情JSON")
    is_default = Column(Boolean, default=False, nullable=False, comment="是否为默认存储")
    created_at = Column(sa.DateTime(timezone=True), default=_now)
    updated_at = Column(sa.DateTime(timezone=True), onupdate=_now)
