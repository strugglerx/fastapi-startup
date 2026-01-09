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
from sqlalchemy import create_engine,event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool  # 连接池实现
from .models import *  # 导入所有模型
from .sqlite import init_sqlite
from .mysql import init_mysql
from app.boot import settings

def init_engine():  
    if os.getenv("APP_ENV") == "production":
        _engine = init_mysql(
            db_host=settings.database.host,
            db_user=settings.database.user,
            db_password=settings.database.password,
            db_port=settings.database.port,
            db_name=settings.database.db_name,
        )
    else:
        _engine = init_sqlite()
    return _engine 
        
engine = init_engine()
        
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)