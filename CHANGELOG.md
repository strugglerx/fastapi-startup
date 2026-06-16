# Changelog

本项目所有显著变更记录于此。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

---

## [1.1.1] — 2026-06-16

补丁版本：修复运行时产物路径错位与 Makefile 启动入口 bug，补 `.dockerignore`。

### 修复

- **`auto_docs/` / `routes.md` / 静态资源目录误用 cwd 相对路径** —— 从仓库根启动（如 `uvicorn backend.app.main:app`）时这些产物会洒到仓库根。新增 `app/paths.py` 集中所有项目路径常量（基于 `__file__` 解析），`boot/doc.py`、`boot/static.py`、`library/debug/__init__.py` 改用 `BACKEND_DIR / AUTO_DOCS_DIR / STATIC_DIR / ROUTES_MD_PATH`，无论从哪启动产物都落在 `backend/` 下
- **`make run-api` 启不起来** —— 原 Makefile 中 `cd app && uvicorn main:app` 会因 `main.py` 内的相对导入（`from .boot.application import create_app`）失败。改为在 `backend/` 下执行 `uvicorn app.main:app`；同时端口/主机抽成变量（`make run-api PORT=9000`），新增 `run-api-prod` 目标（多 worker 生产启动）

### 新增

- **`app/paths.py`** —— 集中路径常量（`BACKEND_DIR / APP_DIR / DATA_DIR / STATIC_DIR / AUTO_DOCS_DIR / ROUTES_MD_PATH / LOGS_DIR`）
- **`backend/.dockerignore`** —— 之前缺失，导致 build context 把 `venv/`、`logs/`、`*.sqlite`、`__pycache__/` 等全部传给 Docker daemon。同时修复 `.gitignore` 中误把 `.dockerignore` 自身屏蔽掉的规则

---

## [1.1.0] — 2026-06-16

围绕"AI 驱动开发"做了一轮系统性升级：引入分层架构、现代化基础设施、补齐测试与文档。

### 新增

- **`app/service/` 业务逻辑层** —— 路由保持薄 Controller，事务/规则/外部调用统一沉淀到 service。
  - 示例实现：`UserService`（注册 / 登录 / 列表 / 删除）+ 配套薄路由 `api/v1/user.py`
- **`backend/CLAUDE.md`** —— AI Agent 工作手册：三层职责约束、添加接口流程、常见陷阱、配置项速查表
- **`CLAUDE.md`**（仓库根）—— Monorepo 入口指南
- **`schema/base.py`** —— 泛型 `BaseResponse[T]`，统一响应模型基类
- **`boot/openapi.py`** —— 通过 lazy override 注入 `x-tagGroups` 文档分组
- **`pyproject.toml`** —— pytest + ruff 配置（py39 目标，line-length 120）
- **测试套件扩展** 4 → 27 个：
  - `test_jwt.py` —— 签名/篡改/过期/格式校验
  - `test_security.py` —— bcrypt 哈希/校验/盐随机性
  - `test_errors.py` —— 404 / 405 / 响应包装防重 / 健康检查公开
  - `test_user_service.py` —— Service 层全覆盖（业务码断言）
  - `conftest.py` —— 共享 `TestClient` fixture

### 变更

- **`APP_USE_SQLITE=true` 才走 SQLite**，默认连 MySQL（之前是开发自动 SQLite / 生产 MySQL）
- **响应包装成功 code 改为 `0`**（之前是 `200`），与前端常见约定对齐
- **HTTP 状态码 + body code 分工明确**：
  - `APIException` 业务异常 → HTTP **永远 200**，body code 表达任意业务码（401/403/422/10001…）
  - `StarletteHTTPException`（路由不存在/方法错误）→ 保留真实 HTTP 状态码（404/405），方便 CDN/k8s/监控识别
