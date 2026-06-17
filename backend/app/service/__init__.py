"""
Service 层 —— 业务逻辑编排

职责：
- 事务管理（with SessionLocal() 在此打开 / 提交）
- 业务规则校验
- 跨模型操作、外部调用

调用约定：
- 抛 APIException（带业务 code），由上层路由捕获
- 返回普通 dict，不返回 ORM 对象（避免 Session 关闭后访问字段崩溃）
"""
from .role_service import RoleService
from .user_service import UserService
from .menu_service import MenuService
from .audit_service import AuditService

__all__ = [
    "MenuService",
    "RoleService",
    "UserService",
    "AuditService",
]
