# 显式暴露子模块方法
from .middleware import setup_compression,setup_cors
from .static import serve_static
from .config import settings
from .logger import logger
from .exceptions import APIException
