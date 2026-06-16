from pydantic import BaseModel, Field


class LoginReq(BaseModel):
    account: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1, max_length=128)
