# CLAUDE.md — AI Agent 工作说明

> 本文件供 Claude Code / Codex 等 AI 助手使用。任何 AI 在编辑本项目前必须阅读。

## 一句话定位

**AI 驱动开发的 FastAPI 企业级脚手架**：默认 MySQL（`APP_USE_SQLITE=true` 切 SQLite），自动迁移字段，JWT + AccessKey 双鉴权，统一响应包装，插件式启动架构。

## 顶级规则

1. **不破坏 `.env` 加载机制** —— 由 `boot/config.py` 用 `python-dotenv` 加载，缺配置回落默认值，**永远不让项目启动失败**。
2. **默认 MySQL，特殊 env 才 SQLite** —— `APP_USE_SQLITE=true` 才走 SQLite。生产环境不要切 SQLite。
3. **响应必须是 `{code, data}` 或 `{code, msg}`** —— `code=0` 表示成功，业务码请非零。响应包装由 `boot/plugins.py:setup_stand_response` 自动处理，**业务代码直接返回 dict 或 Pydantic 模型即可**。
4. **新增字段免迁移** —— 改 `db/models.py` 加列，重启自动 `ALTER TABLE`。不要写 alembic 迁移，本项目不用。
5. **中间件分两层**，别放错地方：
   - **框架插件** → `app/boot/plugins.py`（CORS、响应包装、异常处理）
   - **业务中间件** → `app/middleware/`（访问日志、链路追踪等）
6. **业务逻辑必须下沉到 `app/service/`** —— `api/v1/` 只做参数解析和返回，**禁止在路由里写 DB 查询、规则判断、跨模型操作**。详见下方"三层职责"。
7. **有显著改动必须更新 `CHANGELOG.md`**（仓库根目录），格式遵循 Keep a Changelog：
   - `[Unreleased]` 节累积未发版改动
   - 发版时改成 `[x.y.z] — YYYY-MM-DD` 并同步升级 `boot/application.py` 与 `pyproject.toml` 的 `version`
   - 仅改注释 / 修笔误 / 重命名变量这类小事不必记

## 三层职责（必读）

```
api/v1/         ← 薄 Controller：参数解析、鉴权 Depends、调 service、返回结果
service/        ← 业务逻辑：事务、规则校验、跨模型操作、外部调用
db/models.py    ← ORM 模型，加字段重启自动迁移
```

| 层 | 该做 | 不该做 |
|---|------|------|
| **api** | 解析 Request、调 Depends、调 service、返回 dict/Pydantic | 不写 SQL、不写业务规则、不开事务 |
| **service** | 开事务、查 DB、校验业务、抛 `APIException` | 不接触 Request/Response、不返 ORM 对象 |
| **db** | 模型定义、字段定义 | 不写业务方法 |

**为什么这么分？**
- AI 写代码有明确目的地，不会顺手把所有东西堆 api 里
- service 可被路由、Celery、CLI 共用
- 业务测试脱离 HTTP 直接跑 service（看 `tests/test_user_service.py`）

## 目录结构

```
backend/app/
├── api/
│   ├── public/      # 公开接口（健康检查、前端静态）
│   └── v1/          # 业务接口
│       ├── deps.py  # 依赖注入：get_current_user / require_admin / apply_tenant_filter
│       └── hello.py # 示例
├── boot/            # 应用启动层（框架级，业务代码勿动）
│   ├── application.py  # create_app 工厂 + lifespan
│   ├── config.py       # 配置加载（pydantic-settings）
│   ├── plugins.py      # 框架插件：CORS / 响应包装 / 异常
│   ├── logger.py       # 彩色日志 + 文件轮转
│   ├── exceptions.py   # APIException
│   ├── doc.py          # RapiDoc 文档页
│   ├── openapi.py      # OpenAPI x-tagGroups 分组
│   └── static.py       # 静态资源挂载
├── core/            # 核心工具（基础设施，不放业务）
│   ├── jwt.py              # HMAC-SHA256 自实现 JWT
│   ├── security.py         # bcrypt 密码哈希
│   ├── redis_pool.py       # Redis 单例 + PubSub 管理器
│   ├── limiter.py          # 基于 AccessKey 的 IP 限流（懒加载）
│   └── sync_task_limiter.py
├── service/         # 业务逻辑层（事务/规则/编排）
│   ├── __init__.py
│   └── user_service.py     # 示例：注册/登录/列表/删除
├── db/
│   ├── __init__.py  # 引擎切换：MySQL（默认）/ SQLite（APP_USE_SQLITE=true）
│   ├── models.py    # SQLAlchemy 2.0 DeclarativeBase 风格
│   ├── mysql.py     # MySQL 初始化 + auto_migrate_columns
│   └── sqlite.py    # SQLite 初始化 + auto_migrate_columns
├── middleware/      # 业务中间件（按文件拆分）
│   ├── __init__.py  # 只做导出
│   └── access_log.py
├── schema/          # Pydantic 模型
│   ├── base.py      # BaseResponse[T] 泛型
│   ├── admin.py
│   ├── task.py
│   └── token.py
├── library/         # 工具库（debug / json / schema / url）
└── main.py          # 入口，include_router
```

## 添加新接口的最小流程（AI 必读）

> 假设要加 `/api/v1/article/list` 文章列表接口。**顺序：DB → Service → API → 注册**。

### Step 1: 在 `db/models.py` 增加模型

```python
class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text)
    created_by = Column(Integer, index=True)
    # 新增字段直接加，重启自动 ALTER TABLE
```

