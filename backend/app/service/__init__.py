"""
Service 层 —— 业务逻辑编排

职责：
- 事务管理（with SessionLocal() 在此打开 / 提交）
- 业务规则校验（用户名重复、密码强度等）
- 跨模型操作、外部调用（邮件、消息队列）
- 不接触 Request / Response 对象，不抛 HTTP 状态码

调用约定：
- 抛 APIException（带业务 code），由上层路由捕获
- 返回普通 dict / dataclass / Pydantic 模型，不返回 ORM 对象
"""
from .user_service import UserService

__all__ = ["UserService"]
