import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from urllib.parse import quote_plus
from .models import *  # 导入所有模型

def init_mysql(
    db_user: str = "root",
    db_password: str = "123456",
    db_host: str = "localhost",
    db_port: int = 3306,
    db_name: str = "queue_platform",
    create_tables: bool = True
):
    """
    初始化MySQL数据库连接
    :param create_tables: 是否自动创建不存在的表
    """
    # 强制Python运行时区
    os.environ['TZ'] = 'Asia/Shanghai'

    db_password = quote_plus(db_password) 
    
    # 创建连接引擎
    engine = create_engine(
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}",
        poolclass=QueuePool,
        pool_size=8,           # 增加连接池大小
        max_overflow=15,       # 增加溢出连接数
        pool_timeout=30,       # 连接池获取连接超时时间
        pool_recycle=1800,     # 减少连接回收时间到30分钟
        pool_pre_ping=True,    # 启用连接预检查
        echo=False,            # 设为True可查看SQL日志
        connect_args={
            'charset': 'utf8mb4',
            'connect_timeout': 10,      # 连接超时时间(秒)
            'read_timeout': 30,         # 读取超时时间
            'write_timeout': 30,        # 写入超时时间
            'autocommit': True,         # 启用自动提交
            'sql_mode': 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO',
        }
    )
    
    # 检查数据库是否存在，不存在则创建(需要用户有CREATE DATABASE权限)
    is_new_db = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))  # 测试连接
        print(f"成功连接到数据库: {db_name}")
    except Exception as e:
        if "Unknown database" in str(e):
            # 创建数据库
            temp_engine = create_engine(
                f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/",
                isolation_level="AUTOCOMMIT"
            )
            with temp_engine.connect() as conn:
                conn.execute(text(f"CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
            temp_engine.dispose()
            print(f"已创建新数据库: {db_name}")
            is_new_db = True
        else:
            raise
    
    # 始终检查并创建缺失的表（支持增量更新）
    if create_tables:
        try:
            Base.metadata.create_all(bind=engine)
            print("表结构已检查/创建")
            
            # 自动迁移新增字段
            auto_migrate_columns(engine)
        except Exception as e:
            print("建表时出错:", e)
        
        # 只在新数据库时初始化样例数据
        if is_new_db:
            init_sample_data(engine)
    
    return engine

def auto_migrate_columns(engine):
    """自动检测并添加/修改模型中的字段"""
    from sqlalchemy import inspect, Integer, String, Text, Boolean, DateTime
    from sqlalchemy.dialects import mysql
    from .models import FlexibleJSONType
    
    inspector = inspect(engine)
    
    # 类型映射：SQLAlchemy类型 -> MySQL类型
    def get_mysql_type(column):
        col_type = column.type
        
        # 对于 TypeDecorator（如 FlexibleJSONType），直接获取 impl
        if hasattr(col_type, 'impl'):
            actual_type = col_type.impl
        else:
            actual_type = col_type
        
        # 统一检查：无论是类还是实例
        # 先检查是否是类
        if isinstance(actual_type, type):
            if issubclass(actual_type, Text):
                return "TEXT"
            elif issubclass(actual_type, Integer):
                return "INT"
            elif issubclass(actual_type, String):
                return "VARCHAR(255)"
            elif issubclass(actual_type, DateTime):
                return "DATETIME"
            elif issubclass(actual_type, Boolean):
                return "TINYINT(1)"
        
        # 检查实例类型
        if isinstance(actual_type, Text):
            return "TEXT"
        elif isinstance(actual_type, Integer):
            return "INT"
        elif isinstance(actual_type, Boolean):
            return "TINYINT(1)"
        elif isinstance(actual_type, String):
            length = getattr(actual_type, 'length', None) or 255
            return f"VARCHAR({length})"
        elif isinstance(actual_type, DateTime):
            return "DATETIME"
        
        # 默认类型
        return "VARCHAR(255)"
    
    try:
        for table_name, table in Base.metadata.tables.items():
            # 检查表是否存在
            if table_name not in inspector.get_table_names():
                continue  # 表不存在，会由 create_all() 创建
            
            # 获取现有列信息（包括类型）
            existing_columns_info = {col['name']: col for col in inspector.get_columns(table_name)}
            existing_columns = set(existing_columns_info.keys())
            
            # 检查每个模型列
            for column in table.columns:
                if column.name not in existing_columns:
                    # 构建 ALTER TABLE 语句
                    col_type = get_mysql_type(column)
                    nullable = "NULL" if column.nullable else "NOT NULL"
                    default = ""
                    
                    # 处理默认值
                    if column.default is not None:
                        if hasattr(column.default, 'arg'):
                            if callable(column.default.arg):
                                # 对于函数默认值（如 datetime.now），不设置 DEFAULT
                                default = ""
                            else:
                                default = f" DEFAULT '{column.default.arg}'"
                        else:
                            default = f" DEFAULT '{column.default}'"
                    
                    # 处理注释
                    comment = ""
                    if column.comment:
                        comment = f" COMMENT '{column.comment}'"
                    
                    alter_sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{column.name}` {col_type} {nullable}{default}{comment}"
                    
                    try:
                        with engine.connect() as conn:
                            conn.execute(text(alter_sql))
                            conn.commit()
                        print(f"✓ 已添加字段: {table_name}.{column.name}")
                        
                        # 如果是 created_by 字段，将现有记录分配给管理员用户（ID=1）
                        if column.name == "created_by":
                            try:
                                update_sql = f"UPDATE `{table_name}` SET `created_by` = 1 WHERE `created_by` IS NULL"
                                with engine.connect() as conn:
                                    result = conn.execute(text(update_sql))
                                    conn.commit()
                                    if result.rowcount > 0:
                                        print(f"  → 已将 {result.rowcount} 条现有记录分配给管理员用户")
                            except Exception as e:
                                print(f"  ⚠ 更新现有记录失败: {e}")
                    except Exception as e:
                        # 如果字段已存在（并发情况），忽略错误
                        if "Duplicate column name" not in str(e):
                            print(f"✗ 添加字段失败 {table_name}.{column.name}: {e}")
                
                else:
                    # 字段已存在，检查类型是否需要修改
                    # 特殊处理：notification_config 从 VARCHAR 改为 TEXT
                    if column.name == "notification_config" and table_name == "task_define":
                        existing_col = existing_columns_info[column.name]
                        existing_type = str(existing_col['type']).upper()
                        
                        # 如果是 VARCHAR 或 JSON 类型，改为 TEXT
                        if 'VARCHAR' in existing_type or 'JSON' in existing_type:
                            try:
                                # 调试：打印类型信息
                                print(f"  调试: column.type={column.type}, type class={type(column.type)}")
                                if hasattr(column.type, 'impl'):
                                    print(f"  调试: column.type.impl={column.type.impl}, is type?={isinstance(column.type.impl, type)}")
                                
                                col_type = get_mysql_type(column)
                                print(f"  调试: get_mysql_type 返回 -> {col_type}")
                                
                                nullable = "NULL" if column.nullable else "NOT NULL"
                                comment = f" COMMENT '{column.comment}'" if column.comment else ""
                                
                                alter_sql = f"ALTER TABLE `{table_name}` MODIFY COLUMN `{column.name}` {col_type} {nullable}{comment}"
                                
                                with engine.connect() as conn:
                                    conn.execute(text(alter_sql))
                                    conn.commit()
                                print(f"✓ 已修改字段类型: {table_name}.{column.name} -> {col_type}")
                            except Exception as e:
                                print(f"✗ 修改字段类型失败 {table_name}.{column.name}: {e}")
        
        print("字段迁移检查完成")
    except Exception as e:
        print(f"自动迁移过程出错: {e}")

def init_sample_data(engine):
    """初始化样例数据（可选）"""
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # 检查是否已存在数据
        if not db.query(User).filter(User.username == "main").first():
            db.add(User(
                username="main",
                hashed_password="E10ADC3949BA59ABBE56E057F20F883E",  # 123456的MD5
                fixed=True
            ))
            db.commit()
            print("初始化样例数据完成")
    except Exception as e:
        db.rollback()
        print("初始化数据失败:", e)
    finally:
        db.close()
