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
        "ip_location": row.ip_location,
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

    @classmethod
    def scrub_history(cls) -> dict:
        """一次性把历史 request_body 跑一遍脱敏。
        - 仅处理可能含敏感字段的路径（_REDACT_FULL_PATHS）或包含敏感关键字的 JSON body
        - 处理完写一个标记到 Redis 避免重复跑：audit_scrub_done = "1" / 30 天
        """
        from app.core.redis_pool import RedisPool
        from app.middleware.audit_log import scrub_request_body
        from app.boot import logger

        try:
            r = RedisPool.get_redis()
            if r.get("audit_scrub_done") == b"1" or r.get("audit_scrub_done") == "1":
                return {"skipped": True, "reason": "already_done"}
        except Exception as e:
            logger.debug(f"audit scrub redis check skipped: {e}")
            r = None

        scanned = 0
        scrubbed = 0
        with SessionLocal() as db:
            rows = db.query(SysAuditLog).filter(
                SysAuditLog.request_body.isnot(None),
                SysAuditLog.request_body != "",
            ).yield_per(500)

            for row in rows:
                scanned += 1
                if not row.request_body:
                    continue
                cleaned = scrub_request_body(row.request_body.encode("utf-8"), row.path or "")
                if cleaned != row.request_body:
                    row.request_body = cleaned
                    scrubbed += 1
                if scrubbed and scrubbed % 500 == 0:
                    db.commit()
            db.commit()

        if r is not None:
            try:
                r.setex("audit_scrub_done", 30 * 24 * 3600, "1")
            except Exception:
                pass

        logger.info(f"✓ 审计日志历史脱敏：扫 {scanned} 行，改写 {scrubbed} 行")
        return {"scanned": scanned, "scrubbed": scrubbed}

    @classmethod
    def clean_old_logs(cls, retention_days: int) -> int:
        """删除 retention_days 之前的所有审计日志"""
        from datetime import datetime, timedelta
        import pytz
        
        EAST_8_TIMEZONE = pytz.timezone("Asia/Shanghai")
        cutoff = datetime.now(EAST_8_TIMEZONE) - timedelta(days=retention_days)
        cutoff = cutoff.replace(microsecond=0)
        
        with SessionLocal() as db:
            try:
                deleted = db.query(SysAuditLog).filter(SysAuditLog.created_at < cutoff).delete()
                db.commit()
                return deleted
            except Exception as e:
                db.rollback()
                raise e
