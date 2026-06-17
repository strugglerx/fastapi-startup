from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.api.v1.deps import require_permission
from app.service import AuditService

router = APIRouter(prefix="/audit", tags=["审计日志"])

@router.get("/list")
async def list_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    username: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    status_code: Optional[int] = Query(None),
    _user=Depends(require_permission("system:audit")),
):
    return AuditService.list_logs(
        page=page,
        size=size,
        username=username,
        action=action,
        status_code=status_code,
    )
