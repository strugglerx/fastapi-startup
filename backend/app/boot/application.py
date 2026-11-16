import os
import warnings
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI

from .config import app_config
from .plugins import setup_cors, setup_stand_response, setup_exception, setup_custom_server
from app.middleware import setup_access_log, setup_audit_log
from .static import mount_static
from .doc import setup_docs
from .openapi import custom_openapi
from .logger import logger

warnings.filterwarnings("ignore", category=UserWarning, message=".*validate_default.*", module="pydantic")


class ExtendedFastAPI(FastAPI):
    def use(self, plugin: Callable):
        """Vue 风格的 use() —— app.use(setup_cors).use(setup_xxx)"""
        plugin(self)
        return self


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    import os

    # ── 1. 后台线程跑 DDL 迁移（建表 + ALTER TABLE），不阻塞主事件循环 ──
    auto_migrate = os.getenv("AUTO_MIGRATE_ON_BOOT", "true").lower() == "true"
    migration_task = None
    if not auto_migrate:
        logger.info("○ AUTO_MIGRATE_ON_BOOT=false，跳过启动迁移（请手动跑 run_db_migration）")
    else:
        try:
            def _run_migration_in_thread():
                from app.db import run_db_migration
                run_db_migration()

            logger.info("⏳ 数据库字段迁移已在后台线程启动，服务主流程不等待迁移完成...")
            migration_task = asyncio.create_task(asyncio.to_thread(_run_migration_in_thread))
        except Exception as e:
            logger.exception(f"启动迁移任务失败: {e}")
            migration_task = None

    # ── 2. 等迁移完成后再跑 seed（seed 依赖表已存在） ──
    async def _run_seeds():
        if migration_task:
            try:
                await migration_task
            except Exception as e:
                logger.error(f"等待迁移任务完成时异常: {e}")

        # 启动：种子管理员（容错，DB 异常时不阻断启动）
        try:
            from app.service import MenuService, RoleService, UserService
            RoleService.ensure_seed_roles()
            MenuService.ensure_source_migration()
            MenuService.ensure_seed_menus()   # 首次部署：菜单表为空时自动写入内置菜单
            r = UserService.ensure_seed_admin()
            if r.get("created"):
                logger.warning(
                    f"⚠ 已创建种子管理员 {r.get('email')}（密码来自 SEED_ADMIN_PASSWORD），"
                    "请首次登录后立即改密"
                )
            elif r.get("skipped"):
                logger.warning(
                    "⚠ 未配置 SEED_ADMIN_PASSWORD，跳过种子管理员创建。"
                    "请设置该环境变量后重启，或手工建号。"
                )
            else:
                logger.info(f"✓ 种子管理员已存在: {r.get('email')}")
        except Exception as e:
            logger.warning(f"种子管理员 ensure 失败（已跳过）: {e}")

        # 一次性历史审计日志脱敏（首次启动时跑，Redis 标记已完成）
        try:
            from app.service import AuditService
            AuditService.scrub_history()
        except Exception as e:
            logger.warning(f"审计日志历史脱敏跳过（不影响新写入的日志已脱敏）: {e}")

    asyncio.create_task(_run_seeds())

    # 启动异步任务队列 Worker 与定时任务调度器
    try:
        from app.core.tasks import task_worker_loop, enqueue_task
        import asyncio
        
        asyncio.create_task(task_worker_loop())
        
        async def audit_cleanup_scheduler():
            retention_days = int(os.getenv("AUDIT_LOG_RETENTION_DAYS", "180"))
            logger.info(f"审计日志自动清理调度器启动，日志保留天数: {retention_days}天")
            while True:
                try:
                    await enqueue_task("clean_old_audit_logs", retention_days)
                except Exception as ex:
                    logger.error(f"下发清理审计日志任务异常: {ex}")
                # 每 24 小时调度一次
                await asyncio.sleep(24 * 3600)
                
        asyncio.create_task(audit_cleanup_scheduler())
    except Exception as e:
        logger.warning(f"异步任务队列/调度器启动失败: {e}")

    try:
        mount_static(app)
        logger.info("静态资源已挂载到 /")
    except Exception as e:
        logger.error(f"静态资源挂载失败: {e}")

    if os.getenv("APP_ENV") != "production":
        try:
            from app.library.debug import generate_route_md
            generate_route_md(app)
        except Exception as e:
            logger.debug(f"路由文档生成跳过: {e}")

    yield

    # 关闭
    logger.info("应用已关闭")


def create_app() -> FastAPI:
    is_prod = os.getenv("APP_ENV") == "production"

    app = ExtendedFastAPI(
        debug=app_config.debug,
        title="engine",
        version="1.1.0",
        json_as_ascii=False,
        docs_url=None if is_prod else "/docs",
        openapi_url=None if is_prod else "/openapi.json",
        lifespan=lifespan,
    )

    # 内层 → 外层（FastAPI 中间件执行顺序与挂载顺序相反）
    app.use(setup_stand_response)
    app.use(setup_exception)
    app.use(setup_docs)
    app.use(setup_custom_server)
    app.use(setup_audit_log)
    app.use(setup_access_log)
    app.use(setup_cors)  # 最外层：先处理 OPTIONS / 跨域头

    app.use(lambda a: logger.info(f"所有插件已加载: {a.title}"))

    custom_openapi(app)
    return app
