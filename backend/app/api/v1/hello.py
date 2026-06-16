from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["示例"])


class HelloResponse(BaseModel):
    message: str
    status: str
    version: str
    docs: str


class PingResponse(BaseModel):
    status: str


@router.get("/hello", summary="Hello World", response_model=HelloResponse)
async def hello_world() -> HelloResponse:
    return HelloResponse(
        message="Hello, base scaffold!",
        status="success",
        version="1.0.0",
        docs="/docs",
    )


@router.get("/ping", summary="健康检查", response_model=PingResponse)
async def ping() -> PingResponse:
    return PingResponse(status="ok")
