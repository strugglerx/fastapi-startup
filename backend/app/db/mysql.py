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
):
    """仅创建 engine + 验证连接（快速），不做耗时的 DDL 迁移。
    迁移请调用 run_db_migration(engine)。"""
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

    # 将 is_new_db 标记挂在 engine 上，供后续迁移阶段判断
    engine._is_new_db = is_new_db
    return engine


def run_db_migration(engine):
    """耗时的建表 + ALTER TABLE 字段迁移，设计为在后台线程中运行。"""
    is_new_db = getattr(engine, '_is_new_db', False)
    try:
        Base.metadata.create_all(bind=engine)
        print("表结构已检查/创建")
        auto_migrate_columns(engine)
    except Exception as e:
        print("建表时出错:", e)

    if is_new_db:
        init_sample_data(engine)


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

        # ─────── UniqueConstraint 同步（__table_args__ 里新增的复合 UNIQUE） ───────
        # auto_migrate_columns 默认只处理 ADD/MODIFY 列，跟不上 __table_args__ 里新增的
        # UniqueConstraint。这里补一遍：把模型声明的 UniqueConstraint 跟 DB 实际索引/约束
        # 比对，缺则 ALTER ADD CONSTRAINT。存量数据有重复时 ALTER 会失败，告警提示运维清理。
        from sqlalchemy import UniqueConstraint
        for table_name, table in Base.metadata.tables.items():
            if table_name not in inspector.get_table_names():
                continue
            try:
                existing_uniques = {
                    uc.get('name') for uc in inspector.get_unique_constraints(table_name)
                    if uc.get('name')
                }
                # 兼容：MySQL 把 UNIQUE 约束以「unique index」呈现，name 一致
                existing_uniques |= {
                    idx.get('name') for idx in inspector.get_indexes(table_name)
                    if idx.get('unique') and idx.get('name')
                }
            except Exception as e:
                print(f"⚠ 读取 {table_name} 约束失败：{e}")
                continue

            for constraint in table.constraints:
                if not isinstance(constraint, UniqueConstraint):
                    continue
                if not constraint.name or constraint.name in existing_uniques:
                    continue
                col_names = [c.name for c in constraint.columns]
                if not col_names:
                    continue
                cols_sql = ", ".join(f"`{c}`" for c in col_names)
                alter_sql = (
                    f"ALTER TABLE `{table_name}` ADD CONSTRAINT `{constraint.name}` "
                    f"UNIQUE ({cols_sql})"
                )
                try:
                    with engine.connect() as conn:
                        conn.execute(text(alter_sql))
                        conn.commit()
                    print(f"✓ 已添加唯一约束: {table_name}.{constraint.name} ({cols_sql})")
                except Exception as e:
                    es = str(e)
                    if "Duplicate entry" in es or "errno: 121" in es or "1062" in es:
                        print(
                            f"⚠ 添加唯一约束失败 {table_name}.{constraint.name}：表里存在违反约束的重复数据，"
                            f"需先清理。\n  cols={cols_sql}\n  详情: {e}"
                        )
                    elif "Duplicate key name" in es or "already exists" in es:
                        # 约束名已存在但 inspector 没读到（罕见，可能别名映射）—— 跳过
                        pass
                    else:
                        print(f"✗ 添加唯一约束失败 {table_name}.{constraint.name}: {e}")

        # zhihui Agent 上架从「一个 Agent 只能出现一次」改为「同一 Agent 可出现在多个分类」。
        # 旧库由 Column(unique=True) 生成过 role_id 唯一索引；这里定向删除，后面的普通
        # Index 同步会按新模型补回非唯一 role_id 索引。
        if "zhihui_agent_visibility" in inspector.get_table_names():
            try:
                for idx in inspector.get_indexes("zhihui_agent_visibility"):
                    if not idx.get("unique"):
                        continue
                    if list(idx.get("column_names") or []) != ["role_id"]:
                        continue
                    idx_name = idx.get("name")
                    if not idx_name:
                        continue
                    with engine.connect() as conn:
                        conn.execute(text(f"ALTER TABLE `zhihui_agent_visibility` DROP INDEX `{idx_name}`"))
                        try:
                            conn.execute(text(
                                "CREATE INDEX `ix_zhihui_agent_visibility_role_id` "
                                "ON `zhihui_agent_visibility` (`role_id`)"
                            ))
                        except Exception as index_error:
                            if "Duplicate key name" not in str(index_error):
                                raise
                        conn.commit()
                    print(f"✓ 已移除唯一索引并补普通索引: zhihui_agent_visibility.{idx_name}")
            except Exception as e:
                print(f"✗ 移除 zhihui_agent_visibility.role_id 唯一索引失败: {e}")

        # ─────── Index 同步（__table_args__ 里新增的普通 Index，以及 Column(index=True)） ───────
        # create_all 只对「新建」的表生成索引；存量表 __table_args__ 新增 sa.Index 或
        # Column(index=True) 都不会被 create_all 补上。这里把模型声明的所有非唯一索引
        # 跟 DB 实际索引比对，缺则 CREATE INDEX。
        # 与 UniqueConstraint 同步是一套机制，但 Index 走 inspector.get_indexes 单独处理。
        from sqlalchemy import Index
        for table_name, table in Base.metadata.tables.items():
            if table_name not in inspector.get_table_names():
                continue
            try:
                existing_indexes = {
                    idx.get('name') for idx in inspector.get_indexes(table_name)
                    if idx.get('name')
                }
            except Exception as e:
                print(f"⚠ 读取 {table_name} 索引失败：{e}")
                continue

            for index in table.indexes:
                if index.unique:
                    # 唯一索引由 UniqueConstraint 分支处理
                    continue
                if not index.name or index.name in existing_indexes:
                    continue
                col_names = [c.name for c in index.columns]
                if not col_names:
                    continue
                cols_sql = ", ".join(f"`{c}`" for c in col_names)
                create_sql = f"CREATE INDEX `{index.name}` ON `{table_name}` ({cols_sql})"
                try:
                    with engine.connect() as conn:
                        conn.execute(text(create_sql))
                        conn.commit()
                    print(f"✓ 已添加索引: {table_name}.{index.name} ({cols_sql})")
                except Exception as e:
                    es = str(e)
                    if "Duplicate key name" in es or "already exists" in es:
                        # 索引名已存在但 inspector 没读到 —— 跳过
                        pass
                    else:
                        print(f"✗ 添加索引失败 {table_name}.{index.name}: {e}")

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
