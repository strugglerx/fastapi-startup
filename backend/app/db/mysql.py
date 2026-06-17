import os
import re
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from urllib.parse import quote_plus
from .models import *


def init_mysql(
    db_user: str = "root",
    db_password: str = "123456",
    db_host: str = "localhost",
    db_port: int = 3306,
    db_name: str = "queue_platform",
    create_tables: bool = True
):
    os.environ['TZ'] = 'Asia/Shanghai'

    db_password = quote_plus(db_password)

    engine = create_engine(
        f"mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}",
        poolclass=QueuePool,
        pool_size=8,
        max_overflow=15,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        echo=False,
        connect_args={
            'charset': 'utf8mb4',
            'connect_timeout': 10,
            'read_timeout': 30,
            'write_timeout': 30,
            'autocommit': True,
            'sql_mode': 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO',
        }
    )

    is_new_db = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"成功连接到数据库: {db_name}")
    except Exception as e:
        if "Unknown database" in str(e):
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

    if create_tables:
        try:
            Base.metadata.create_all(bind=engine)
            print("表结构已检查/创建")
            auto_migrate_columns(engine)
        except Exception as e:
            print("建表时出错:", e)

        if is_new_db:
            init_sample_data(engine)

    return engine


def auto_migrate_columns(engine):
    """自动检测并添加/修改模型中的字段（MySQL 版本）"""
    from sqlalchemy import inspect, Integer, String, Text, Boolean, DateTime
    from sqlalchemy.types import TypeDecorator

    inspector = inspect(engine)

    def get_mysql_type(column):
        col_type = column.type
        # 优先通过方言编译获取真实类型（可识别 MEDIUMTEXT/LONGTEXT 等 TypeDecorator）
        try:
            if isinstance(col_type, TypeDecorator):
                dialect_type = col_type.load_dialect_impl(engine.dialect)
            else:
                dialect_type = col_type
            compiled = str(dialect_type.compile(dialect=engine.dialect)).upper()
            if compiled:
                return compiled
        except Exception:
            pass

        actual_type = col_type.impl if hasattr(col_type, 'impl') else col_type

        if isinstance(actual_type, type):
            if issubclass(actual_type, Text):
                return "TEXT"
            if issubclass(actual_type, Integer):
                return "INT"
            if issubclass(actual_type, String):
                return "VARCHAR(255)"
            if issubclass(actual_type, DateTime):
                return "DATETIME"
            if issubclass(actual_type, Boolean):
                return "TINYINT(1)"

        if isinstance(actual_type, Text):
            return "TEXT"
        if isinstance(actual_type, Integer):
            return "INT"
        if isinstance(actual_type, Boolean):
            return "TINYINT(1)"
        if isinstance(actual_type, String):
            length = getattr(actual_type, 'length', None) or 255
            return f"VARCHAR({length})"
        if isinstance(actual_type, DateTime):
            return "DATETIME"

        return "VARCHAR(255)"

    def normalize_mysql_type(type_str: str) -> str:
        """归一化 MySQL 类型字符串，避免 CHARACTER SET / UNSIGNED 等差异触发假性 MODIFY。"""
        s = (type_str or "").upper().strip()
        s = re.sub(r"\s+CHARACTER SET\s+['\"]?[a-zA-Z0-9_-]+['\"]?", "", s)
        s = re.sub(r"\s+COLLATE\s+['\"]?[a-zA-Z0-9_-]+['\"]?", "", s)
        s = s.replace(" UNSIGNED", "").replace(" ZEROFILL", "").strip()

        if s.startswith("INTEGER") or s.startswith("INT("):
            return "INT"
        if s.startswith("BIGINT"):
            return "BIGINT"
        if s.startswith("SMALLINT"):
            return "SMALLINT"
        if s.startswith("TINYINT") or s.startswith("BOOL"):
            return "TINYINT"
        if s.startswith("LONGTEXT"):
            return "LONGTEXT"
        if s.startswith("MEDIUMTEXT"):
            return "MEDIUMTEXT"
        if s.startswith("TEXT"):
            return "TEXT"
        if s.startswith("TIMESTAMP"):
            return "TIMESTAMP"
        if s.startswith("DATETIME"):
            return "DATETIME"
        if s.startswith("DATE"):
            return "DATE"
        if s.startswith("DECIMAL") or s.startswith("NUMERIC"):
            return s
        if s.startswith("DOUBLE"):
            return "DOUBLE"
        if s.startswith("FLOAT"):
            return "FLOAT"
        if s.startswith("VARCHAR") or s.startswith("CHAR"):
            return s
        if s.startswith("JSON"):
            return "JSON"
        return s

    def should_modify_column_type(column, existing_type: str, desired_type: str) -> bool:
        if column.primary_key:
            return False
        return normalize_mysql_type(existing_type) != normalize_mysql_type(desired_type)

    try:
        for table_name, table in Base.metadata.tables.items():
            if table_name not in inspector.get_table_names():
                continue

            existing_columns_info = {col['name']: col for col in inspector.get_columns(table_name)}
            existing_columns = set(existing_columns_info.keys())

            for column in table.columns:
                if column.name not in existing_columns:
                    col_type = get_mysql_type(column)
                    nullable = "NULL" if column.nullable else "NOT NULL"
                    default = ""
                    if column.default is not None:
                        if hasattr(column.default, 'arg') and not callable(column.default.arg):
                            arg = column.default.arg
                            # 关键修复：Boolean 默认值要转 1/0；数字不带引号；其他才加引号
                            from sqlalchemy import Boolean, Integer
                            actual_type = type(column.type)
                            if isinstance(column.type, Boolean) or issubclass(actual_type, Boolean):
                                default = f" DEFAULT {1 if arg else 0}"
                            elif isinstance(arg, bool):
                                default = f" DEFAULT {1 if arg else 0}"
                            elif isinstance(arg, (int, float)):
                                default = f" DEFAULT {arg}"
                            else:
                                default = f" DEFAULT '{arg}'"
                    comment = f" COMMENT '{column.comment}'" if column.comment else ""

                    alter_sql = f"ALTER TABLE `{table_name}` ADD COLUMN `{column.name}` {col_type} {nullable}{default}{comment}"
                    try:
                        with engine.connect() as conn:
                            conn.execute(text(alter_sql))
                            conn.commit()
                        print(f"✓ 已添加字段: {table_name}.{column.name}")

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
                        if "Duplicate column name" not in str(e):
                            print(f"✗ 添加字段失败 {table_name}.{column.name}: {e}")

                else:
                    existing_col = existing_columns_info[column.name]
                    existing_type = str(existing_col['type']).upper()
                    desired_type = get_mysql_type(column).upper()
                    if should_modify_column_type(column, existing_type, desired_type):
                        try:
                            nullable = "NULL" if column.nullable else "NOT NULL"
                            comment = f" COMMENT '{column.comment}'" if column.comment else ""
                            alter_sql = f"ALTER TABLE `{table_name}` MODIFY COLUMN `{column.name}` {desired_type} {nullable}{comment}"
                            with engine.connect() as conn:
                                conn.execute(text(alter_sql))
                                conn.commit()
                            print(
                                f"✓ 已修改字段类型: {table_name}.{column.name} "
                                f"{normalize_mysql_type(existing_type)} -> {normalize_mysql_type(desired_type)}"
                            )
                        except Exception as e:
                            print(f"✗ 修改字段类型失败 {table_name}.{column.name}: {e}")

        print("字段迁移检查完成")
    except Exception as e:
        print(f"自动迁移过程出错: {e}")


def init_sample_data(engine):
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "main").first():
            from app.core.security import get_password_hash
            db.add(User(
                username="main",
                hashed_password=get_password_hash("123456"),
                fixed=True
            ))
            db.commit()
            print("初始化样例数据完成")
    except Exception as e:
        db.rollback()
        print("初始化数据失败:", e)
    finally:
        db.close()
