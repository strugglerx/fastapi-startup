"""
Base Scaffold Database Models
只保留核心表：AccessKey 和 User
"""
import pytz
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

# 定义东八区时区对象
EAST_8_TIMEZONE = pytz.timezone("Asia/Shanghai")

Base = declarative_base()

class AccessKey(Base):
    """访问密钥表"""
    __tablename__ = "access_keys"

    id = Column(Integer, primary_key=True)
    secret_key = Column(String(100), unique=True, nullable=False, comment="密钥内容")
    description = Column(String(255), comment="密钥描述")
    max_qps = Column(Integer, default=10, comment="最大每秒请求数")
    created_by = Column(Integer, nullable=True, index=True, comment="创建用户ID")
    created_at = Column(sa.DateTime(timezone=True), default=lambda: datetime.now(EAST_8_TIMEZONE).replace(microsecond=0), comment="创建时间")
    updated_at = Column(sa.DateTime(timezone=True), onupdate=lambda: datetime.now(EAST_8_TIMEZONE).replace(microsecond=0), comment="更新时间")
    deleted_at = Column(sa.DateTime(timezone=True), nullable=True, comment="删除时间")

class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, comment="用户名")
    hashed_password = Column(String(60), nullable=False, comment="加密后的密码")
    last_login = Column(sa.DateTime(timezone=True), comment="最后登录时间")
    fixed = Column(Boolean, default=False, comment="是否为固定管理员用户")
    created_at = Column(sa.DateTime(timezone=True), default=lambda: datetime.now(EAST_8_TIMEZONE).replace(microsecond=0), comment="创建时间")
    updated_at = Column(sa.DateTime(timezone=True), onupdate=lambda: datetime.now(EAST_8_TIMEZONE).replace(microsecond=0), comment="更新时间")
    deleted_at = Column(sa.DateTime(timezone=True), nullable=True, comment="删除时间")