- **`boot/middleware.py` → `boot/plugins.py`** —— 与 `app/middleware/`（业务中间件）命名解耦
- **生命周期切换为 `lifespan`** —— 替换所有过时的 `@app.on_event("startup")` 钩子
- **CORS 升级**：支持 `*` 通配 + 子域名正则 + 凭证模式；挂载为最外层中间件
- **`app/middleware/access_log.py`** —— 业务访问日志从 `__init__.py` 拆分到独立文件，并跳过 `/docs`、`/health` 等噪音路径
- **`db/models.py` 升级到 SQLAlchemy 2.0 `DeclarativeBase`** —— 消除启动 `MovedIn20Warning`
- **`hashed_password` 字段长度 60 → 128**（适配 bcrypt 输出 + 余量）
- **MySQL `auto_migrate_columns` 加强**：
  - 通过 `TypeDecorator.load_dialect_impl` 识别 `MEDIUMTEXT/LONGTEXT` 等扩展类型
  - 新增 `normalize_mysql_type` —— 忽略 `CHARACTER SET / UNSIGNED / 显示宽度` 等无意义差异，避免假性 `MODIFY`
  - 主键字段跳过类型修改（风险高）
- **`config.py` 瘦身** 220 行 → 100 行：7 个重复 `try/except` 块改为 `Field(default_factory)`；配置加载失败时全局兜底；启动概览改用 `logger` 输出
- **`api/v1/hello.py`** 升级到 Pydantic 响应模型（OpenAPI 文档更完整）
- **`schema/admin.py`** 加字段长度约束 + 清理噪音注释
- **`schema/token.py`** `exp/iat` 类型由 `datetime` 修正为 `int` Unix 时间戳（与 JWT 实际负载一致）
- **`requirements.txt`** —— 移除未使用的 `toml`、`asgiref`；新增 `httpx`、`orjson`
- **README.md / README_ZH.md** 同步本次架构变更（响应格式、目录结构、限流用法、Redis 用法、DB 切换逻辑）

### 修复

- **JWT `datetime.utcnow()` 弃用警告** —— 全面切换到 `datetime.now(timezone.utc)`（Python 3.12 兼容）
- **`verify_token` / `decode_token` 代码重复** —— 合并为单一 `_decode(verify_exp=...)` 私有函数
- **限流器模块顶层实例化导致 import 链崩溃** —— Redis 未启动也能 import；改为 `get_rate_limiter()` 懒加载单例
- **响应包装中间件丢失 headers** —— `JSONResponse` / `StreamingResponse` 重建时正确保留原始响应头（剔除 `content-length`、`content-type` 由框架重算）
- **`is_wrapped_response` 误判**：之前只检查 `code` 字段，业务字段名为 `code` 时会跳过包装。现要求同时包含 `code` + (`data` 或 `msg`)
- **健康检查 `/api/health` 之前 `allow_local_only` 导致负载均衡器探活 403** —— 现已改为公开
- **SQLite `init_sample_data` 重启时重复插入种子数据** —— 补充存在性检查

### 安全

- **密码哈希 MD5 → bcrypt**（直接使用 `bcrypt` 库，避开 passlib 1.7.4 与 bcrypt 5.x 的兼容问题）
- **JWT 默认密钥提示**：生产环境用默认密钥时打 warning（不阻断启动，遵循"配置缺失不影响启动"原则）

### 移除

- `boot/middleware.py`（已拆分到 `boot/plugins.py`）
- `app/library/queue/`（空骨架，待真实队列实现时再加回）

---

## [1.0.0] — 2026-01-06

首版发布。

### 新增

- FastAPI 0.115 + Uvicorn 启动框架
- JWT 鉴权（HMAC-SHA256 自实现）
- AccessKey + IP 限流（Redis Lua 原子脚本）
- Redis 连接池（同步 + 异步 + PubSub）
- MySQL / SQLite 双引擎自动切换
- 模型字段变更自动 `ALTER TABLE` 迁移
- 统一响应包装中间件 `{code, data}`
- 自动文档：Swagger UI / RapiDoc / OpenAPI JSON
- Docker + docker-compose + Makefile 一键启动
- 彩色日志 + 文件轮转
