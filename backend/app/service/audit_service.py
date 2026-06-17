"""审计日志 Service"""
from typing import Optional, Dict, Any
from sqlalchemy import desc
from app.db import SessionLocal, SysAuditLog

def _log_to_dict(row: SysAuditLog) -> dict:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "username": row.username,
        "action": row.action,
        "description": row.description,
        "method": row.method,
        "path": row.path,
        "query_params": row.query_params,
        "request_body": row.request_body,
        "status_code": row.status_code,
        "ip_address": row.ip_address,
        "user_agent": row.user_agent,
        "cost_time": row.cost_time,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }

class AuditService:
    @classmethod
    def list_logs(
        cls,
        page: int = 1,
        size: int = 20,
        username: Optional[str] = None,
        action: Optional[str] = None,
        status_code: Optional[int] = None,
    ) -> Dict[str, Any]:
        page = max(1, page)
        size = max(1, min(size, 100))
        
        with SessionLocal() as db:
            query = db.query(SysAuditLog)
            if username:
                query = query.filter(SysAuditLog.username.like(f"%{username.strip()}%"))
            if action:
                query = query.filter(SysAuditLog.action.like(f"%{action.strip()}%"))
            if status_code is not None:
                query = query.filter(SysAuditLog.status_code == status_code)
                
            total = query.count()
            rows = query.order_by(desc(SysAuditLog.created_at)).offset((page - 1) * size).limit(size).all()
            
            return {
                "total": total,
                "items": [_log_to_dict(row) for row in rows],
                "page": page,
                "size": size,
            }
