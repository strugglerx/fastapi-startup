'''
Description: 
Author: Moqi
Date: 2025-07-07 17:00:16
Email: str@li.cm
Github: https://github.com/strugglerx
LastEditors: Moqi
LastEditTime: 2025-07-07 17:01:03
'''
import os
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool  # 连接池实现
from .models import *  # 导入所有模型

def init_sqlite(db_path: str = "app/data/sqlite.db"):
    # 强制Python运行时区（即使不修改模型）
    os.environ['TZ'] = 'Asia/Shanghai'
    """自动初始化SQLite数据库"""
    # 确保目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # 连接数据库（自动创建文件）
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=QueuePool,  # 关键配置
        pool_size=5,          # 保持的连接数
        max_overflow=10,      # 超出pool_size时允许新增的连接数
        pool_timeout=30,      # 获取连接超时时间(秒)
        pool_recycle=3600,     # 连接自动回收时间(秒)
    )
    
    # 检查是否为新数据库
    is_new_db = not os.path.exists(db_path)
    
    # 始终检查并创建缺失的表（支持增量更新）
    try:
        Base.metadata.create_all(bind=engine)
        if is_new_db:
            print(f"创建新数据库: {db_path}")
        else:
            print(f"数据库已存在，检查并创建缺失的表: {db_path}")
        
        # 自动迁移新增字段
        auto_migrate_columns(engine)
    except Exception as e:
        print(f"创建表时出错: {e}")
    
    # 只在新数据库时初始化样例数据
    if is_new_db:
        init_sample_data(engine)
    
    return engine

def auto_migrate_columns(engine):
    """自动检测并添加模型中新增的字段（SQLite版本）"""
    from sqlalchemy import inspect, Integer, String, Text, Boolean, DateTime
    
    inspector = inspect(engine)
    
    # 类型映射：SQLAlchemy类型 -> SQLite类型
    def get_sqlite_type(column):
        col_type = column.type
        
        if isinstance(col_type, Integer):
            return "INTEGER"
        elif isinstance(col_type, Boolean):
            return "INTEGER"  # SQLite uses INTEGER for BOOLEAN
        elif isinstance(col_type, String):
            return "TEXT"
        elif isinstance(col_type, Text):
            return "TEXT"
        elif isinstance(col_type, DateTime):
            return "DATETIME"
        else:
            return "TEXT"  # 默认类型
    
    try:
        for table_name, table in Base.metadata.tables.items():
            # 检查表是否存在
            if table_name not in inspector.get_table_names():
                continue  # 表不存在，会由 create_all() 创建
            
            # 获取现有列
            existing_columns = {col['name'] for col in inspector.get_columns(table_name)}
            
            # 检查每个模型列
            for column in table.columns:
                if column.name not in existing_columns:
                    # 构建 ALTER TABLE 语句
                    col_type = get_sqlite_type(column)
                    
                    # SQLite 限制：添加的列必须满足以下条件之一：
                    # 1. 允许 NULL
                    # 2. 有默认值
                    # 因此，如果列定义为 NOT NULL 但没有默认值，我们将其改为允许 NULL
                    nullable_clause = ""
                    default_clause = ""
                    
                    if column.default is not None:
                        if hasattr(column.default, 'arg'):
                            if not callable(column.default.arg):
                                default_clause = f" DEFAULT '{column.default.arg}'"
                        else:
                            default_clause = f" DEFAULT '{column.default}'"
                    
                    # 如果既不允许 NULL 也没有默认值，强制允许 NULL（SQLite 限制）
                    if not column.nullable and not default_clause:
                        print(f"⚠ 警告: {table_name}.{column.name} 定义为 NOT NULL 但无默认值，SQLite 将其改为允许 NULL")
                    
                    alter_sql = f'ALTER TABLE "{table_name}" ADD COLUMN "{column.name}" {col_type}{default_clause}'
                    
                    try:
                        with engine.connect() as conn:
                            conn.execute(text(alter_sql))
                            conn.commit()
                        print(f"✓ 已添加字段: {table_name}.{column.name}")
                        
                        # 如果是 created_by 字段，将现有记录分配给管理员用户（ID=1）
                        if column.name == "created_by":
                            try:
                                update_sql = f'UPDATE "{table_name}" SET "created_by" = 1 WHERE "created_by" IS NULL'
                                with engine.connect() as conn:
                                    result = conn.execute(text(update_sql))
                                    conn.commit()
                                    if result.rowcount > 0:
                                        print(f"  → 已将 {result.rowcount} 条现有记录分配给管理员用户")
                            except Exception as e:
                                print(f"  ⚠ 更新现有记录失败: {e}")
                    except Exception as e:
                        # 如果字段已存在（并发情况），忽略错误
                        if "duplicate column name" not in str(e).lower():
                            print(f"✗ 添加字段失败 {table_name}.{column.name}: {e}")
        
        print("字段迁移检查完成")
    except Exception as e:
        print(f"自动迁移过程出错: {e}")

def init_sample_data(engine):
    """初始化样例数据（可选）"""
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # 在这里添加初始化数据
        # 例如： db.add(User(name="admin"))
        # md5 32位大些 main 123456
        db.add(User(username="main",hashed_password="E10ADC3949BA59ABBE56E057F20F883E",fixed=True))
        db.commit()
    except Exception as e:
        db.rollback()
        print("初始化数据失败:", e)
    finally:
        db.close()
