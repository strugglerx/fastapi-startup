from typing import Generic, Optional, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """统一响应模型：code + data + msg"""
    code: int = 0
    data: Optional[T] = None
    msg: str = ""
