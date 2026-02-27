English | [中文简体](./README_ZH.md)

# FastAPI Base Scaffold

A concise, easy-to-use, production-ready FastAPI backend scaffold, out of the box.

## ✨ Core Features

- 🚀 **FastAPI 0.115** - Modern, high-performance Web framework.
- 🔐 **JWT Authentication** - Complete user authentication system (enable/disable optional).
- 🗄️ **Dual Database Support** - Intelligent switching between MySQL/SQLite (based on environment).
- ⚡ **Redis Cache** - High-performance caching + connection pool management (5-minute TTL).
- 🛡️ **Unified Response Format** - Automatically wraps responses in `{"code": 200, "data": {}}` format.
- 📝 **Auto Documentation** - Three-in-one Swagger UI / ReDoc / RapiDoc.
- 🧩 **Modular Design** - Clear layered architecture, easy to extend.
- 🎯 **Intelligent Exception Handling** - Friendly error messages.
- 🧪 **Complete Testing** - pytest testing infrastructure.
- 🔧 **Makefile Tools** - One-click start, deploy, and cleanup.
- 🐳 **Docker Support** - Multi-stage builds + one-click deployment with docker-compose.
- 🌏 **UTC+8 Timezone** - All timestamps use the `Asia/Shanghai` timezone.

## 📁 Project Structure

```
.
├── backend/                    # Backend directory
│   ├── app/
│   │   ├── api/               # API Routing layer
│   │   │   ├── public/        # Public interfaces (no auth required)
│   │   │   └── v1/            # API v1 version
│   │   │       ├── deps.py    # Dependency injection (Auth, Permissions)
│   │   │       └── hello.py   # Example interface
│   │   ├── boot/              # App startup configuration
│   │   │   ├── application.py # App factory
│   │   │   ├── config.py      # Configuration management (Pydantic Settings)
│   │   │   ├── logger.py      # Logger configuration
│   │   │   ├── middleware.py  # Global middleware (CORS, Response wrapping, Exception handling)
│   │   │   ├── exceptions.py  # Custom exceptions
│   │   │   ├── doc.py         # API documentation config
│   │   │   └── static.py      # Static file service
│   │   ├── core/              # Core functional modules
│   │   │   ├── jwt.py         # JWT tools (Encrypt, Decrypt, Verify)
│   │   │   ├── redis_pool.py  # Redis connection pool
│   │   │   ├── limiter.py     # API Rate limiter
│   │   │   ├── security.py    # Security tools (Password hashing, etc.)
│   │   │   └── sync_task_limiter.py # Sync task limiter
│   │   ├── db/                # Database layer
│   │   │   ├── __init__.py    # Database engine initialization
│   │   │   ├── models.py      # Data models (User, AccessKey)
│   │   │   ├── mysql.py       # MySQL connection
│   │   │   └── sqlite.py      # SQLite connection
│   │   ├── library/           # Utility libraries
│   │   │   ├── debug/         # Debug tools (Route export, etc.)
│   │   │   ├── json/          # JSON utilities
│   │   │   ├── queue/         # Queue utilities
│   │   │   ├── schema/        # Schema validation
│   │   │   └── url/           # URL utilities
│   │   ├── schema/            # Pydantic data models
│   │   ├── middleware/        # Custom middlewares
│   │   └── main.py            # Application entry point
│   ├── .env                   # Environment variables configuration
│   ├── .env.example           # Environment variables example
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile             # Docker configuration
│   ├── docker-compose.yml     # Docker Compose configuration
│   └── .gitignore             # Git ignore file
├── tests/                     # Testing directory
├── Makefile                   # Project management tool
└── README.md                  # Project documentation
```

## 🚀 Quick Start

### Option 1: Using Makefile (Recommended)

```bash
# 1. Install all dependencies
make install

# 2. Start the backend service
make run-api

# 3. Start the frontend service (in another terminal)
make run-front
```

### Option 2: Manual Installation

```bash
# 1. Create a virtual environment
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# Edit .env file to configure database, Redis, etc.

# 4. Start the service
uvicorn app.main:app --reload --port 8000
```

## ⚙️ Configuration

### Environment Variables (`.env`)

