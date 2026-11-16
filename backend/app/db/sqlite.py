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
    """仅创建 engine + 验证连接（快速），不做耗时的 DDL 迁移。
    迁移请调用 run_db_migration(engine)。"""
    # 强制Python运行时区（即使不修改模型）
    os.environ['TZ'] = 'Asia/Shanghai'
    # 确保目录存在
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=3600,
    )

    # 标记是否为新库（文件不存在），供后续迁移阶段判断
    engine._is_new_db = not os.path.exists(db_path)
    return engine


def run_db_migration(engine):
    """耗时的建表 + ALTER TABLE 字段迁移，设计为在后台线程中运行。"""
    is_new_db = getattr(engine, '_is_new_db', False)
    try:
        Base.metadata.create_all(bind=engine)
        if is_new_db:
            print(f"创建新数据库完成")
        else:
            print(f"数据库已存在，检查并创建缺失的表")
        auto_migrate_columns(engine)
    except Exception as e:
        print(f"创建表时出错: {e}")

    if is_new_db:
        init_sample_data(engine)

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
        def relax_zhihui_visibility_role_unique():
            table_name = "zhihui_agent_visibility"
            if table_name not in inspector.get_table_names():
                return
            with engine.connect() as conn:
                indexes = conn.execute(text(f'PRAGMA index_list("{table_name}")')).fetchall()
                has_unique_role = False
                for idx in indexes:
                    idx_name = idx[1]
                    is_unique = bool(idx[2])
                    if not is_unique:
                        continue
                    cols = conn.execute(text(f'PRAGMA index_info("{idx_name}")')).fetchall()
                    if [c[2] for c in cols] == ["role_id"]:
                        has_unique_role = True
                        break
                if not has_unique_role:
                    return

                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS zhihui_agent_visibility_new (
                        id BIGINT NOT NULL PRIMARY KEY,
                        role_id BIGINT NOT NULL,
                        category_id BIGINT,
                        category VARCHAR(64) DEFAULT '' NOT NULL,
                        allowed_roles TEXT,
                        sort INTEGER DEFAULT 0 NOT NULL,
                        show_thinking BOOLEAN DEFAULT 0 NOT NULL,
                        is_enabled BOOLEAN DEFAULT 1 NOT NULL,
                        created_at DATETIME,
                        updated_at DATETIME
                    )
                """))
                conn.execute(text("""
                    INSERT INTO zhihui_agent_visibility_new (
                        id, role_id, category_id, category, allowed_roles, sort,
                        show_thinking, is_enabled, created_at, updated_at
                    )
                    SELECT
                        id, role_id, category_id, category, allowed_roles, sort,
                        show_thinking, is_enabled, created_at, updated_at
                    FROM zhihui_agent_visibility
                """))
                conn.execute(text('DROP TABLE zhihui_agent_visibility'))
                conn.execute(text(
                    'ALTER TABLE zhihui_agent_visibility_new RENAME TO zhihui_agent_visibility'
                ))
                conn.execute(text(
                    'CREATE INDEX IF NOT EXISTS ix_zhihui_agent_visibility_role_id '
                    'ON zhihui_agent_visibility (role_id)'
                ))
                conn.execute(text(
                    'CREATE INDEX IF NOT EXISTS ix_zhihui_agent_visibility_category_id '
                    'ON zhihui_agent_visibility (category_id)'
                ))
                conn.commit()
                print("✓ 已移除唯一索引: zhihui_agent_visibility.role_id")

        relax_zhihui_visibility_role_unique()

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

        # ─────── UniqueConstraint 同步（SQLite 版本） ───────
        # SQLite 不支持 ALTER TABLE ADD CONSTRAINT，但可以用 CREATE UNIQUE INDEX
        # 达到等价语义（INSERT 违反时同样抛 IntegrityError）。
        # 跟 MySQL 端逻辑对齐：把 __table_args__ 里新增的 UniqueConstraint 同步到 DB，
        # 让本地 SQLite 测试和线上 MySQL 行为一致（避免「本地测过、生产挂」）。
        from sqlalchemy import UniqueConstraint
        for table_name, table in Base.metadata.tables.items():
            if table_name not in inspector.get_table_names():
                continue
            try:
                existing_unique = {
                    idx.get('name') for idx in inspector.get_indexes(table_name)
                    if idx.get('unique') and idx.get('name')
                }
            except Exception as e:
                print(f"⚠ 读取 {table_name} 索引失败：{e}")
                continue

            for constraint in table.constraints:
                if not isinstance(constraint, UniqueConstraint):
                    continue
                if not constraint.name or constraint.name in existing_unique:
                    continue
                col_names = [c.name for c in constraint.columns]
                if not col_names:
                    continue
                cols_sql = ", ".join(f'"{c}"' for c in col_names)
                create_sql = (
                    f'CREATE UNIQUE INDEX IF NOT EXISTS "{constraint.name}" '
                    f'ON "{table_name}" ({cols_sql})'
                )
                try:
                    with engine.connect() as conn:
                        conn.execute(text(create_sql))
                        conn.commit()
                    print(f"✓ 已添加唯一索引: {table_name}.{constraint.name} ({cols_sql})")
                except Exception as e:
                    es = str(e).lower()
                    if "unique constraint failed" in es or "constraint failed" in es:
                        print(
                            f"⚠ 添加唯一索引失败 {table_name}.{constraint.name}：表里存在违反约束的重复数据，"
                            f"需先清理 (cols={cols_sql})"
                        )
                    else:
                        print(f"✗ 添加唯一索引失败 {table_name}.{constraint.name}: {e}")

        # ─────── 普通 Index 同步（SQLite 版本） ───────
        # 跟 MySQL 端逻辑对齐：__table_args__ 里新增的 sa.Index 或 Column(index=True)
        # 在存量表上不会被 create_all 补出来，这里逐个 CREATE INDEX IF NOT EXISTS。
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
                cols_sql = ", ".join(f'"{c}"' for c in col_names)
                create_sql = (
                    f'CREATE INDEX IF NOT EXISTS "{index.name}" '
                    f'ON "{table_name}" ({cols_sql})'
                )
                try:
                    with engine.connect() as conn:
                        conn.execute(text(create_sql))
                        conn.commit()
                    print(f"✓ 已添加索引: {table_name}.{index.name} ({cols_sql})")
                except Exception as e:
                    print(f"✗ 添加索引失败 {table_name}.{index.name}: {e}")

        print("字段迁移检查完成")
    except Exception as e:
        print(f"自动迁移过程出错: {e}")

def init_sample_data(engine):
    """初始化样例数据（可选）"""
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "main").first():
            from app.core.security import get_password_hash
            db.add(User(username="main", hashed_password=get_password_hash("123456"), fixed=True))
            db.commit()
            print("初始化样例数据完成")
    except Exception as e:
        db.rollback()
        print("初始化数据失败:", e)
    finally:
        db.close()
