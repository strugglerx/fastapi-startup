# Backend Agent Guide (backend/AGENTS.md)

欢迎开发 FastAPI 后端。编辑代码前请务必阅读本指南，遵循约定以确保代码质量与系统稳定。

## 📁 目录结构与职责

```
backend/app/
├── api/             # 路由控制层
│   ├── public/      # 公开接口（无需 Token 认证）
│   └── v1/          # 业务接口（挂载身份认证与权限校验）
│       └── deps.py  # 共享依赖注入项（用户验证、权限、限流、raw_response）
├── boot/            # 服务启动器与全局插件初始化
├── core/            # 核心机制（JWT、Redis、密码安全、雪花ID、加密、时间时区、异步任务）
│   ├── snowflake.py # 分布式雪花算法主键生成器
│   ├── crypto.py    # 对称加密与敏感数据脱敏掩码
│   ├── time.py      # 东八区时区管理与 naive datetime 修复
│   └── tasks.py     # 异步/定时任务定义与队列消费者
├── db/              # 数据库操作层
│   ├── models/      # ORM 模型（按域拆分子模块，__init__.py 统一 re-export）
│   │   ├── base.py  # Base / SfPk / 共享列类型 (FlexibleJSONType / MediumText)
│   │   ├── auth.py  # User / AccessKey / RefreshToken
│   │   └── system.py# 菜单、角色、审计日志、文件存储、数据字典
│   ├── mysql.py     # MySQL 连接与 DDL / 索引 / 唯一约束自动迁移
│   └── sqlite.py    # SQLite 连接与沙箱环境支持
├── library/         # 基础类库（JSON 安全序列化、存储抽象等）
│   └── json/        # dumps_jssafe (防前端大整数丢失精度)
├── middleware/      # 中间件（审计日志拦截、访问日志）
├── public/          # 静态文件目录（包含 uploads/ 文件上传）
├── schema/          # Pydantic 传输模型
├── service/         # 业务逻辑服务层 (按域拆分子包与 mixin 架构)
│   └── user/        # 用户管理与双 Token 认证实现
└── paths.py         # 权威项目路径常量定义
```

## 🛠️ 后端开发约定与陷阱

### 1. 自动表与索引迁移
- **千万不要**使用 `Alembic` 等迁移脚本。
- 所有的表定义写在 `app/db/models/` 对应子模块中（`__init__.py` 统一 re-export，import 路径保持不变）。
- 支持列追加、列类型适配、`__table_args__` 内声明的 `UniqueConstraint` 与复合 `Index` 自动补齐。
- 主键推荐使用 `id = SfPk()` 雪花算法，天然支持分布式且全库唯一。

### 2. 统一响应格式与跳过包装
- 全局中间件已包装响应格式，路由层函数**直接返回** dict 或 Pydantic 模型即可。
- **禁止**在路由函数内手动书写 `{"code": 0, "data": ...}`。
- 发生业务错误时，直接抛出 `APIException(msg="错误信息", code=错误码, status_code=状态码)`，框架会自动拦截并格式化输出。
- 若特定接口需要原样返回（如 OpenAPI、SSE、二进制流、第三方 Webhook）：
  ```python
  from app.api.v1.deps import raw_response

  @router.post("/endpoint", dependencies=[Depends(raw_response)])
  async def endpoint():
      ...
  ```

### 3. API 权限验证
- 所有的增删改接口应配置路由权限拦截：
  ```python
  from app.api.v1.deps import require_permission

  # 要求拥有 "system:my_module:create" 菜单授权
  @router.post("", dependencies=[Depends(require_permission("system:my_module:create"))])
  async def create_item():
      ...
  ```

### 4. API 速率限制 (Rate Limiting)
- 敏感或高并发接口应合理配置 Redis 限流器：
  ```python
  from app.api.v1.deps import RateLimiter

  # 限制该接口每 60 秒同一客户端/用户最多调用 10 次
  @router.post("/action", dependencies=[Depends(RateLimiter(limit=10, window=60, name="action_limit"))])
  async def action():
      ...
  ```

### 5. 异步/定时任务
- 耗时逻辑（如发信、日志清理等）不允许直接阻塞 HTTP 线程，请下发到 Redis 任务队列：
  ```python
  from app.core.tasks import enqueue_task

  # 下发异步清理审计日志任务 (延迟执行)
  await enqueue_task("clean_old_audit_logs", retention_days)
  ```

### 6. 双 Token 认证与安全机制
- 系统采用 Access Token（短效，默认 8h）+ Refresh Token（长效，默认 30d）架构。
- 数据库只存储 Refresh Token 的 SHA-256 哈希值，防止库泄露；换发时强制 Rotate 轮转防重放。
- 内置针对账号与 IP 的 Redis 爆破锁定保护机制（连续输错 5 次临时锁定 15 分钟）。

### 7. 测试安全全局守卫
- `tests/conftest.py` 会在启动任何测试前强制指定 SQLite 内存/本地沙箱并断言引擎类型。
- 严禁在测试中绕过 conftest 或将测试直接指向含有生产/开发业务数据的 MySQL 数据库。
