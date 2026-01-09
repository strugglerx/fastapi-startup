# FastAPI Base Scaffold

一个简洁、易用、生产就绪的 FastAPI 后端脚手架，开箱即用。

## ✨ 核心特性

- 🚀 **FastAPI 0.115** - 现代化的高性能 Web 框架
- 🔐 **JWT 认证** - 完整的用户认证系统（可选启用）
- 🗄️ **双数据库支持** - 智能切换 MySQL/SQLite（基于环境）
- ⚡ **Redis 缓存** - 高性能缓存 + 连接池管理（5分钟 TTL）
- 🛡️ **统一响应格式** - 自动包装 `{"code": 200, "data": {}}` 格式
- 📝 **自动文档** - Swagger UI / ReDoc / RapiDoc 三合一
- 🧩 **模块化设计** - 清晰的分层架构，易于扩展
- 🎯 **智能异常处理** - 友好的中文错误提示
- 🧪 **完整测试** - pytest 测试基础设施
- 🔧 **Makefile 工具** - 一键启动、部署、清理
- 🐳 **Docker 支持** - 多阶段构建 + docker-compose 一键部署
- 🌏 **东八区时间** - 所有时间戳统一使用 Asia/Shanghai 时区

## 📁 项目结构

```
.
├── backend/                    # 后端目录
│   ├── app/
│   │   ├── api/               # API 路由层
│   │   │   ├── public/        # 公开接口（无需认证）
│   │   │   └── v1/            # API v1 版本
│   │   │       ├── deps.py    # 依赖注入（认证、权限）
│   │   │       └── hello.py   # 示例接口
│   │   ├── boot/              # 应用启动配置
│   │   │   ├── application.py # 应用工厂
│   │   │   ├── config.py      # 配置管理（Pydantic Settings）
│   │   │   ├── logger.py      # 日志配置
│   │   │   ├── middleware.py  # 全局中间件（CORS、响应包装、异常处理）
│   │   │   ├── exceptions.py  # 自定义异常
│   │   │   ├── doc.py         # API 文档配置
│   │   │   └── static.py      # 静态文件服务
│   │   ├── core/              # 核心功能模块
│   │   │   ├── jwt.py         # JWT 工具（加密、解密、验证）
│   │   │   ├── redis_pool.py  # Redis 连接池
│   │   │   ├── limiter.py     # API 限流器
│   │   │   ├── security.py    # 安全工具（密码加密等）
│   │   │   └── sync_task_limiter.py # 同步任务限流
│   │   ├── db/                # 数据库层
│   │   │   ├── __init__.py    # 数据库引擎初始化
│   │   │   ├── models.py      # 数据模型（User、AccessKey）
│   │   │   ├── mysql.py       # MySQL 连接
│   │   │   └── sqlite.py      # SQLite 连接
│   │   ├── library/           # 工具库
│   │   │   ├── debug/         # 调试工具（路由导出等）
│   │   │   ├── json/          # JSON 工具
│   │   │   ├── queue/         # 队列工具
│   │   │   ├── schema/        # Schema 验证
│   │   │   └── url/           # URL 工具
│   │   ├── schema/            # Pydantic 数据模型
│   │   ├── middleware/        # 自定义中间件
│   │   └── main.py            # 应用入口
│   ├── .env                   # 环境变量配置
│   ├── .env.example           # 环境变量示例
│   ├── requirements.txt       # Python 依赖
│   ├── Dockerfile             # Docker 配置
│   ├── docker-compose.yml     # Docker Compose 配置
│   └── .gitignore             # Git 忽略文件
├── tests/                     # 测试目录
├── Makefile                   # 项目管理工具
└── README.md                  # 项目文档
```

## 🚀 快速开始

### 方式一：使用 Makefile（推荐）

```bash
# 1. 安装所有依赖
make install

# 2. 启动后端服务
make run-api

# 3. 启动前端服务（另一个终端）
make run-front
```

### 方式二：手动安装

```bash
# 1. 创建虚拟环境
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库、Redis 等

# 4. 启动服务
uvicorn app.main:app --reload --port 8000
```

## ⚙️ 配置说明

### 环境变量配置（`.env`）

