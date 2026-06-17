# AGENTS.md

> Monorepo 入口指南。AI agent 编辑代码前请先读对应子项目的 AGENTS.md。

## 仓库结构

```
.
├── backend/   # FastAPI 后端脚手架 → 详见 backend/AGENTS.md
├── frontend/  # 前端（Naivue UI）
└── hack/      # 工具脚本（含 codegen.py 代码生成器）
```

## ⚡ 开发提效工具

本项目提供了一键生成业务 CRUD 的代码生成器与前端配置化表格组件：

1. **业务 CRUD 一键生成 CLI**：
   运行 `hack/codegen.py` 可自动生成后端 Model、Service、Router，以及前端 API 交互与 UI 页面：
   ```bash
   python hack/codegen.py --name [模块小写名称] --title "[中文显示标题]" --fields "[字段1]:[类型]:[中文标签],..."
   ```
   * 示例：
     ```bash
     python hack/codegen.py --name product --title "产品管理" --fields "name:string:产品名称,price:float:产品单价,status:int:状态:0,description:text:描述"
     ```
   * 生成后：重启后台服务以自动建表，再运行 `node scripts/sync-menu.mjs` 同步菜单即可使用。

2. **前端通用表格组件 (ProTable)**：
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

