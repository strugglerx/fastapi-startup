from fastapi.openapi.utils import get_openapi


def custom_openapi(app):
    """覆盖 app.openapi 以注入 x-tagGroups 分组。

    用 lazy override（首次访问 /openapi.json 时计算并缓存到
    app.openapi_schema）替代 on_event("startup")，保证拿到
    所有已注册路由（include_router 之后才被读取）。
    """

    def _openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            routes=app.routes,
        )

        openapi_schema["x-tagGroups"] = [
            {
                "name": "API/V1",
                "tags": ["示例接口"],
            },
            {
                "name": "通用",
                "tags": ["公开接口"],
            },
        ]

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = _openapi
