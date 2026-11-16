'''
Description: 
Author: Moqi
Date: 2025-11-29 10:20:15
Email: str@li.cm
Github: https://github.com/strugglerx
LastEditors: Moqi
LastEditTime: 2025-12-01 21:35:56
'''
import os
from typing import Generator
from sqlalchemy import create_engine,event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool  # 连接池实现
from .models import *  # 导入所有模型
from .sqlite import init_sqlite, run_db_migration as _run_db_migration_sqlite
from .mysql import init_mysql, run_db_migration as _run_db_migration_mysql
from app.boot import settings

def init_engine():
    # 默认 MySQL；只有显式设置 APP_USE_SQLITE=true 才走 SQLite（本地轻量开发）
    if os.getenv("APP_USE_SQLITE", "").lower() == "true":
        _engine = init_sqlite()
    else:
        _engine = init_mysql(
            db_host=settings.database.host,
            db_user=settings.database.user,
            db_password=settings.database.password,
            db_port=settings.database.port,
            db_name=settings.database.db_name,
        )
    return _engine
        
engine = init_engine()
        
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def run_db_migration():
    """在后台线程中执行耗时的建表 + ALTER TABLE 字段迁移。
    由 lifespan 通过 asyncio.to_thread(run_db_migration) 调用，不阻塞主事件循环。"""
    if os.getenv("APP_USE_SQLITE", "").lower() == "true":
        _run_db_migration_sqlite(engine)
    else:
        _run_db_migration_mysql(engine)