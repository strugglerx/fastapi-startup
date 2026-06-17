# AGENTS.md

> Monorepo 入口指南。AI agent 编辑代码前请先读对应子项目的 AGENTS.md。

## 仓库结构

```
.
├── backend/   # FastAPI 后端脚手架 → 详见 backend/AGENTS.md
└── frontend/  # 前端（Naive UI） → 详见 frontend/AGENTS.md
```

## ⚡ 开发提效工具

**前端通用表格组件 (ProTable)**：
前端所有标准的列表 CRUD 建议使用 `frontend/app/admin/components/ProTable.vue`，只需配置 schema 即可自动渲染搜索栏、表格、分页以及增删改查弹窗表单。

## 开发约定

- **任何 backend 改动前必读** `backend/AGENTS.md`，里面有目录结构、新增接口流程、配置项、常见陷阱。
- **不要破坏 `.env` 加载逻辑**：缺配置回落默认值，永远不阻断启动。
- **不要写数据库迁移脚本**：本项目用 `models.py` + 启动时自动 `ALTER TABLE`。
- **响应格式由中间件统一包装**：路由函数直接返回 dict / Pydantic 模型，勿手写 `{"code": 0, ...}`。

## 快速启动

```bash
# 方式一：Docker 一键部署运行整个技术栈（含 MySQL + Redis + 编译后的前端 + 后端）
docker-compose up -d --build

# 方式二：本地 Makefile 启动
cd backend
make install     # 装依赖
make run-api     # 启动后端（默认 8000）
make test        # 跑测试
```

