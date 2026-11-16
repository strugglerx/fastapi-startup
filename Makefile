# 项目启动工具
.PHONY: install venv frontend-deps run run-api stop-api run-front build test clean help \
        docker-build docker-build-amd64 docker-up docker-stop docker-logs docker-ps

# 可选包含腾讯云配置（如果存在 hack/tencent.mk）
-include ./hack/tencent.mk

# 配置
PROJECT_ROOT := $(shell pwd)
VENV := $(PROJECT_ROOT)/backend/venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
NPM = pnpm

# Docker 镜像配置
IMAGE_NAME            ?= fastapi-startup
_TAG                  ?= latest
DOCKER_IMAGE          ?= $(IMAGE_NAME):$(_TAG)
DOCKER_AMD64_PLATFORM ?= linux/amd64
DOCKER_CONTAINER_NAME ?= $(IMAGE_NAME)
DOCKER_HOST_PORT      ?= 8000

# 默认目标
.DEFAULT_GOAL := help

help:
	@echo "📋 可用命令:"
	@echo ""
	@echo "  == 开发 =="
	@echo "  make install              - 安装所有依赖（后端 + 前端）"
	@echo "  make venv                 - 创建 Python 虚拟环境并安装后端依赖"
	@echo "  make frontend-deps        - 安装前端依赖"
	@echo "  make run-api              - 启动 FastAPI 后端服务（自动清理端口）"
	@echo "  make stop-api             - 停止 FastAPI 后端服务"
	@echo "  make run-front            - 启动 Vue 前端服务"
	@echo "  make build                - 构建前端生产包"
	@echo "  make clean                - 清理临时文件"
	@echo ""
	@echo "  == 测试 =="
	@echo "  make test                 - 运行后端测试套件"
	@echo ""
	@echo "  == Docker / 镜像 =="
	@echo "  make docker-build         - 构建镜像（自动先 build 前端）"
	@echo "  make docker-build-amd64   - 构建 amd64 镜像（buildx 跨平台，给 linux 部署）"
	@echo "  make docker-up            - 后台跑容器（docker-compose 全栈）"
	@echo "  make docker-stop          - 停容器"
	@echo "  make docker-logs          - 看实时日志"
	@echo "  make docker-ps            - 容器状态"
	@echo ""

# 安装所有依赖
install: venv frontend-deps
	@echo "✅ 所有依赖安装完成！"

# 创建 Python 虚拟环境
venv:
	@echo "🔧 创建 Python 虚拟环境..."
	python3 -m venv $(VENV)
	@echo "激活虚拟环境: source ${VENV}/bin/activate"
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt
	@echo "✅ 后端依赖安装完成！"

# 安装前端依赖
frontend-deps:
	@echo "📦 安装前端依赖..."
	cd frontend && $(NPM) install
	@echo "✅ 前端依赖安装完成！"

# 停止 FastAPI 后端
stop-api:
	@echo "⏸️  停止 FastAPI 后端服务..."
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || echo "✓ 端口 8000 未被占用"

# 启动 FastAPI 后端
run-api: stop-api
	@echo "🚀 启动 FastAPI 后端服务..."
	cd backend && $(PYTHON) -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --timeout-keep-alive 300 --http h11 --log-level info

# 启动 Vue 前端
run-front:
	@echo "🚀 启动 Vue 前端服务..."
	cd frontend && $(NPM) run dev

# 构建前端生产包
build:
	@echo "📦 构建前端生产包..."
	cd frontend && $(NPM) run build
	@echo "✅ 构建完成！输出目录: backend/app/public"

# 运行测试套件
test:
	@echo "🧪 运行后端单元测试..."
	cd backend && $(MAKE) test

# 清理临时文件
clean:
	@echo "🧹 清理临时文件..."
	rm -rf backend/__pycache__
	rm -rf backend/app/__pycache__
	rm -rf backend/.pytest_cache
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.vite
	@echo "✅ 清理完成！"

# ════════════════════════════════════════════════════════════════════
#  Docker / 部署 target
# ════════════════════════════════════════════════════════════════════

# 镜像构建：优先构建前端，再打 Docker
docker-build: build
	@echo "🐳 构建 amd64 镜像: $(DOCKER_IMAGE)"
	docker buildx build --platform $(DOCKER_AMD64_PLATFORM) -t $(DOCKER_IMAGE) --load .

docker-build-amd64: docker-build

docker-up:
	@echo "🚀 后台启动 docker-compose 全栈..."
	docker compose up -d

docker-stop:
	@echo "⏸️  停止 docker-compose..."
	docker compose stop

docker-logs:
	docker compose logs -f --tail=200

docker-ps:
	docker compose ps
