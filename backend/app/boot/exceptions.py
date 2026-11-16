from fastapi import HTTPException

class APIException(HTTPException):
    """自定义API异常。

    所有业务代码统一抛这个；框架会按 `{code, msg}` 统一响应。
    暴露 `self.msg` / `self.code` 作为公开属性。
    """
    def __init__(self, msg: str, code: int = 1, status_code: int = 200):
        self.code = code     # 业务错误码
        self.msg = msg       # 业务错误文本（独立暴露，方便 except 块自取）
        super().__init__(
            status_code=status_code,
            detail={"code": code, "msg": msg},
        )
