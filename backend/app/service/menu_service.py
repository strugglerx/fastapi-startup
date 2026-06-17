from typing import List, Optional

from app.boot import APIException
from app.db import SessionLocal, SysMenu, SysRoleMenu
from app.service.role_service import RoleService


def _to_bool(value) -> bool:
    return bool(value)


def _menu_to_dict(row: SysMenu) -> dict:
    return {
        "id": row.id,
        "menuKey": row.menu_key,
        "parentKey": row.parent_key,
        "title": row.title,
        "path": row.path,
        "component": row.component,
        "icon": row.icon,
        "sort": row.sort,
        "hidden": bool(row.hidden),
        "cacheable": bool(row.cacheable),
        "source": row.source or "code",
        "enabled": bool(row.enabled),
    }


class MenuService:
    GROUP_COMPONENT = "__group__"

    @classmethod
    def list_enabled(cls, user_role: str = "member", include_disabled: bool = False) -> List[dict]:
        with SessionLocal() as db:
            q = db.query(SysMenu)
            if not include_disabled:
                q = q.filter(SysMenu.enabled == True)  # noqa: E712
            rows = q.order_by(SysMenu.sort.asc(), SysMenu.id.asc()).all()
            if user_role == "admin":
                return [_menu_to_dict(row) for row in rows]

            grants = {
                row.menu_key
                for row in db.query(SysRoleMenu.menu_key)
                .filter(SysRoleMenu.role == user_role)
                .all()
            }
            rows = cls._filter_rows_by_grants(rows, grants)
            return [_menu_to_dict(row) for row in rows]

    @classmethod
    def _filter_rows_by_grants(cls, rows: List[SysMenu], grants: set[str]) -> List[SysMenu]:
        by_parent = {}
        for row in rows:
            by_parent.setdefault(row.parent_key, []).append(row)

        accepted = set()

        def visit(row: SysMenu) -> bool:
            visible_by_rule = bool(row.hidden) or row.menu_key in grants
            if not visible_by_rule:
                return False

            child_rows = by_parent.get(row.menu_key, [])
            kept_children = [child for child in child_rows if visit(child)]
            if row.component == "__group__" and not row.hidden and not kept_children:
                return False

            accepted.add(row.menu_key)
            return True

        for row in by_parent.get(None, []):
            visit(row)

        return [row for row in rows if row.menu_key in accepted]

    @classmethod
    def get_role_grants(cls, role: str) -> dict:
        with SessionLocal() as db:
            ordered_keys = [
                row.menu_key
                for row in db.query(SysMenu)
                .filter(SysMenu.enabled == True)  # noqa: E712
                .order_by(SysMenu.sort.asc(), SysMenu.id.asc())
                .all()
            ]
            granted = {
                row.menu_key
                for row in db.query(SysRoleMenu.menu_key)
                .filter(SysRoleMenu.role == role)
                .all()
            }
            return {
                "role": role,
                "menuKeys": [key for key in ordered_keys if key in granted],
            }

    @classmethod
    def set_role_grants(cls, role: str, menu_keys: List[str]) -> dict:
        role = (role or "").strip()
        if role == "admin":
            raise APIException("admin 角色无需配置授权", code=61006, status_code=400)
        if role not in RoleService.get_active_codes():
            raise APIException("角色不存在或已停用", code=61005, status_code=400)

        clean_keys = []
        seen = set()
        for menu_key in menu_keys or []:
            key = (menu_key or "").strip()
            if key and key not in seen:
                clean_keys.append(key)
                seen.add(key)

        with SessionLocal() as db:
            enabled_rows = db.query(SysMenu).filter(SysMenu.enabled == True).all()  # noqa: E712
            enabled_keys = {row.menu_key for row in enabled_rows}
            invalid = sorted(set(clean_keys) - enabled_keys)
            if invalid:
                raise APIException(f"菜单不存在或已禁用：{invalid}", code=61007, status_code=400)

            try:
                db.query(SysRoleMenu).filter(SysRoleMenu.role == role).delete(synchronize_session=False)
                for menu_key in clean_keys:
                    db.add(SysRoleMenu(role=role, menu_key=menu_key))
                db.commit()
            except Exception:
                db.rollback()
                raise

            return cls.get_role_grants(role)

    DEFAULT_CORE_GROUPS = {
        "g:system": {
            "title": "系统管理",
            "icon": "Settings",
            "sort": 90,
        }
    }

    DEFAULT_CORE_MENUS = {
        "dashboard": {
            "title": "控制台",
            "icon": "LayoutDashboard",
            "parentKey": None,
            "sort": 1,
        },
        "profile": {
            "title": "个人中心",
            "icon": "User",
            "parentKey": None,
            "sort": 2,
        },
        "system:admin": {
            "title": "账号管理",
            "icon": "Users",
            "parentKey": "g:system",
            "sort": 10,
        },
        "system:role": {
            "title": "角色与权限",
            "icon": "Shield",
            "parentKey": "g:system",
            "sort": 11,
        },
        "system:menu": {
            "title": "菜单管理",
            "icon": "Settings",
            "parentKey": "g:system",
            "sort": 12,
        },
        "system:settings": {
            "title": "系统设置",
            "icon": "Settings",
            "parentKey": "g:system",
            "sort": 13,
        },
        "system:audit": {
            "title": "审计日志",
            "icon": "FileText",
            "parentKey": "g:system",
            "sort": 14,
        },
        "system:file": {
            "title": "文件管理",
            "icon": "FolderOpen",
            "parentKey": "g:system",
            "sort": 15,
        },
        "system:dict": {
            "title": "数据字典",
            "icon": "BookOpen",
            "parentKey": "g:system",
            "sort": 16,
        },
        "system:product": {
            "title": "产品管理",
            "icon": "Grid",
            "parentKey": "g:system",
            "sort": 17,
        },
    }

    @classmethod
    def sync(cls, pages: List[dict]) -> dict:
        if not isinstance(pages, list):
            raise APIException("pages 必须是数组", code=61001, status_code=400)

        clean = []
        seen = set()
        dup = set()
        for page in pages:
            menu_key = (page.get("menuKey") or "").strip()
            if not menu_key:
                raise APIException("menuKey 不能为空", code=61002, status_code=400)
            if menu_key in seen:
                dup.add(menu_key)
            seen.add(menu_key)

            # 提取可能包含的默认初始化元数据字段
            parent_key = page.get("parentKey")
            if parent_key is not None:
                parent_key = str(parent_key).strip() or None

            title = page.get("title")
            if title is not None:
                title = str(title).strip() or None

            icon = page.get("icon")
            if icon is not None:
                icon = str(icon).strip() or None

            sort = page.get("sort")
            if sort is not None:
                try:
                    sort = int(sort)
                except (ValueError, TypeError):
                    sort = None

            hidden = page.get("hidden")
            if hidden is not None:
                hidden = _to_bool(hidden)

            clean.append({
                "menuKey": menu_key,
                "path": (page.get("path") or "").strip(),
                "component": (page.get("component") or "").strip(),
                "cacheable": _to_bool(page.get("cacheable")),
                "parentKey": parent_key,
                "title": title,
                "icon": icon,
                "sort": sort,
                "hidden": hidden,
            })
        if dup:
            raise APIException(f"menuKey 冲突：{sorted(dup)}", code=61003, status_code=400)

        added, updated, disabled = 0, 0, 0
        code_keys = {p["menuKey"] for p in clean}

        with SessionLocal() as db:
            existing = {
                row.menu_key: row
                for row in db.query(SysMenu).all()
            }

            # 自动创建缺少的系统内置或自定义分组（如 g:system）
            for page in clean:
                menu_key = page["menuKey"].strip()
                if menu_key not in existing:
                    core_meta = cls.DEFAULT_CORE_MENUS.get(menu_key)
                    p_key = page["parentKey"] or (core_meta["parentKey"] if core_meta else None)
                    if p_key and p_key not in existing:
                        if p_key.startswith("g:") or p_key in cls.DEFAULT_CORE_GROUPS:
                            group_meta = cls.DEFAULT_CORE_GROUPS.get(p_key) or {
                                "title": p_key[2:] if p_key.startswith("g:") and len(p_key) > 2 else p_key,
                                "icon": "Folder",
                                "sort": 90,
                            }
                            g_row = SysMenu(
                                menu_key=p_key,
                                parent_key=None,
                                title=group_meta["title"],
                                path="",
                                component=cls.GROUP_COMPONENT,
                                icon=group_meta["icon"],
                                sort=group_meta["sort"],
                                hidden=False,
                                cacheable=False,
                                source="ui",
                                enabled=True,
                            )
                            db.add(g_row)
                            existing[p_key] = g_row

            # 同步页面数据
            for page in clean:
                menu_key = page["menuKey"].strip()
                row = existing.get(menu_key)
                if row is None:
                    # 如果是新页面，优先使用传入的初始属性，其次使用默认内置核心页面配置，最后使用回落默认值
                    core_meta = cls.DEFAULT_CORE_MENUS.get(menu_key)
                    parent_key = page["parentKey"] or (core_meta["parentKey"] if core_meta else None)
                    title = page["title"] or (core_meta["title"] if core_meta else menu_key)
                    icon = page["icon"] or (core_meta["icon"] if core_meta else None)
                    
                    sort = page["sort"]
                    if sort is None:
                        sort = core_meta["sort"] if core_meta else 9999
                        
                    hidden = page["hidden"]
                    if hidden is None:
                        hidden = False

                    # 默认情况下，新同步的页面（如新开发的页面）处于禁用状态，供管理员在菜单管理中自行配置并启用
                    # 仅控制台与核心内置菜单默认启用，以确保基础入口可用
                    is_enabled = True if (menu_key == "dashboard" or menu_key in cls.DEFAULT_CORE_MENUS) else False

                    db.add(SysMenu(
                        menu_key=menu_key,
                        parent_key=parent_key,
                        title=title,
                        path=page["path"],
                        component=page["component"],
                        icon=icon,
                        sort=sort,
                        hidden=hidden,
                        cacheable=page["cacheable"],
                        source="code",
                        enabled=is_enabled,
                    ))
                    added += 1
                    continue

                if row.source == "ui":
                    raise APIException("UI 创建的分组 menuKey 与代码页面冲突", code=61010, status_code=400)

                row.source = "code"
                row.path = page["path"]
                row.component = page["component"]
                row.cacheable = page["cacheable"]
                # 保持数据库中现有的启用/禁用状态，不在此强制覆盖
                updated += 1

            for menu_key, row in existing.items():
                if row.source == "code" and menu_key not in code_keys:
                    # 如果代码中的页面定义已彻底删除，从数据库物理删除该菜单项及相关角色授权
                    db.query(SysRoleMenu).filter(SysRoleMenu.menu_key == menu_key).delete(synchronize_session=False)
                    db.delete(row)
                    disabled += 1

            db.commit()

        return {"added": added, "updated": updated, "disabled": disabled}

    @classmethod
    def update_meta(
        cls,
        menu_key: str,
        *,
        title: Optional[str] = None,
        icon: Optional[str] = None,
        parent_key: Optional[str] = None,
        sort: Optional[int] = None,
        hidden: Optional[bool] = None,
    ) -> dict:
        menu_key = (menu_key or "").strip()
        if not menu_key:
            raise APIException("menuKey 不能为空", code=61002, status_code=400)

        with SessionLocal() as db:
            row = db.query(SysMenu).filter(
                SysMenu.menu_key == menu_key,
                SysMenu.enabled == True,  # noqa: E712
            ).first()
            if not row:
                raise APIException("菜单项不存在或已禁用", code=61009, status_code=404)

            if parent_key is not None:
                row.parent_key = cls._validate_parent(db, menu_key, parent_key)
            if title is not None:
                row.title = title.strip()
            if icon is not None:
                row.icon = icon.strip() or None
            if sort is not None:
                row.sort = int(sort)
            if hidden is not None:
                row.hidden = bool(hidden)

            db.commit()
            db.refresh(row)
            return _menu_to_dict(row)

    @classmethod
    def create_group(
        cls,
        menu_key: str,
        title: str,
        icon: Optional[str] = None,
        parent_key: Optional[str] = None,
        sort: int = 9999,
    ) -> dict:
        menu_key = (menu_key or "").strip()
        title = (title or "").strip()
        if not menu_key:
            raise APIException("menuKey 不能为空", code=61002, status_code=400)
        if not menu_key.startswith("g:"):
            raise APIException("UI 分组 menuKey 必须以 g: 前缀开头", code=61011, status_code=400)
        if not title:
            raise APIException("title 不能为空", code=61012, status_code=400)

        with SessionLocal() as db:
            existing = db.query(SysMenu).filter(SysMenu.menu_key == menu_key).first()
            if existing:
                raise APIException(f"menuKey {menu_key} 已存在", code=61003, status_code=400)

            row = SysMenu(
                menu_key=menu_key,
                parent_key=cls._validate_parent(db, menu_key, parent_key),
                title=title,
                path="",
                component=cls.GROUP_COMPONENT,
                icon=(icon or "").strip() or None,
                sort=int(sort),
                hidden=False,
                cacheable=False,
                source="ui",
                enabled=True,
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return _menu_to_dict(row)

    @classmethod
    def ensure_source_migration(cls):
        """一次性迁移：把现存分组标记为 ui，其余保持 code。"""
        with SessionLocal() as db:
            rows = db.query(SysMenu).all()
            changed = False
            for row in rows:
                if row.component == cls.GROUP_COMPONENT and row.source != "ui":
                    row.source = "ui"
                    changed = True
                elif row.source not in ("code", "ui"):
                    row.source = "code"
                    changed = True
            if changed:
                db.commit()

    @classmethod
    def _validate_parent(cls, db, menu_key: str, parent_key: Optional[str]) -> Optional[str]:
        parent_key = (parent_key or "").strip()
        if not parent_key:
            return None
        if parent_key == menu_key:
            raise APIException("父级不能是自身", code=61015, status_code=400)

        parent = db.query(SysMenu).filter(
            SysMenu.menu_key == parent_key,
            SysMenu.enabled == True,  # noqa: E712
        ).first()
        if not parent:
            raise APIException("父级菜单不存在或已禁用", code=61016, status_code=400)
        if parent.component != cls.GROUP_COMPONENT:
            raise APIException("只能挂载到分组下", code=61017, status_code=400)

        cursor = parent
        visited = set()
        while cursor and cursor.parent_key:
            if cursor.parent_key == menu_key:
                raise APIException("父级不能造成循环", code=61018, status_code=400)
            if cursor.parent_key in visited:
                raise APIException("菜单树存在循环", code=61019, status_code=400)
            visited.add(cursor.parent_key)
            cursor = db.query(SysMenu).filter(
                SysMenu.menu_key == cursor.parent_key,
                SysMenu.enabled == True,  # noqa: E712
            ).first()
        return parent_key

    @classmethod
    def create_menu(cls, data: dict) -> dict:
        menu_key = (data.get("menuKey") or "").strip()
        if not menu_key:
            raise APIException("menuKey 不能为空", code=61002, status_code=400)
        
        comp = data.get("component") or "__group__"
        parent_key = data.get("parentKey")
        if comp == cls.GROUP_COMPONENT:
            parent_key = None

        with SessionLocal() as db:
            existing = db.query(SysMenu).filter(SysMenu.menu_key == menu_key).first()
            if existing:
                raise APIException(f"menuKey {menu_key} 已存在", code=61003, status_code=400)
                
            row = SysMenu(
                menu_key=menu_key,
                parent_key=parent_key,
                title=data.get("title") or menu_key,
                path=data.get("path") or "",
                component=comp,
                icon=data.get("icon"),
                sort=int(data.get("sort") or 0),
                hidden=bool(data.get("hidden")),
                cacheable=bool(data.get("cacheable")),
                enabled=bool(data.get("enabled", True)),
                source="ui",
            )
            db.add(row)
            db.commit()
            db.refresh(row)
            return _menu_to_dict(row)

    @classmethod
    def update_menu(cls, id: int, data: dict) -> dict:
        with SessionLocal() as db:
            row = db.query(SysMenu).filter(SysMenu.id == id).first()
            if not row:
                raise APIException("菜单项不存在", code=61009, status_code=404)
            
            menu_key = (data.get("menuKey") or "").strip()
            if menu_key and menu_key != row.menu_key:
                existing = db.query(SysMenu).filter(SysMenu.menu_key == menu_key, SysMenu.id != id).first()
                if existing:
                    raise APIException(f"menuKey {menu_key} 已存在", code=61003, status_code=400)
                row.menu_key = menu_key
            
            if "component" in data:
                row.component = data.get("component") or row.component
                if row.component == cls.GROUP_COMPONENT:
                    row.parent_key = None

            if "parentKey" in data:
                if row.component == cls.GROUP_COMPONENT:
                    row.parent_key = None
                else:
                    row.parent_key = data.get("parentKey")
                    
            if "title" in data:
                row.title = data.get("title") or row.title
            if "path" in data:
                row.path = data.get("path") or ""
            if "icon" in data:
                row.icon = data.get("icon")
            if "sort" in data:
                row.sort = int(data.get("sort") or 0)
            if "hidden" in data:
                row.hidden = bool(data.get("hidden"))
            if "cacheable" in data:
                row.cacheable = bool(data.get("cacheable"))
            if "enabled" in data:
                row.enabled = bool(data.get("enabled"))
                
            db.commit()
            db.refresh(row)
            return _menu_to_dict(row)

    @classmethod
    def delete_menu(cls, id: int) -> dict:
        with SessionLocal() as db:
            row = db.query(SysMenu).filter(SysMenu.id == id).first()
            if not row:
                raise APIException("菜单项不存在", code=61009, status_code=404)
            
            try:
                db.query(SysRoleMenu).filter(SysRoleMenu.menu_key == row.menu_key).delete(synchronize_session=False)
                db.delete(row)
                db.commit()
            except Exception:
                db.rollback()
                raise
            return {"id": id, "success": True}