```bash
# ============================================
# APP CONFIGURATION
# ============================================
APP_ENV=development          # Environment: development/production
APP_DEBUG=true              # Debug mode
APP_CORS_ORIGINS=*          # CORS allowed origins (comma separated)
APP_ENABLE_GZIP=true        # Enable Gzip compression

# ============================================
# DATABASE CONFIGURATION
# ============================================
# SQLite is used automatically in development (app/data/sqlite.db)
# For production (APP_ENV=production), MySQL is used, configure the following:

# DB_USER=root
# DB_PASSWORD=your_database_password
# DB_HOST=localhost
# DB_PORT=3306
# DB_NAME=fastapi_scaffold

# ============================================
# REDIS CONFIGURATION
# ============================================
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# ============================================
# JWT CONFIGURATION
# ============================================
JWT_SECRET_KEY=your_jwt_secret_key_here_please_change
JWT_EXPIRE_MINUTES=480
```

### Database Switching Logic

```python
# Automatically switch based on APP_ENV
if APP_ENV == "production":
    USE MySQL  # Requires DB_USER, DB_PASSWORD, etc.
else:
    USE SQLite  # Default path: backend/app/data/sqlite.db
```

## 📚 Core Features Deep Dive

### 1. Unified Response Format

All API responses are automatically wrapped in a unified format:

```json
// Success Response
{
  "code": 200,
  "data": {
    "message": "Hello World"
  }
}

// Error Response
{
  "code": 1,
  "msg": "Error Message"
}
```

**Features:**
- ✅ Auto-wrapping, no need to manually return standard formats.
- ✅ Intelligent detection to avoid double wrapping.
- ✅ Supports StreamingResponse.
- ✅ Friendly error messages.

### 2. Custom Exception Handling

```python
from app.boot.exceptions import APIException

# Raise a business exception
raise APIException(msg="User not found", code=404)

# Response format
{
  "code": 404,
  "msg": "User not found"
}
```

### 3. JWT Authentication

```python
from fastapi import Depends
from app.api.v1.deps import get_current_user

@router.get("/protected")
async def protected_route(current_user = Depends(get_current_user)):
    return {"user": current_user.username}
```

**Authentication Flow:**
1. Login to get Token.
2. Include `Authorization: Bearer <token>` in request headers.
3. Automatically verify and inject `current_user`.

### 4. Redis Caching

```python
from app.core.redis_pool import get_redis

redis = get_redis()
redis.set("key", "value", ex=3600)  # Set 1 hour expiration
value = redis.get("key")
```

### 5. API Rate Limiting

```python
from app.core.limiter import rate_limit

@router.get("/api")
@rate_limit(max_requests=100, window=60)  # Max 100 requests per minute
async def limited_api():
    return {"status": "ok"}
```

## 🔧 Makefile Commands

```bash
# Install dependencies
make install              # Install all dependencies (Backend + Frontend)
make venv                 # Create Python virtual environment
make frontend-deps        # Install frontend dependencies

# Run services
make run-api              # Start FastAPI backend (cleans port automatically)
make stop-api             # Stop FastAPI backend
make run-front            # Start Vue frontend

# Test
make test                 # Run all tests
make test-verbose         # Run tests with detailed output

# Build and Clean
make build                # Build production bundle for frontend
make clean                # Clean temporary files
```

## 📖 API Documentation

Access after starting the service:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **RapiDoc**: http://localhost:8000/rapidoc

### Example Endpoints

| Interface | Method | Path | Description |
|-----------|--------|------|-------------|
| Hello World | GET | `/api/v1/hello` | Example endpoint |
| Health Check | GET | `/api/v1/ping` | System health status |

Testing the endpoint:

```bash
curl http://localhost:8000/api/v1/hello
```

Response:

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

## 🧪 Testing

Run tests with pytest:

```bash
# Run all tests
python -m pytest tests/

# Run tests with detailed output
python -m pytest tests/ -v

# Run a specific test file
python -m pytest tests/test_hello.py

# Run tests with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

**Test Example:**

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

## 🔨 How to Add New Endpoints

### 1. Create a Routing File

```python
# backend/app/api/v1/users.py
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["User Management"])