### Step 2: 在 `service/` 写业务逻辑

```python
# app/service/article_service.py
from app.db import SessionLocal, Article
from app.boot import APIException


class ArticleService:
    @classmethod
    def list_articles(cls, page: int, size: int, user_id: int) -> dict:
        page, size = max(1, page), max(1, min(size, 100))
        with SessionLocal() as db:
            q = db.query(Article).filter(Article.created_by == user_id)
            total = q.count()
            items = q.order_by(Article.id.desc()).offset((page - 1) * size).limit(size).all()
            return {
                "total": total,
                "items": [{"id": a.id, "title": a.title} for a in items],
            }

    @classmethod
    def create(cls, user_id: int, title: str, content: str) -> dict:
        if not title.strip():
            raise APIException("标题不能为空", code=20001, status_code=400)
        with SessionLocal() as db:
            a = Article(title=title.strip(), content=content, created_by=user_id)
            db.add(a)
            db.commit()
            db.refresh(a)
            return {"id": a.id}
```

记得在 `service/__init__.py` 暴露：
```python
from .article_service import ArticleService
__all__ = [..., "ArticleService"]
```

### Step 3: 在 `api/v1/` 写薄路由

```python
# app/api/v1/article.py
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from app.api.v1.deps import get_current_user
from app.service import ArticleService

router = APIRouter(prefix="/article", tags=["文章"])


class CreateReq(BaseModel):
    title: str
    content: str = ""


@router.get("/list")
async def article_list(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user=Depends(get_current_user),
):
    return ArticleService.list_articles(page, size, user.id)


@router.post("/create")
async def create(req: CreateReq, user=Depends(get_current_user)):
    return ArticleService.create(user.id, req.title, req.content)
```

### Step 4: 在 `api/v1/__init__.py` 注册

```python
from . import hello, user, article
router.include_router(article.router)
```

启动即可访问 `GET /api/v1/article/list`、`POST /api/v1/article/create`。

### 参考实现

完整可跑的示例：`app/service/user_service.py` + `app/api/v1/user.py` + `tests/test_user_service.py`。

## 鉴权方式

```python
from app.api.v1.deps import get_current_user, require_admin, get_current_user_no_err

# 强制登录
@router.get("/profile")
async def profile(user=Depends(get_current_user)): ...

# 强制管理员
@router.delete("/user/{id}")
async def delete_user(id: int, admin=Depends(require_admin)): ...

# 可选登录（未登录返回 None）
@router.get("/public-feed")
async def feed(user=Depends(get_current_user_no_err)): ...
```

## 异常处理

```python
from app.boot import APIException

raise APIException(msg="资源不存在", code=10001, status_code=404)
# ↑ 自动转换为 HTTP 404，body: {"code": 10001, "msg": "资源不存在"}
```

## 配置项

| 环境变量 | 作用 | 默认 |
|----------|------|------|
| `APP_ENV` | `development` / `production` | development |
| `APP_USE_SQLITE` | `true` 才用 SQLite | 不设置则默认 MySQL |
| `APP_DEBUG` | 调试模式 | true |
| `APP_CORS_ORIGINS` | CORS 域名，逗号分隔，`*` 表示全部 | * |
| `JWT_SECRET_KEY` | JWT 签名密钥（生产必改） | 默认值（warning） |
| `JWT_EXPIRE_MINUTES` | Token 有效期 | 480 |
| `DB_USER/PASSWORD/HOST/PORT/NAME` | MySQL 配置 | root/空/localhost/3306/queue_platform |
| `REDIS_HOST/PORT/PASSWORD` | Redis 配置 | 127.0.0.1/6379/空 |
| `MAX_SYNC_CONCURRENT` | 同步任务并发上限 | 10 |

## 测试

```bash
pytest            # 跑全部测试（17 个）
pytest tests/test_jwt.py -v  # 跑单文件
```

测试位置：`backend/tests/`，新增测试请遵循 `test_*.py` 命名。

## 常见陷阱

| ❌ 错误做法 | ✅ 正确做法 |
|---|---|
| 在 `api/v1/xxx.py` 里写 DB 查询和业务规则 | 下沉到 `app/service/` |
| 在 service 里抛 `HTTPException` | 抛 `APIException(msg, code, status_code)`，框架会处理 |
| 在 service 里直接 return ORM 对象 | 转成 dict / Pydantic 模型再返回（避免 Session 关闭后访问字段崩溃） |
| 在 boot/ 下加业务中间件 | 放到 `app/middleware/` |
| 用 alembic 写迁移脚本 | 直接改 `models.py`，重启自动迁移 |
| 在路由里返回 `JSONResponse({"code": 0, ...})` | 直接返回 dict，中间件会包装 |
| 把 Redis/DB 在模块顶层实例化 | 用 `RedisPool.get_redis()` / `SessionLocal()` 懒加载 |
| 把 `@app.on_event("startup")` 用作启动钩子 | 用 `boot/application.py` 的 `lifespan` |
| MD5/SHA1 哈希密码 | 用 `app.core.security.get_password_hash`（bcrypt） |

## 启动命令

```bash
cd backend
uvicorn app.main:app --reload --port 8000
# 或
make run-api
```

## 文档

- Swagger: <http://localhost:8000/docs>
- RapiDoc: <http://localhost:8000/doc/rapidoc>
- OpenAPI JSON: <http://localhost:8000/openapi.json>
- 路由表（启动时自动生成）：`backend/routes.md`
