"""项目路径常量 —— 全部基于源码位置定位，不依赖启动 cwd。"""
from pathlib import Path

# app/paths.py → app/ → backend/
BACKEND_DIR: Path = Path(__file__).resolve().parent.parent
APP_DIR: Path = BACKEND_DIR / "app"
DATA_DIR: Path = APP_DIR / "data"
STATIC_DIR: Path = APP_DIR / "public"
AUTO_DOCS_DIR: Path = BACKEND_DIR / "auto_docs"
ROUTES_MD_PATH: Path = BACKEND_DIR / "routes.md"
LOGS_DIR: Path = BACKEND_DIR / "logs"
