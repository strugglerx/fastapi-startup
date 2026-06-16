"""
框架级插件：CORS、响应包装、异常处理、自定义 Server 头。
所有插件通过 app.use(setup_xxx) 挂载。

不放业务中间件 —— 业务中间件请到 app/middleware/。
"""
import re
import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .exceptions import APIException
from .config import app_config
from .logger import logger


# ────────────────────────────────────────────
# CORS
# ────────────────────────────────────────────
def setup_cors(app: FastAPI):
    from fastapi.middleware.cors import CORSMiddleware

    origins = app_config.cors_origins_list

    if "*" in origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=".*",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("CORS: 允许所有域名 (正则模式 + 凭证)")
        return

    regex_patterns = []
    for origin in origins:
        clean = origin.replace("http://", "").replace("https://", "").strip("/")
        if not clean:
            continue
        regex_patterns.append(rf"^https?://([^/]+\.)?{re.escape(clean)}(:[0-9]+)?$")

    if regex_patterns:
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex="|".join(regex_patterns),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info(f"CORS: 允许域名及子域名: {origins}")
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info(f"CORS: 允许指定域名: {origins}")


# ────────────────────────────────────────────
# 自定义 Server 头
# ────────────────────────────────────────────
def setup_custom_server(app: FastAPI):
    @app.middleware("http")
    async def server_header(request: Request, call_next):
        response = await call_next(request)
        response.headers["Server"] = "struggler/1.0"
        return response


# ────────────────────────────────────────────
# Gzip 压缩（可选启用）
# ────────────────────────────────────────────
def setup_compression(app: FastAPI):
    from fastapi.middleware.gzip import GZipMiddleware
    app.add_middleware(GZipMiddleware)


# ────────────────────────────────────────────
# 统一响应包装：{code, data} 或 {code, msg}
# ────────────────────────────────────────────
_SKIP_WRAP_PREFIXES = ("/docs", "/redoc", "/openapi.json", "/doc/")


def _is_wrapped_response(data) -> bool:
    """更稳健的判断：dict 且同时包含 code + (data 或 msg)。"""
    if not isinstance(data, dict):
        return False
    if "code" not in data:
        return False
    return "data" in data or "msg" in data


def setup_stand_response(app: FastAPI):
    async def response_wrapper_middleware(request: Request, call_next):
        try:
            response = await call_next(request)
        except APIException:
            raise
        except Exception as e:
            logger.exception("响应包装中间件捕获未处理异常")
            return JSONResponse(status_code=500, content={"code": 500, "msg": str(e)})

        # 跳过文档/规范路径
        if any(request.url.path.startswith(p) for p in _SKIP_WRAP_PREFIXES):
            return response

        ctype = response.headers.get("content-type", "")
        if "application/json" not in ctype or response.status_code != 200:
            return response

        # 流式响应
        if isinstance(response, StreamingResponse):
            return _wrap_streaming(response)

        return await _wrap_regular(response)

    app.middleware("http")(response_wrapper_middleware)


def _wrap_streaming(response: StreamingResponse) -> StreamingResponse:
    async def gen():
        chunks = []
        try:
            async for chunk in response.body_iterator:
                chunks.append(chunk)
            full_body = b"".join(chunks).decode()
            try:
                data = json.loads(full_body)
                if not _is_wrapped_response(data):
                    data = {"code": 0, "data": data}
                yield json.dumps(data, ensure_ascii=False).encode()
            except json.JSONDecodeError:
                yield full_body.encode()
        except Exception as e:
            logger.error(f"流式响应处理错误: {e}")
            yield json.dumps({"code": 1, "msg": "Stream processing failed"}, ensure_ascii=False).encode()
        finally:
            close = getattr(getattr(response, "body_iterator", None), "close", None)
            if close:
                try:
                    await close()
                except Exception:
                    pass

    headers = dict(response.headers)
    headers.pop("content-length", None)
    headers.pop("content-type", None)
    return StreamingResponse(
        status_code=response.status_code,
        content=gen(),
        media_type="application/json",
        headers=headers,
    )


async def _wrap_regular(response):
    body = b""
    body_consumed = False
    if hasattr(response, "body") and response.body is not None:
        body = response.body
    elif hasattr(response, "body_iterator"):
        chunks = []
        async for chunk in response.body_iterator:
            chunks.append(chunk)
        body = b"".join(chunks)
        body_consumed = True

    if not body:
        return response

    try:
        data = json.loads(body)
    except Exception as e:
        logger.warning(f"JSON 解析失败，保留原响应: {e}")
        if body_consumed:
            from starlette.responses import Response
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type"),
            )
        return response

    if not _is_wrapped_response(data):
        data = {"code": 0, "data": data}

    headers = dict(response.headers)
    headers.pop("content-length", None)
    headers.pop("content-type", None)
    return JSONResponse(status_code=response.status_code, content=data, headers=headers)


# ────────────────────────────────────────────
# 异常处理：保留真实 HTTP 状态码 + body 内 code 业务码
# ────────────────────────────────────────────
def setup_exception(app: FastAPI):
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    _STATUS_MESSAGES = {
        400: "请求格式错误",
        401: "未授权访问",
        403: "禁止访问",
        404: "接口不存在",
        405: "请求方法不允许",
        408: "请求超时",
        413: "请求体过大",
        422: "参数验证失败",
        429: "请求过于频繁",
        500: "服务器内部错误",
        502: "网关错误",
        503: "服务暂时不可用",
    }

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        if not errors:
            return JSONResponse(status_code=200, content={"code": 422, "msg": "请求参数验证失败"})

        first = errors[0]
        loc = first.get("loc", [])
        field = loc[-1] if len(loc) > 1 else (loc[0] if loc else "参数")
        msg_type = first.get("type", "")
        msg = first.get("msg", "")

        if "missing" in msg_type:
            error_msg = f"缺少必填参数: {field}"
        elif msg_type.startswith("type_error") or msg_type.startswith("int_") or msg_type.startswith("string_"):
            error_msg = f"参数类型错误: {field} ({msg})"
        else:
            error_msg = f"参数验证失败: {field} - {msg}"

        if len(errors) > 1:
            error_msg += f" (共 {len(errors)} 个错误)"

        # HTTP 永远 200，业务结果由 body code 表示
        return JSONResponse(status_code=200, content={"code": 422, "msg": error_msg})

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        base = _STATUS_MESSAGES.get(exc.status_code, f"HTTP 错误 {exc.status_code}")
        if exc.detail and exc.detail != base:
            base += f": {exc.detail}"
        return JSONResponse(status_code=exc.status_code, content={"code": exc.status_code, "msg": base})

    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        detail = exc.detail if isinstance(exc.detail, dict) else {"code": 1, "msg": str(exc.detail)}
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": detail.get("code") or 1, "msg": detail.get("msg") or ""},
        )

    @app.exception_handler(ValueError)
    async def value_exception_handler(request: Request, exc: ValueError):
        return JSONResponse(status_code=400, content={"code": 1, "msg": str(exc)})

    @app.exception_handler(Exception)
    async def universal_exception_handler(request: Request, exc: Exception):
        logger.error(f"未处理的异常: {type(exc).__name__}: {exc}", exc_info=True)
        return JSONResponse(status_code=500, content={"code": 500, "msg": "服务器内部错误"})
