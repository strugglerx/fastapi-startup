# FastAPI + Vue3 Naive UI 管理后台脚手架 (smart-ai)

[English](./README.md) | **中文简体** | [更新日志](./CHANGELOG.md)

一款专为极速开发与 AI 辅助开发设计的企业级前后端分离管理后台脚手架。后端基于 **FastAPI**，前端基于 **Vue 3 + Naive UI + TailwindCSS**，开箱即用，代码精简规范，易于二次扩展。

---

## ⚡ 核心特性

### 1. ⚙️ 后端特性 (FastAPI)
- **高性能框架**：基于 **FastAPI 0.115**，原生支持异步协程，极致的响应速度。
- **智能表结构自动迁移**：无需手动编写复杂的 Alembic 迁移脚本。只需在 `models.py` 中定义或追加字段，应用启动时底层自动执行 `Base.metadata.create_all()` 并通过 `auto_migrate_columns` 差量追加新字段。
- **原子级接口限流 (Rate Limiter)**：内置基于 Redis 令牌桶算法的分布式限流拦截器，可针对单个接口进行细粒度调用限制。
- **全方位操作审计**：集成操作日志拦截中间件，自动拦截 `POST/PUT/PATCH/DELETE` 写入操作，**自动识别敏感字段并脱敏**。
- **IP 归属地双重缓存**：结合 L1 本地内存缓存与 L2 Redis 缓存，自动解析并缓存操作 IP 的地理位置。
- **双数据库灵活切**：开发环境默认自动使用 SQLite，生产环境无缝切换至 MySQL。

### 2. 🎨 前端特性 (Vue3 + Naive UI)
- **高阶 CRUD 提效组件 (ProTable)**：封装了极强表现力的 [ProTable](file:///Users/struggler/Documents/project/front-project/智慧幕墙/smart-ai/frontend/app/admin/components/ProTable.vue) 统一列表页面。仅需配置 JSON Schema，即可自动完成：**表格渲染、表单弹窗、分页切换、条件检索、多重按钮权限绑定**。
- **动态菜单与权限闭环**：
  - **页面访问隔离**：登录后动态请求 `/api/menu/list` 获取当前用户角色有权访问的菜单，前端据此**动态构建路由表**并挂载，无权限路径直接回退 404。
  - **按钮级控制**：全局封装 `v-auth` 自定义指令及 `hasPermission()` 方法，对未授权按钮进行无占位隐藏。
- **主题化系统与现代审美**：深度整合 Naive UI 的配置系统，全面兼容 Dark Mode（暗黑模式），配合 TailwindCSS 提供顺滑流畅的微交互动效。

### 3. 💼 开箱即用业务功能
- **账号管理**：支持管理员账号创建、禁用、重置密码及角色分配。
- **角色管理**：支持角色组定义与图形化菜单权限勾选授予。
- **菜单管理**：内置代码级路由声明同步机制（支持扫描 `page.js` 快速上报菜单至数据库）。
- **文件中心**：本地化静态文件服务，支持 **MD5 极速去重秒传**。
- **数据字典**：全动态多级联动数据字典配置。

---

## 📁 目录结构

```
.
├── backend/                    # 后端项目 (FastAPI)
│   ├── app/
│   │   ├── api/               # 路由层 (public 公开 / v1 业务接口)
│   │   │   └── v1/deps.py     # 共享依赖注入项 (JWT验证、权限、限流)
│   │   ├── boot/              # 应用工厂与生命周期插件加载
│   │   ├── core/              # JWT、Redis 连接池、限流、安全算法、队列任务
│   │   ├── db/                # 数据库模型 (models.py) 与数据库切换引擎
│   │   ├── middleware/        # 审计日志、访问拦截中间件
│   │   └── main.py            # 后端主入口
│   ├── .env                   # 本地环境变量配置
│   └── requirements.txt       # 后端依赖声明
│
├── frontend/                   # 前端项目 (Vue 3)
│   ├── app/
│   │   ├── admin/             # 管理员系统核心
│   │   │   ├── api/           # 请求封装与接口定义
│   │   │   ├── components/    # 通用组件 (ProTable.vue 核心位于此)
│   │   │   ├── router/        # 路由定义与动态路由加载
│   │   │   ├── stores/        # Pinia 状态管理
│   │   │   └── views/         # 页面视图 (dashboard/error/system等)
│   │   └── login/             # 独立登录页应用
│   ├── vite.config.js         # Vite 配置文件
│   └── tailwind.config.js     # Tailwind 样式配置
│
├── Makefile                   # 极速开发运维命令行助手
└── docker-compose.yml         # 生产一键打包容器编排
```

---

## 🚀 快速启动

### 方式一：使用 Makefile (强烈推荐)

系统根目录下准备了快捷 `Makefile` 命令：

```bash
# 1. 安装前后端所有依赖 (需提前准备 python3、pnpm)
make install

# 2. 启动 FastAPI 后端服务器 (默认占用 8000 端口，含自动热重载)
make run-api

# 3. 启动 Vue 前端服务 (在另一个终端中，默认占用 5173 端口)
make run-front
```

### 方式二：手动启动

#### 1. 启动后端 (Backend)
```bash
cd backend
# 创建并激活虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖项
pip install -r requirements.txt

# 复制并配置环境变量
cp .env.example .env

# 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

#### 2. 启动前端 (Frontend)
```bash
cd frontend
# 安装依赖
pnpm install

# 启动开发服务器
pnpm run dev
```

启动完成后：
- 后端 API 文档：[http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI) / [ReDoc](http://localhost:8000/redoc)
- 前端管理后台：[http://localhost:5173](http://localhost:5173)

---

## 📚 开发者指南 (HOW-TO)

### 1. 新增业务模块流程
要在系统里新增一个带有增删改查的业务页，只需遵循以下流程：

#### 第一步：设计数据库表 (backend)
在 [backend/app/db/models.py](file:///Users/struggler/Documents/project/front-project/智慧幕墙/smart-ai/backend/app/db/models.py) 中新增实体模型：
```python
class SysProduct(Base):
    __tablename__ = "sys_product"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False, comment="产品名称")
    price = Column(Numeric(10, 2), default=0.00, comment="单价")
    status = Column(Integer, default=1, comment="状态 1启用 0禁用")
