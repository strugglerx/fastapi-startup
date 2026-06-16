import os
from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from .logger import logger


class _Base(BaseSettings):
    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")


class DatabaseConfig(_Base):
    user: str = Field(default="root", validation_alias="DB_USER")
    password: str = Field(default="", validation_alias="DB_PASSWORD")
    host: str = Field(default="localhost", validation_alias="DB_HOST")
    port: int = Field(default=3306, validation_alias="DB_PORT")
    db_name: str = Field(default="queue_platform", validation_alias="DB_NAME")


class RedisConfig(_Base):
    host: str = Field(default="127.0.0.1", validation_alias="REDIS_HOST")
    port: int = Field(default=6379, validation_alias="REDIS_PORT")
    password: str = Field(default="", validation_alias="REDIS_PASSWORD")


class AppConfig(_Base):
    debug: bool = Field(default=True, validation_alias="APP_DEBUG")
    cors_origins: str = Field(default="*", validation_alias="APP_CORS_ORIGINS")
    enable_gzip: bool = Field(default=True, validation_alias="APP_ENABLE_GZIP")
    max_sync_concurrent: int = Field(default=10, validation_alias="MAX_SYNC_CONCURRENT")

    @property
    def cors_origins_list(self) -> List[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


class JwtConfig(_Base):
    secret_key: str = Field(
        default="default_secret_key_please_change_in_production",
        validation_alias="JWT_SECRET_KEY",
    )
    expire_minutes: int = Field(default=480, validation_alias="JWT_EXPIRE_MINUTES")


class Settings(_Base):
    app: AppConfig = Field(default_factory=AppConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    jwt: JwtConfig = Field(default_factory=JwtConfig)


def _find_env_file() -> Path:
    """优先 backend/.env，回退到项目根目录的 .env"""
    backend_dir = Path(__file__).resolve().parent.parent.parent
    p = backend_dir / ".env"
    if p.exists():
        return p
    root_p = backend_dir.parent / ".env"
    return root_p if root_p.exists() else p


_env_path = _find_env_file()
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)
    logger.info(f"✓ 已加载配置文件: {_env_path}")
else:
    logger.warning(f"⚠ 未找到 .env，使用默认配置 ({_env_path})")

# 配置加载兜底：任何环节失败都退回默认值，保证项目能启动
try:
    settings = Settings()
except Exception as e:
    logger.warning(f"配置加载异常，使用默认值: {e}")
    settings = Settings.model_construct(
        app=AppConfig.model_construct(),
        database=DatabaseConfig.model_construct(),
        redis=RedisConfig.model_construct(),
        jwt=JwtConfig.model_construct(),
    )

app_config = settings.app
database_config = settings.database
redis_config = settings.redis
jwt_config = settings.jwt

# 启动概览（敏感信息脱敏）
_app_env = os.getenv("APP_ENV", "development")
_use_sqlite = os.getenv("APP_USE_SQLITE", "").lower() == "true"
_jwt_default = jwt_config.secret_key == "default_secret_key_please_change_in_production"

logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
logger.info(f"  环境       : {_app_env}")
logger.info(f"  调试模式   : {'开启' if app_config.debug else '关闭'}")
logger.info(f"  数据库     : {'SQLite (app/data/sqlite.db)' if _use_sqlite else f'MySQL {database_config.user}@{database_config.host}:{database_config.port}/{database_config.db_name}'}")
logger.info(f"  Redis      : {redis_config.host}:{redis_config.port} ({'有密码' if redis_config.password else '无密码'})")
logger.info(f"  JWT        : {'⚠ 使用默认密钥（不安全，生产环境请修改）' if _jwt_default else '已配置'}, 过期 {jwt_config.expire_minutes} 分钟")
logger.info(f"  CORS       : {app_config.cors_origins_list}")
logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

# 生产环境用默认 JWT 密钥时发警告，但不阻断启动
if _app_env == "production" and _jwt_default:
    logger.warning("⚠ 生产环境正在使用默认 JWT 密钥，强烈建议配置 JWT_SECRET_KEY")
