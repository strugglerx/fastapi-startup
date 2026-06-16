from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["公开接口"])


@router.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse("app/public/index.html")


@router.get("/api/health", name="服务健康检查")
async def health_check():
    return {"status": "ok"}
