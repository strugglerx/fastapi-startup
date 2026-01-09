from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse,StreamingResponse
import json
from .exceptions import APIException
from .config import app_config
from .logger import logger

def setup_cors(app: FastAPI):
    from fastapi.middleware.cors import CORSMiddleware
        
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_config.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def setup_custom_server(app:FastAPI):
    @app.middleware("http")
    async def server_header(request: Request, call_next):
        response = await call_next(request)
        response.headers["Server"]  = "struggler/1.0" 
        access_control_allow_origin = response.headers.get("access-control-allow-origin", "")
        if access_control_allow_origin == "*" and "origin" in request.headers:
            origin = request.headers.get("origin")
            response.headers["access-control-allow-origin"] = origin  # 覆盖为请求的 Origin
        return response
    
def setup_compression(app: FastAPI):
    """配置Gzip压缩"""
    from fastapi.middleware.gzip import GZipMiddleware
    app.add_middleware(GZipMiddleware)
    
def setup_stand_response(app: FastAPI):
    
    def is_wrapped_response(data: dict) -> bool:
        """检查是否已经是标准格式响应"""
        # logger.info(data)
        return all(key in data for key in ("code",))
    async def response_wrapper_middleware(request: Request, call_next):
        try:
            response = await call_next(request)

            # 跳过文档等特殊路径
            if request.url.path.startswith(("/docs", "/openapi.json", "/api/v1/mcp")):
                return response
                
            # 只处理JSON响应且状态码为200
            if "application/json" in response.headers.get("content-type", "") and response.status_code == 200:
                # 处理流式响应
                if isinstance(response, StreamingResponse):
                    async def wrapped_stream():
                        chunks = []
                        try:
                            async for chunk in response.body_iterator:
                                chunks.append(chunk)
                            
                            # 拼接所有chunk并解码
                            full_body = b''.join(chunks).decode()
                            try:
                                data = json.loads(full_body)
                                if not is_wrapped_response(data):  # 检查是否已包装
                                    data = {"code": 200, "data": data}
                                yield json.dumps(data,ensure_ascii=False).encode()
                            except json.JSONDecodeError:
                                yield full_body.encode()
                        except Exception as e:
                            logger.error(f"Stream processing error: {e}")
                            error_response = {"code": 1, "msg": "Stream processing failed"}
                            yield json.dumps(error_response, ensure_ascii=False).encode()
                        finally:
                            # 确保资源清理
                            if hasattr(response, 'body_iterator') and hasattr(response.body_iterator, 'close'):
                                try:
                                    await response.body_iterator.close()
                                except:
                                    pass
                                    
                    # 创建新的响应，不包含 content-length
                    return StreamingResponse(
                        status_code=response.status_code,
                        content=wrapped_stream(),
                        media_type="application/json"
                    )
                
                # 对于普通 Response，读取 body
                body = b""
                body_was_consumed = False
                
                if hasattr(response, 'body'):
                    body = response.body
                elif hasattr(response, 'body_iterator'):
                    chunks = []
                    async for chunk in response.body_iterator:
                        chunks.append(chunk)
                    body = b''.join(chunks)
                    body_was_consumed = True  # 标记 body_iterator 已被消费
                
                if body:
                    try:
                        data = json.loads(body)
                        if not is_wrapped_response(data):  # 关键检查
                            data = {
                                "code": 200,
                                "data": data
                            }
                        # 无论是否包装，都创建新的 JSONResponse 以确保 Content-Length 正确
                        return JSONResponse(
                            status_code=response.status_code,
                            content=data
                        )
                    except Exception as e:
                        logger.error(f"JSON parse error: {e}")
                        # 如果解析失败但 body_iterator 已被消费，需要重建响应
                        if body_was_consumed:
                            from starlette.responses import Response
                            return Response(
                                content=body,
                                status_code=response.status_code,
                                headers=dict(response.headers),
                                media_type=response.headers.get("content-type")
                            )
                
            return response
        except APIException as e:
            raise
            
        except Exception as e:
            return JSONResponse(
                status_code=200,
                content={"code": 1, "msg": str(e)}
            )
    app.middleware("http")(response_wrapper_middleware)
    
def setup_exception(app: FastAPI):
    from fastapi.exceptions import RequestValidationError, HTTPException as FastAPIHTTPException
    from starlette.exceptions import HTTPException as StarletteHTTPException
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """统一处理 FastAPI 参数验证错误 (422)"""
        errors = exc.errors()
        
        # 格式化第一个错误信息为易读的中文
        if errors:
            first_error = errors[0]
            loc = first_error.get("loc", [])
            msg_type = first_error.get("type", "")
            msg = first_error.get("msg", "")
            
            # 提取字段名（跳过 'body' 或 'query' 等前缀）
            field_name = loc[-1] if len(loc) > 1 else loc[0] if loc else "参数"
            
            # 根据错误类型生成友好的中文提示
            if msg_type == "value_error.missing":
                error_msg = f"缺少必填参数: {field_name}"
            elif msg_type.startswith("type_error"):
                error_msg = f"参数类型错误: {field_name} ({msg})"
            elif msg_type == "value_error.any_str.min_length":
                error_msg = f"参数长度不足: {field_name} ({msg})"
            elif msg_type == "value_error.any_str.max_length":
                error_msg = f"参数长度超限: {field_name} ({msg})"
            elif msg_type.startswith("value_error"):
                error_msg = f"参数值错误: {field_name} ({msg})"
            else:
                error_msg = f"参数验证失败: {field_name} - {msg}"
            
            # 如果有多个错误，添加提示
            if len(errors) > 1:
                error_msg += f" (共 {len(errors)} 个错误)"
        else:
            error_msg = "请求参数验证失败"
        
        return JSONResponse(
            status_code=200,  # 统一返回 200，通过 code 字段区分
            content={"code": 1, "msg": error_msg}
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """统一处理 HTTP 异常 (404, 405, 500 等)"""
        # 根据状态码提供友好的中文提示
        status_messages = {
            400: "请求格式错误",
            401: "未授权访问",
            403: "禁止访问",
            404: "接口不存在",
            405: "请求方法不允许",
            408: "请求超时",
            413: "请求体过大",
            429: "请求过于频繁",
            500: "服务器内部错误",
            502: "网关错误",
            503: "服务暂时不可用",
        }
        
        error_msg = status_messages.get(exc.status_code, f"HTTP 错误 {exc.status_code}")
        
        # 如果有详细信息，追加到错误消息
        if exc.detail and exc.detail != error_msg:
            error_msg += f": {exc.detail}"
        
        return JSONResponse(
            status_code=200,  # 统一返回 200，通过 code 字段区分
            content={"code": exc.status_code, "msg": error_msg}
        )
    
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        """统一处理自定义 API 异常"""
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.detail.get("code") or 1, "msg": exc.detail.get("msg") or ""}
        )
    
    @app.exception_handler(ValueError)
    async def value_exception_handler(request: Request, exc: ValueError):
        """统一处理 ValueError"""
        return JSONResponse(
            status_code=200,
            content={"code": 1, "msg": f"{str(exc)}"}
        )

    @app.exception_handler(Exception)
    async def universal_exception_handler(request: Request, exc: Exception):
        """捕获所有未处理的异常（兜底）"""
        from app.boot import logger
        logger.error(f"未处理的异常: {type(exc).__name__}: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=200,  # 统一返回 200
            content={"code": 500, "msg": f"服务器内部错误: {str(exc)}"}
        )
    