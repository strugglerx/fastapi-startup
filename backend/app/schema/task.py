from pydantic import BaseModel
from typing import Optional

class TaskConfig(BaseModel):
    """异步任务配置模型 - 适用于后台任务场景"""
    task_uuid: str
    params: dict          # 任务参数（如 {"input_file": "data.csv"}）
    callback_url: Optional[str] = None    # 任务完成后回调的 URL
    unique_id: Optional[str] = None          # 任务唯一标识

class TaskResponse(BaseModel):
    """异步任务响应模型"""
    task_id: str
    status: str           # "pending" | "success" | "failed"
    result: Optional[dict] = None
