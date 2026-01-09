from fastapi import HTTPException

class APIException(HTTPException):
    """自定义API异常"""
    def __init__(self, msg: str, code: int = 1, status_code: int = 200):
        self.code = code  # 业务错误码
        super().__init__(
            status_code=status_code,
            detail={
                "code": code,
                "msg": msg  # 直接传入错误信息
            }
        )
