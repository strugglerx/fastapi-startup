import json
import time
import asyncio
from fastapi import FastAPI, Request
from anyio.to_thread import run_sync
from app.db import SessionLocal, SysAuditLog
from app.boot import logger

_SKIP_AUDIT_PREFIXES = ("/docs", "/openapi.json", "/redoc", "/doc/", "/health", "/favicon.ico")

def determine_action(method: str, path: str) -> str:
    path_clean = path.strip("/")
    parts = [p for p in path_clean.split("/") if p and not p.isdigit()]
    path_key = ":".join(parts)
    
    if "auth:login" in path_key:
        return "auth:login"
    if "auth:logout" in path_key:
        return "auth:logout"
        
    action_map = {
        "POST": "create",
        "PUT": "update",
        "PATCH": "update",
        "DELETE": "delete"
    }
    suffix = action_map.get(method, "action")
    
    if "api:v1:admin" in path_key:
        return f"sys:admin:{suffix}"
    if "api:v1:role" in path_key:
        if "grants" in path_key:
            return "sys:role:grants"
        return f"sys:role:{suffix}"
    if "api:menu" in path_key:
        if "sync" in path_key:
            return "sys:menu:sync"
        return f"sys:menu:{suffix}"
        
    module = parts[-1] if parts else "system"
    if len(parts) > 2 and parts[0] == "api" and parts[1] == "v1":
        module = parts[2]
    return f"sys:{module}:{suffix}"

def determine_description(method: str, path: str, body_bytes: bytes) -> str:
    action = determine_action(method, path)
    
    desc_map = {
        "auth:login": "用户登录",
        "auth:logout": "用户登出",
        "sys:admin:create": "创建系统账号",
        "sys:admin:update": "编辑系统账号",
        "sys:admin:delete": "删除系统账号",
        "sys:role:create": "创建系统角色",
        "sys:role:update": "编辑系统角色",
        "sys:role:delete": "删除系统角色",
        "sys:role:grants": "更新角色菜单授权",
        "sys:menu:create": "创建菜单",
        "sys:menu:update": "编辑菜单",
        "sys:menu:delete": "删除菜单",
        "sys:menu:sync": "同步系统菜单",
    }
    
    if action in desc_map:
        return desc_map[action]
        
    method_desc = {
        "POST": "新建",
        "PUT": "修改",
        "PATCH": "更新",
        "DELETE": "删除"
    }.get(method, "操作")
    
    parts = [p for p in path.strip("/").split("/") if p and not p.isdigit()]
    module = parts[-1] if parts else "模块"
    if len(parts) > 2 and parts[0] == "api" and parts[1] == "v1":
        module = parts[2]
        
    module_zh = {
        "user": "用户",
        "settings": "系统配置",
        "menu": "菜单",
        "role": "角色",
        "admin": "账号"
    }.get(module, module)
    
    return f"{method_desc}{module_zh}"

async def save_audit_log(**kwargs):
    try:
        def _save():
            with SessionLocal() as db:
                log = SysAuditLog(**kwargs)
                db.add(log)
                db.commit()
        await run_sync(_save)
    except Exception as e:
        logger.error(f"Failed to save audit log: {e}")

def setup_audit_log(app: FastAPI):
    @app.middleware("http")
    async def audit_log_middleware(request: Request, call_next):
        method = request.method
        path = request.url.path
        is_mutative = method in ("POST", "PUT", "DELETE", "PATCH")
        skip = any(path.startswith(p) for p in _SKIP_AUDIT_PREFIXES)

        if not is_mutative or skip:
            return await call_next(request)

        body_bytes = b""
        try:
            body_bytes = await request.body()
            async def receive():
                return {"type": "http.request", "body": body_bytes, "more_body": False}
            request._receive = receive
        except Exception as e:
            logger.debug(f"Audit log failed to read request body: {e}")

        start_time = time.time()
        try:
            response = await call_next(request)
            cost_time = int((time.time() - start_time) * 1000)
            
            user = getattr(request.state, "user", None)
            user_id = user.id if user else None
            username = user.username if user else None
            
            if not username and path == "/api/v1/auth/login":
                try:
                    payload = json.loads(body_bytes.decode("utf-8"))
                    username = payload.get("username") or payload.get("email")
                except:
                    pass

            status_code = response.status_code
            
            asyncio.create_task(
                save_audit_log(
                    user_id=user_id,
                    username=username,
                    action=determine_action(method, path),
                    description=determine_description(method, path, body_bytes),
                    method=method,
                    path=path,
                    query_params=str(request.query_params) if request.query_params else None,
                    request_body=body_bytes.decode("utf-8", errors="ignore")[:4000] if body_bytes else None,
                    status_code=status_code,
                    ip_address=request.client.host if request.client else "",
                    user_agent=request.headers.get("user-agent", "")[:512],
                    cost_time=cost_time
                )
            )
            
            return response
        except Exception as e:
            cost_time = int((time.time() - start_time) * 1000)
            user = getattr(request.state, "user", None)
            user_id = user.id if user else None
            username = user.username if user else None
            
            asyncio.create_task(
                save_audit_log(
                    user_id=user_id,
                    username=username,
                    action=determine_action(method, path),
                    description=f"异常: {str(e)[:200]}",
                    method=method,
                    path=path,
                    query_params=str(request.query_params) if request.query_params else None,
                    request_body=body_bytes.decode("utf-8", errors="ignore")[:4000] if body_bytes else None,
                    status_code=500,
                    ip_address=request.client.host if request.client else "",
                    user_agent=request.headers.get("user-agent", "")[:512],
                    cost_time=cost_time
                )
            )
            raise e
