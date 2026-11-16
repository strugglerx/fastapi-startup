"""用户 & 管理员服务（拆自原 user_service.py 724 行 → 6 个 ≤175 行模块）。

外部依然 `from app.service import UserService` 一致使用，方法签名 100% 不变。

子模块职责：
- `_helpers.py`        —— 共享 helpers（refresh token / 登录锁定 / 序列化），所有 mixin 共用
- `_auth.py`           —— login / refresh_token / refresh_with_refresh_token / revoke_refresh_token
- `_me.py`             —— get_me / update_self_profile / change_password
- `_password_reset.py` —— request_password_reset / confirm_password_reset
- `_admin_crud.py`     —— register / create_admin / list_admins / update_admin /
                          reset_password / delete_admin + legacy list_users/delete_user
- `_bootstrap.py`      —— ensure_seed_admin / _seed_email / _seed_username

UserService = (_AuthMixin, _MeMixin, _PasswordResetMixin, _AdminCrudMixin, _BootstrapMixin)
"""
from ._admin_crud import _AdminCrudMixin
from ._auth import _AuthMixin
from ._bootstrap import _BootstrapMixin
from ._me import _MeMixin
from ._password_reset import _PasswordResetMixin


class UserService(
    _AuthMixin,
    _MeMixin,
    _PasswordResetMixin,
    _AdminCrudMixin,
    _BootstrapMixin,
):
    """用户 & 管理员总服务门面。所有方法见各 mixin 文件。"""
    pass


__all__ = ["UserService"]