```
> [!NOTE]
> 保存并重启后端，系统会自动识别该表并同步建表，无需编写 sql 或执行迁移命令。

#### 第二步：编写 CRUD API 接口 (backend)
在 `backend/app/api/v1/` 下新建对应路由文件（可挂载 `require_permission` 依赖）：
```python
from fastapi import APIRouter, Depends
from app.api.v1.deps import require_permission

router = APIRouter(prefix="/products", tags=["产品管理"])

@router.get("", dependencies=[Depends(require_permission("system:product:list"))])
async def list_products():
    ...
```

#### 第三步：在前端添加视图文件并定义 `page.js` (frontend)
在 `frontend/app/admin/views/` 下创建页面目录，并在此目录下声明一个 [page.js](file:///Users/struggler/Documents/project/front-project/智慧幕墙/smart-ai/frontend/app/admin/views/system/admin/page.js) 文件用于描述路由元数据：
```javascript
export default {
  title: '产品管理',
  icon: 'LayersOutline',
  order: 99,
  permissions: ['system:product:list', 'system:product:create', 'system:product:update', 'system:product:delete']
}
```

#### 第四步：同步菜单并分配权限 (管理后台)
1. 登录管理后台，进入 **「系统设置」** 页面。
2. 点击 **「一键同步菜单」**，前台会自动扫描所有的 `page.js` 页面并将新增菜单上传至数据库表 `sys_menu`。
3. 进入 **「角色管理」**，为您当前所属的角色勾选刚才新增的产品菜单及按钮权限。
4. 刷新页面，新菜单即会自动呈现在侧边栏中。

---

### 2. 使用 `ProTable` 极速完成列表页
在前端视图的 `index.vue` 中，可以直接引入 [ProTable](file:///Users/struggler/Documents/project/front-project/智慧幕墙/smart-ai/frontend/app/admin/components/ProTable.vue) 组件（高级功能配置参考 [ProTable 开发指南](file:///Users/struggler/Documents/project/front-project/智慧幕墙/smart-ai/docs/PROTABLE_GUIDE.md)），仅传入 schema 即可自动渲染完整的增删改查页：

```html
<template>
  <pro-table
    title="产品管理"
    api-path="/api/v1/products"
    permission-prefix="system:product"
    :columns="columns"
    :form-schema="formSchema"
  />
</template>

<script setup>
const columns = [
  { title: "产品名称", key: "name", search: true },
  { title: "产品价格", key: "price" },
  { title: "产品状态", key: "status", render: (row) => row.status === 1 ? '启用' : '禁用' }
]

const formSchema = {
  name: { label: "产品名称", type: "input", required: true },
  price: { label: "产品价格", type: "number", required: true },
  status: { label: "产品状态", type: "select", options: [{ label: "启用", value: 1 }, { label: "禁用", value: 0 }] }
}
</script>
```

---

## 🛡️ 开发规范与提交标准

项目遵循 Conventional Commits 提交规范，提交消息请严格符合以下格式：

```
feat: 新增产品批量导出功能
fix: 修复 uvicorn 启动时 python 3.9 环境下的类型注解报错
docs: 更新 README 文档有关 ProTable 的使用范例
```

---

## 📄 开源许可证
本项目采用 MIT 许可证开源。
