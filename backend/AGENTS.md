# Backend Agent Guide (backend/AGENTS.md)

欢迎开发 FastAPI 后端。编辑代码前请务必阅读本指南，遵循约定以确保代码质量与系统稳定。

## 📁 目录结构与职责

```
backend/app/
├── api/             # 路由控制层
│   ├── public/      # 公开接口（无需 Token 认证）
│   └── v1/          # 业务接口（挂载身份认证与权限校验）
│       └── deps.py  # 共享依赖注入项（用户验证、权限、限流）
├── boot/            # 服务启动器与全局插件初始化
├── core/            # 核心机制（JWT、Redis、密码安全、异步队列任务）
│   └── tasks.py     # 异步/定时任务定义与队列消费者
├── db/              # 数据库操作层
│   ├── models.py    # 唯一的数据模型声明表
│   └── mysql.py     # 自动迁移引擎逻辑
├── middleware/      # 中间件（审计日志拦截、访问日志）
├── public/          # 静态文件目录（前端打包产物输出，包含 uploads/ 文件上传）
├── schema/          # Pydantic 传输模型 (可选，亦可直接写在 Router 文件中)
├── service/         # 业务逻辑服务层 (CRUD 核心逻辑)
└── main.py          # 服务入口
```

## 🛠️ 后端开发约定与陷阱

### 1. 自动表迁移
- **千万不要**使用 `Alembic` 等迁移脚本。
- 所有的表定义必须统一写在 `app/db/models.py` 中。
- 新增模型后，重启后台服务，`Base.metadata.create_all()` 与 `auto_migrate_columns()` 能够自动完成数据库建表和字段追加。

### 2. 统一响应格式
- 全局中间件已包装响应格式，路由层函数**直接返回** dict 或 Pydantic 模型即可。
- **禁止**在路由函数内手动书写 `{"code": 0, "data": ...}`。
- 发生业务错误时，直接抛出 `APIException(msg="错误信息", code=错误码, status_code=状态码)`，框架会自动拦截并格式化输出。

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
- 消费者轮询在 `app/boot/application.py` 的 lifespan 阶段以独立协程运行。如有新任务类型，在 `app/core/tasks.py` 中的 `task_worker_loop` 内注册对应的任务处理器函数即可。

### 6. 文件上传服务
- 建议使用 `/api/v1/file/upload` 统一处理上传，该服务会自动计算文件 MD5 进行去重秒传，返回的静态资源路径可通过 `/uploads/{hash}.{ext}` 直接回显（已被根目录静态映射支持）。