```bash
# ============================================
# 应用配置
# ============================================
APP_ENV=development          # 环境：development/production
APP_DEBUG=true              # 调试模式
APP_CORS_ORIGINS=*          # CORS 允许的源（逗号分隔）
APP_ENABLE_GZIP=true        # 启用 Gzip 压缩

# ============================================
# 数据库配置
# ============================================
# 开发环境自动使用 SQLite (app/data/sqlite.db)
# 生产环境 (APP_ENV=production) 使用 MySQL，需配置以下参数：

# DB_USER=root
# DB_PASSWORD=your_database_password
# DB_HOST=localhost
# DB_PORT=3306
# DB_NAME=fastapi_scaffold

# ============================================
# Redis 配置
# ============================================
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# ============================================
# JWT 配置
# ============================================
JWT_SECRET_KEY=your_jwt_secret_key_here_please_change
JWT_EXPIRE_MINUTES=480
```

### 数据库切换逻辑

```python
# 通过 APP_ENV 环境变量自动切换
if APP_ENV == "production":
    使用 MySQL  # 需要配置 DB_USER、DB_PASSWORD 等
else:
    使用 SQLite  # 默认路径：backend/app/data/sqlite.db
```

## 📚 核心功能详解

### 1. 统一响应格式

所有 API 响应自动包装为统一格式：

```json
// 成功响应
{
  "code": 200,
  "data": {
    "message": "Hello World"
  }
}

// 错误响应
{
  "code": 1,
  "msg": "错误信息"
}
```

**特点：**
- ✅ 自动包装，无需手动返回标准格式
- ✅ 智能检测，避免重复包装
- ✅ 支持流式响应（StreamingResponse）
- ✅ 友好的中文错误提示

### 2. 自定义异常处理

```python
from app.boot.exceptions import APIException

# 抛出业务异常
raise APIException(msg="用户不存在", code=404)

# 返回格式
{
  "code": 404,
  "msg": "用户不存在"
}
```

### 3. JWT 认证

```python
from fastapi import Depends
from app.api.v1.deps import get_current_user

@router.get("/protected")
async def protected_route(current_user = Depends(get_current_user)):
    return {"user": current_user.username}
```

**认证流程：**
1. 登录获取 Token
2. 请求头携带 `Authorization: Bearer <token>`
3. 自动验证并注入 `current_user`

### 4. Redis 缓存

```python
from app.core.redis_pool import get_redis

redis = get_redis()
redis.set("key", "value", ex=3600)  # 设置 1 小时过期
value = redis.get("key")
```

### 5. API 限流

```python
from app.core.limiter import rate_limit

@router.get("/api")
@rate_limit(max_requests=100, window=60)  # 每分钟最多 100 次
async def limited_api():
    return {"status": "ok"}
```

## 🔧 Makefile 命令

```bash
# 安装依赖
make install              # 安装所有依赖（后端 + 前端）
make venv                 # 创建 Python 虚拟环境
make frontend-deps        # 安装前端依赖

# 运行服务
make run-api              # 启动 FastAPI 后端（自动清理端口）
make stop-api             # 停止 FastAPI 后端
make run-front            # 启动 Vue 前端

# 测试
make test                 # 运行所有测试
make test-verbose         # 运行测试并显示详细输出

# 构建和清理
make build                # 构建前端生产包
make clean                # 清理临时文件
```

## 📖 API 文档

启动服务后访问：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **RapiDoc**: http://localhost:8000/rapidoc

### 示例接口

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| Hello World | GET | `/api/v1/hello` | 示例接口 |
| 健康检查 | GET | `/api/v1/ping` | 系统健康状态 |

测试接口：

```bash
curl http://localhost:8000/api/v1/hello
```

返回：

```json
{
  "code": 200,
  "data": {
    "message": "Hello, base scaffold!",
    "status": "success",
    "version": "1.0.0",
    "docs": "/docs"
  }
}
```

## 🧪 测试

使用 pytest 进行测试：

```bash
# 运行所有测试
python -m pytest tests/

# 运行测试并显示详细输出
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_hello.py

# 运行测试并显示覆盖率
python -m pytest tests/ --cov=app --cov-report=html
```

**测试文件示例：**

```python
# tests/test_hello.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_hello_world():
    response = client.get("/api/v1/hello")
    assert response.status_code == 200
    assert response.json()["code"] == 200
    assert "message" in response.json()["data"]
```

## 🔨 如何添加新接口

### 1. 创建路由文件

