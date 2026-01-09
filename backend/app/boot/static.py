from fastapi import FastAPI
from pathlib import Path
from fastapi.staticfiles import StaticFiles
def serve_static(app: FastAPI):

    @app.on_event("startup")
    def startup():
        static_dir = Path.cwd() / 'app/public'
        app.mount("/", StaticFiles(directory=str(static_dir)), name="static")
