.PHONY: help install venv frontend-deps run-api stop-api run-front clean build test

help: ## 显示帮助信息
	@echo "可用命令:"
	@echo "  make install         - 安装所有依赖（后端+前端）"
	@echo "  make venv            - 创建 Python 虚拟环境"
	@echo "  make frontend-deps    - 安装前端依赖（如果存在 frontend 目录）"
	@echo "  make run-api         - 启动 FastAPI 后端"
	@echo "  make stop-api        - 停止 FastAPI 后端"
	@echo "  make run-front        - 启动前端服务（如果存在）"
	@echo "  make clean           - 清理临时文件"
	@echo "  make build           - 构建前端生产包"
	@echo "  make test            - 运行测试"
	@echo "  make docs            - 生成 API 文档"
	@echo "  make format          - 格式化代码"

install: ## 安装所有依赖
	@echo "安装后端依赖..."
	pip3 install -r requirements.txt
	@if [ -d "frontend" ]; then \
		echo "安装前端依赖..."; \
		cd frontend && pnpm install; \
	fi

venv: ## 创建 Python 虚拟环境
	@echo "创建虚拟环境..."
	python3 -m venv venv
	@echo "激活虚拟环境: source venv/bin/activate"

frontend-deps: ## 安装前端依赖
	@if [ -d "frontend" ]; then \
		cd frontend && pnpm install; \
	else \
		echo "错误: frontend 目录不存在"; \
	fi

run-api: ## 启动 FastAPI 后端
	@echo "停止已运行的服务..."
	lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@echo "启动 FastAPI 后端..."
	cd app && APP_ENV=development uvicorn main:app --host 0.0.0.0 --port 8000 --reload

stop-api: ## 停止 FastAPI 后端
	@echo "停止 FastAPI 后端..."
	lsof -ti:8000 | xargs kill -9 2>/dev/null || true

run-front: ## 启动前端服务
	@if [ -d "frontend" ]; then \
		cd frontend && pnpm dev; \
	else \
		echo "错误: frontend 目录不存在"; \
	fi

clean: ## 清理临时文件
	@echo "清理 Python 缓存..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "清理日志..."
	rm -rf logs/*.log 2>/dev/null || true
	@echo "清理数据库文件..."
	rm -f *.db *.sqlite *.sqlite3 2>/dev/null || true
	@echo "清理完成！"

build: ## 构建前端生产包
	@if [ -d "frontend" ]; then \
		echo "构建前端..."; \
		cd frontend && pnpm build; \
	else \
		echo "错误: frontend 目录不存在"; \
	fi

test: ## 运行测试
	@echo "运行测试..."
	@if [ -d "tests" ]; then \
		pytest -v; \
	else \
		echo "警告: tests 目录不存在，请先创建测试文件"; \
	fi

format: ## 格式化代码
	@echo "格式化代码..."
	@command -v black >/dev/null 2>&1 && black app/ || echo "black 未安装"
	@command -v isort >/dev/null 2>&1 && isort app/ || echo "isort 未安装"

docs: ## 生成 API 文档
	@echo "API 文档地址: http://localhost:8000/docs"

lint: ## 代码检查
	@echo "运行代码检查..."
	@command -v flake8 >/dev/null 2>&1 && flake8 app/ || echo "flake8 未安装"
	@command -v mypy >/dev/null 2>&1 && mypy app/ || echo "mypy 未安装"
