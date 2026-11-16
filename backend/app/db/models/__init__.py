"""Database Models

约定：
- 加列不加 FK 约束（项目用 ALTER TABLE 自动迁移，不写 alembic）
- 关联用 *_id + index 即可
- 按业务域拆分到子模块；本文件统一 re-export，保持 `from app.db.models import X` 不变
"""
from .base import (
    Base,
    SfPk,
    _BIGINT_UNSIGNED,
    FlexibleJSONType,
    FlexibleMediumJSONType,
    MediumText,
)
from .auth import AccessKey, User, RefreshToken
from .system import (
    SysMenu,
    SysRoleMenu,
    SysRole,
    SysAuditLog,
    SysFile,
    SysDict,
    SysDictItem,
    StorageConfig,
)

__all__ = [
    "Base",
    "SfPk",
    "_BIGINT_UNSIGNED",
    "FlexibleJSONType",
    "FlexibleMediumJSONType",
    "MediumText",
    "AccessKey",
    "User",
    "RefreshToken",
    "SysMenu",
    "SysRoleMenu",
    "SysRole",
    "SysAuditLog",
    "SysFile",
    "SysDict",
    "SysDictItem",
    "StorageConfig",
]