```python
# backend/app/api/v1/users.py
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["用户管理"])

@router.get("/")
async def get_users():
    return {"users": []}

@router.post("/")
async def create_user(username: str):
    return {"id": 1, "username": username}
```

### 2. 注册路由

```python
# backend/app/api/v1/__init__.py
from fastapi import APIRouter
from . import hello, users  # 导入新模块

router = APIRouter(prefix="/api/v1")

router.include_router(hello.router)
router.include_router(users.router)  # 注册新路由
```

### 3. 访问接口

- http://localhost:8000/api/v1/users
- 自动出现在 `/docs` 文档中

## 🗄️ 数据模型

### User（用户）

```python
- id: 主键
- username: 用户名（唯一）
- hashed_password: 加密密码
- last_login: 最后登录时间
- fixed: 是否为管理员
- created_at / updated_at: 时间戳
```

### AccessKey（访问密钥）

```python
- id: 主键
- secret_key: 密钥内容（唯一）
- description: 密钥描述
- max_qps: 最大 QPS 限制
- created_by: 创建用户 ID
- created_at / updated_at: 时间戳
```

## 🐳 Docker 部署

### 构建镜像

```bash
cd backend
docker build -t fastapi-scaffold .
```

### 运行容器

```bash
docker run -d \
  --name fastapi-app \
  -p 8000:8000 \
  -e APP_ENV=production \
  -e DB_HOST=your_mysql_host \
  -e DB_PASSWORD=your_password \
  fastapi-scaffold
```

# Docker Compose（推荐）

使用 `docker-compose.yml` 快速启动完整环境：

```bash
# 启动所有服务（API、MySQL、Redis）
docker-compose up -d

# 查看日志
docker-compose logs -f api

# 停止服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

**docker-compose.yml 配置说明：**
- **api**: FastAPI 应用服务，端口 8000
- **mysql**: MySQL 8.0 数据库，端口 3306，root 密码 `root123`
- **redis**: Redis 缓存服务，端口 6379

**健康检查：**
- 服务启动后会自动进行健康检查
- 数据库初始化需要等待 10-30 秒
- 可使用 `docker-compose ps` 查看服务状态

## 📝 开发规范

### 代码风格

- 遵循 **PEP 8** 规范
- 使用 **类型注解**（Type Hints）
- 编写清晰的函数和变量名称
- 添加必要的注释和文档字符串

### 提交规范

```
feat: 新增功能
fix: 修复 bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

### 目录规范

- `api/` - 只放路由定义，不写业务逻辑
- `core/` - 核心功能，可复用的工具
- `db/` - 数据库相关，模型定义
- `library/` - 通用工具库
- `schema/` - Pydantic 数据模型

## 🎯 最佳实践

### 1. 环境隔离

```bash
# 开发环境
APP_ENV=development  # 使用 SQLite

# 生产环境
APP_ENV=production   # 使用 MySQL
```

### 2. 配置管理

所有配置通过 `.env` 文件管理，不要硬编码：

```python
# ❌ 不推荐
db_host = "localhost"

# ✅ 推荐
from app.boot import settings
db_host = settings.database.host
```

### 3. 异常处理

使用自定义异常，提供友好提示：

```python
# ❌ 不推荐
raise Exception("error")

# ✅ 推荐
raise APIException(msg="用户名已存在", code=400)
```

### 4. 日志记录

```python
from app.boot import logger

logger.info("用户登录成功")
logger.error("数据库连接失败", exc_info=True)
```

## 🔍 常见问题

### Q: 如何切换数据库？

A: 修改 `.env` 中的 `APP_ENV`：
- `development` → SQLite
- `production` → MySQL

### Q: 端口被占用怎么办？

A: 使用 `make run-api` 会自动清理 8000 端口

### Q: 如何禁用响应自动包装？

A: 在中间件中添加路径到跳过列表：

```python
# backend/app/boot/middleware.py
if request.url.path.startswith(("/docs", "/your-path")):
    return response
```

### Q: 如何添加新的配置项？

A: 在 `backend/app/boot/config.py` 中添加：

```python
class AppConfig(BaseSettings):
    new_config: str = Field(default="value", validation_alias="NEW_CONFIG")
```

然后在 `.env` 中配置：

```bash
NEW_CONFIG=your_value
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License

---

**祝你使用愉快！如有问题欢迎提 Issue 🎉**
