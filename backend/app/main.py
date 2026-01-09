from .boot.application import create_app
from .api.public import router as public_router
from .api.v1 import router as v1_router
from .library.debug import generate_route_md

app = create_app()


app.include_router(v1_router)

# 公开接口
app.include_router(public_router)


# 注册路由
# app.include_router(v1_router, prefix="/api/v1")

generate_route_md(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", reload=True)