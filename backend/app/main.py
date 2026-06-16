from .boot.application import create_app
from .api.public import router as public_router
from .api.v1 import router as v1_router

app = create_app()

app.include_router(v1_router)
app.include_router(public_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", reload=True)
