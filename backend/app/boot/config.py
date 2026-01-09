'''
Description: 
Author: Moqi
Date: 2025-07-02 17:25:49
Email: str@li.cm
Github: https://github.com/strugglerx
LastEditors: Moqi
LastEditTime: 2025-12-31 21:24:00
'''
import os
from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from .logger import logger


class DatabaseConfig(BaseSettings):
    """数据库配置
    
    注意：环境变量通过 load_dotenv() 统一加载，不在此处配置 env_file
    """
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore"
    )
    
    user: str = Field(default="root", validation_alias="DB_USER")
    password: str = Field(default="", validation_alias="DB_PASSWORD")
    host: str = Field(default="localhost", validation_alias="DB_HOST")
    port: int = Field(default=3306, validation_alias="DB_PORT")
    db_name: str = Field(default="queue_platform", validation_alias="DB_NAME")


class RedisConfig(BaseSettings):
    """Redis 配置
    
    注意：环境变量通过 load_dotenv() 统一加载，不在此处配置 env_file
    """
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore"
    )
    
    host: str = Field(default="127.0.0.1", validation_alias="REDIS_HOST")
    port: int = Field(default=6379, validation_alias="REDIS_PORT")
    password: str = Field(default="", validation_alias="REDIS_PASSWORD")


class AppConfig(BaseSettings):
    """应用配置
    
    注意：环境变量通过 load_dotenv() 统一加载，不在此处配置 env_file
    """
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore"
    )
    
    debug: bool = Field(default=True, validation_alias="APP_DEBUG")
    cors_origins: str = Field(default="*", validation_alias="APP_CORS_ORIGINS")
    enable_gzip: bool = Field(default=True, validation_alias="APP_ENABLE_GZIP")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """将逗号分隔的字符串转换为列表"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


class JwtConfig(BaseSettings):
    """JWT 配置

    注意：环境变量通过 load_dotenv() 统一加载，不在此处配置 env_file
    """
    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore"
    )

    secret_key: str = Field(
        default="default_secret_key_please_change_in_production",
        validation_alias="JWT_SECRET_KEY"
    )
    expire_minutes: int = Field(default=480, validation_alias="JWT_EXPIRE_MINUTES")


class Settings(BaseSettings):
    app: AppConfig
    database: DatabaseConfig
    redis: RedisConfig
    jwt: JwtConfig


# 查找 .env 文件路径
def find_env_file() -> Path:
    """查找 .env 文件，优先使用 backend 目录下的 .env"""
    backend_dir = Path(__file__).resolve().parent.parent.parent
    env_path = backend_dir / ".env"
    
    if env_path.exists():
        return env_path
    
    # 如果 backend/.env 不存在，尝试查找项目根目录
    project_root = backend_dir.parent
    root_env_path = project_root / ".env"
    
    if root_env_path.exists():
        return root_env_path
    
    # 如果都不存在，返回默认路径（会使用默认值）
    return env_path


# 设置环境变量文件路径
env_file_path = find_env_file()
if env_file_path.exists():
    # 使用 python-dotenv 加载环境变量
    from dotenv import load_dotenv
    load_dotenv(env_file_path)
    msg = f"✓ 成功加载配置文件: {env_file_path}"
    logger.info(msg)
    print(msg)
else:
    msg = f"⚠️  未找到 .env 配置文件 (查找路径: {env_file_path})，将使用默认配置"
    logger.warning(msg)
    print(msg)

# 加载各个配置模块
print("=" * 60)
print("开始加载应用配置...")
logger.info("开始加载应用配置...")

try:
    app_config = AppConfig()
    msg = "✓ [应用配置 (app)] 配置已加载"
    logger.info(msg)
    print(msg)
except Exception as e:
    msg = f"⚠️  [应用配置 (app)] 加载失败: {e}，使用默认值"
    logger.warning(msg)
    print(msg)
    app_config = AppConfig()

try:
    database_config = DatabaseConfig()
    msg = "✓ [数据库配置 (database)] 配置已加载"
    logger.info(msg)
    print(msg)
except Exception as e:
    msg = f"⚠️  [数据库配置 (database)] 加载失败: {e}，使用默认值"
    logger.warning(msg)
    print(msg)
    database_config = DatabaseConfig()

try:
    redis_config = RedisConfig()
    msg = "✓ [Redis配置 (redis)] 配置已加载"
    logger.info(msg)
    print(msg)
except Exception as e:
    msg = f"⚠️  [Redis配置 (redis)] 加载失败: {e}，使用默认值"
    logger.warning(msg)
    print(msg)
    redis_config = RedisConfig()

try:
    jwt_config = JwtConfig()
    msg = "✓ [JWT配置 (jwt)] 配置已加载"
    logger.info(msg)
    print(msg)
except Exception as e:
    msg = f"⚠️  [JWT配置 (jwt)] 加载失败: {e}，使用默认值"
    logger.warning(msg)
    print(msg)
    jwt_config = JwtConfig()

settings = Settings(
    app=app_config,
    database=database_config,
    redis=redis_config,
    jwt=jwt_config
)

# 详细输出配置信息（敏感信息脱敏）
print("=" * 60)
print("📋 配置详情:")

# 根据环境显示数据库配置
app_env = os.getenv("APP_ENV", "development")
if app_env == "production":
    print(f"  🗄️  数据库: MySQL - {database_config.user}@{database_config.host}:{database_config.port}/{database_config.db_name}")
else:
    print(f"  🗄️  数据库: SQLite - app/data/sqlite.db")

print(f"  🔴 Redis: {redis_config.host}:{redis_config.port} (密码: {'✓已设置' if redis_config.password else '⚠️未设置'})")
print(f"  🔑 JWT: secret_key={'✓已配置' if jwt_config.secret_key != 'default_secret_key_please_change_in_production' else '⚠️使用默认值(不安全!)'}, 过期时间={jwt_config.expire_minutes}分钟")
print(f"  🐛 调试模式: {'开启' if app_config.debug else '关闭'}")
print(f"  🌐 CORS: {app_config.cors_origins_list}")
print(f"  🌍 环境: {app_env}")
print("=" * 60)
print("✅ 配置加载完成\n")

logger.info("配置加载完成")