@router.get("/")
async def get_users():
    return {"users": []}

@router.post("/")
async def create_user(username: str):
    return {"id": 1, "username": username}
```

### 2. Register the Route

```python
# backend/app/api/v1/__init__.py
from fastapi import APIRouter
from . import hello, users  # Import new module

router = APIRouter(prefix="/api/v1")

router.include_router(hello.router)
router.include_router(users.router)  # Register new route
```

### 3. Access Endpoint

- http://localhost:8000/api/v1/users
- Automatically appears in `/docs`.

## 🗄️ Data Models

### User

```python
- id: Primary Key
- username: Username (Unique)
- hashed_password: Encrypted password
- last_login: Last login time
- fixed: Is admin
- created_at / updated_at: Timestamps
```

### AccessKey

```python
- id: Primary Key
- secret_key: Key content (Unique)
- description: Description
- max_qps: Max QPS limit
- created_by: Created by User ID
- created_at / updated_at: Timestamps
```

## 🐳 Docker Deployment

### Build Image

```bash
cd backend
docker build -t fastapi-scaffold .
```

### Run Container

```bash
docker run -d \
  --name fastapi-app \
  -p 8000:8000 \
  -e APP_ENV=production \
  -e DB_HOST=your_mysql_host \
  -e DB_PASSWORD=your_password \
  fastapi-scaffold
```

# Docker Compose (Recommended)

Use `docker-compose.yml` to quickly start the full environment:

```bash
# Start all services (API, MySQL, Redis)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

**docker-compose.yml configuration:**
- **api**: FastAPI application service, port 8000.
- **mysql**: MySQL 8.0 database, port 3306, root password `root123`.
- **redis**: Redis cache service, port 6379.

**Health Check:**
- Services automatically perform health checks after startup.
- Database initialization takes 10-30 seconds.
- Use `docker-compose ps` to check service status.

## 📝 Development Standards

### Code Style

- Follow **PEP 8**.
- Use **Type Hints**.
- Write clear function and variable names.
- Add necessary comments and docstrings.

### Commit Standards

```
feat: New feature
fix: Bug fix
docs: Documentation update
style: Code formatting
refactor: Refactor
test: Test related
chore: Build/Tool related
```

### Directory Standards

- `api/` - Routing definitions only, no business logic.
- `core/` - Core features, reusable utilities.
- `db/` - Database related, model definitions.
- `library/` - General utility libraries.
- `schema/` - Pydantic data models.

## 🎯 Best Practices

### 1. Environment Isolation

```bash
# Development
APP_ENV=development  # Use SQLite

# Production
APP_ENV=production   # Use MySQL
```

### 2. Configuration Management

Manage all configs via `.env`, do not hardcode:

```python
# ❌ Not recommended
db_host = "localhost"

# ✅ Recommended
from app.boot import settings
db_host = settings.database.host
```

### 3. Exception Handling

Use custom exceptions for friendly hints:

```python
# ❌ Not recommended
raise Exception("error")

# ✅ Recommended
raise APIException(msg="Username already exists", code=400)
```

### 4. Logging

```python
from app.boot import logger

logger.info("User login successful")
logger.error("Database connection failed", exc_info=True)
```

## 🔍 FAQ

### Q: How to switch databases?

A: Modify `APP_ENV` in `.env`:
- `development` → SQLite
- `production` → MySQL

### Q: What if the port is occupied?

A: Use `make run-api`, it automatically cleans up port 8000.

### Q: How to disable automatic response wrapping?

A: Add the path to the skip list in the middleware:

```python
# backend/app/boot/middleware.py
if request.url.path.startswith(("/docs", "/your-path")):
    return response
```

### Q: How to add new configuration items?

A: Add to `backend/app/boot/config.py`:

```python
class AppConfig(BaseSettings):
    new_config: str = Field(default="value", validation_alias="NEW_CONFIG")
```

Then configure in `.env`:

```bash
NEW_CONFIG=your_value
```

## 🤝 Contribution

Issues and Pull Requests are welcome!

## 📄 License

MIT License

---

**Enjoy using FastAPI Base Scaffold! 🎉**
