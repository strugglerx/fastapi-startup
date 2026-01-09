# 项目启动工具
.PHONY: install venv frontend-deps run run-api stop-api run-front build clean help

# 可选包含腾讯云配置（如果存在）
-include ./hack/tencent.mk

# 配置
PROJECT_ROOT := $(shell pwd)
VENV := $(PROJECT_ROOT)/backend/venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
NPM = pnpm

# 默认目标
.DEFAULT_GOAL := help

help:
	@echo "📋 可用命令:"
	@echo ""
	@echo "  make install      - 安装所有依赖（后端 + 前端）"
	@echo "  make venv         - 创建 Python 虚拟环境并安装后端依赖"
	@echo "  make frontend-deps - 安装前端依赖"
	@echo ""
	@echo "  make run-api      - 启动 FastAPI 后端服务（自动清理端口）"
	@echo "  make stop-api     - 停止 FastAPI 后端服务"
	@echo "  make run-front    - 启动 Vue 前端服务"
	@echo "  make build        - 构建前端生产包"
	@echo ""
	@echo "  make clean        - 清理临时文件"
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

# 清理临时文件
clean:
	@echo "🧹 清理临时文件..."
	rm -rf backend/__pycache__
	rm -rf backend/app/__pycache__
	rm -rf backend/.pytest_cache
	rm -rf frontend/dist
	rm -rf frontend/node_modules/.vite
	@echo "✅ 清理完成！"
