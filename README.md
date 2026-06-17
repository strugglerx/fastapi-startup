# FastAPI + Vue3 Naive UI Admin Management Scaffold (smart-ai)

**English** | [中文简体](./README_ZH.md) | [Changelog](./CHANGELOG.md)

An enterprise-grade monorepo admin management scaffold designed for extremely rapid development and AI-driven workflows. Powered by **FastAPI** on the backend and **Vue 3 + Naive UI + TailwindCSS** on the frontend, it is clean, highly extensible, and ready for production.

---

## ✨ Core Features

### 1. ⚙️ Backend Features (FastAPI)
- **High Performance** - Based on **FastAPI 0.115** with native async/await coroutine support.
- **Smart Schema Auto-Migration** - No need for manual Alembic migrations. Simply define or add fields to `models.py`, and the system automatically creates tables (`Base.metadata.create_all()`) and appends missing columns (`auto_migrate_columns`) on startup.
- **Granular Rate Limiting** - Distributed rate limiter middleware powered by Redis Token Bucket algorithm.
- **Full Action Audit Logging** - Automatic audit logging middleware for all mutative requests (`POST/PUT/PATCH/DELETE`), including **automatic masking of sensitive request body fields** (passwords, tokens, keys).
- **IP Geolocation Cache** - Dual-level IP lookup caching (L1 local memory + L2 Redis) to resolve client IP locations with zero database/external-service thrashing.
- **Dual Database Switch** - Seamlessly boots with SQLite in local development and switches to MySQL in production environments.

### 2. 🎨 Frontend Features (Vue3 + Naive UI)
- **High-Efficiency CRUD Component (ProTable)** - Declarative list wrapper [ProTable.vue](file:///Users/struggler/Documents/project/front-project/智慧幕墙/smart-ai/frontend/app/admin/components/ProTable.vue). Simply configure a JSON Schema to automatically render table grids, pagination, search forms, edit forms, modals, and dynamic action buttons.
- **Dynamic RBAC & Route Isolation**:
  - **Route Isolation** - Dynamically pulls authorized menus from `/api/menu/list` upon login, building the router tree on-the-fly. Unauthorized paths result in a 404 page.
  - **Button-level Control** - Custom `v-auth` directive and `hasPermission()` programmatic helper to show/hide UI components based on user privileges.
- **Design Aesthetic & Themes** - Custom theme configuration, built-in Dark Mode compatibility, styled with TailwindCSS, and decorated with micro-animations.

### 3. 💼 Out-of-the-Box Business Modules
- **Account Management** - Manage admin accounts, active states, password resets, and role assignments.
- **Role Permissions** - Create custom roles and allocate resource permissions via a visual tree checklist.
- **Menu Management** - Built-in code-driven route scanning (auto-syncs `page.js` view configurations to `sys_menu` database table).
- **File Center** - Local file upload server with MD5-hash deduplication (秒传 / instant upload bypass).
- **Data Dictionary** - Dynamic multi-level key-value dictionary system.

---

## 📁 Directory Structure

```
.
├── backend/                    # Backend directory (FastAPI)
│   ├── app/
│   │   ├── api/               # Router layer (public endpoints / v1 business routes)
│   │   │   └── v1/deps.py     # Shared dependency injections (JWT, Permission, Rate Limiting)
│   │   ├── boot/              # Application factories, configs, plugins
│   │   ├── core/              # JWT, Redis, Limiter, Security, Queues & Tasks
│   │   ├── db/                # Models (models.py) and database switching engine
│   │   ├── middleware/        # Audit logs, access intercepts
│   │   └── main.py            # App main entry point
│   ├── .env                   # Environment variables configuration
│   └── requirements.txt       # Python dependency list
│
├── frontend/                   # Frontend directory (Vue 3)
│   ├── app/
│   │   ├── admin/             # System admin app core
│   │   │   ├── api/           # Axios fetch helpers and route APIs
│   │   │   ├── components/    # Common components (ProTable.vue resides here)
│   │   │   ├── router/        # Dynamic router builders and guards
│   │   │   ├── stores/        # Pinia state stores
│   │   │   └── views/         # Layout views (dashboard, error, system, etc.)
│   │   └── login/             # Standalone login SPA application
│   ├── vite.config.js         # Vite configurations
│   └── tailwind.config.js     # Tailwind style declarations
│
├── Makefile                   # High-speed development command helpers
└── docker-compose.yml         # One-click Docker container builder
```

---

## 🚀 Quick Start

### Option 1: Using Makefile (Highly Recommended)

We provide a system root `Makefile` to quickly control both backend and frontend development tasks:

```bash
# 1. Install all dependencies (Backend pip dependencies + Frontend pnpm packages)
make install

# 2. Boot the FastAPI backend server (port 8000, handles auto-reloading)
make run-api

# 3. Boot the Vue 3 dev server (in another terminal, port 5173)
make run-front
```

### Option 2: Manual Start

#### 1. Setup Backend
```bash
cd backend
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Create config
cp .env.example .env

# Run server
uvicorn app.main:app --reload --port 8000
```

#### 2. Setup Frontend
```bash
cd frontend
# Install dependencies
pnpm install

# Run server
pnpm run dev
```

Endpoints after booting up:
- Backend Swagger API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Frontend Management Panel: [http://localhost:5173](http://localhost:5173)

---

## 📚 Developer HOW-TO Guide

### 1. Registering a New CRUD Page
To add a new business module with CRUD capabilities, follow these steps:

#### Step 1: Design Database Model (backend)
In [backend/app/db/models.py](file:///Users/struggler/Documents/project/front-project/智慧幕墙/smart-ai/backend/app/db/models.py), add your table schema:
```python
class SysProduct(Base):
    __tablename__ = "sys_product"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(64), nullable=False, comment="Product Name")
    price = Column(Numeric(10, 2), default=0.00, comment="Unit Price")
    status = Column(Integer, default=1, comment="State 1:active 0:disabled")
```
> [!NOTE]
> Save and restart the backend. The database will automatically register this table and alter any missing fields.

#### Step 2: Implement APIs (backend)
Create your route file under `backend/app/api/v1/` and apply permission deps:
```python
from fastapi import APIRouter, Depends
from app.api.v1.deps import require_permission

router = APIRouter(prefix="/products", tags=["Product Management"])

@router.get("", dependencies=[Depends(require_permission("system:product:list"))])
async def list_products():
    ...
```

#### Step 3: Add Vue View and a `page.js` Meta (frontend)
Create your view folder under `frontend/app/admin/views/` and add a [page.js](file:///Users/struggler/Documents/project/front-project/智慧幕墙/smart-ai/frontend/app/admin/views/system/admin/page.js) file detailing page metadata:
```javascript
export default {
  title: 'Product Management',
  icon: 'LayersOutline',
  order: 99,
  permissions: ['system:product:list', 'system:product:create', 'system:product:update', 'system:product:delete']
}
```

#### Step 4: Sync Menu & Grant Privileges (Admin Portal)
1. Go to the Admin Portal, open **"System Settings"** page.
2. Click **"Sync Menu Settings"**. The system will scan `page.js` declarations and sync them into the `sys_menu` table.
3. Open **"Role Management"** and assign these newly registered menu & action permissions to your active role.
4. Refresh the page to see the new menu in your sidebar.

---

### 2. Rapid Development with `ProTable`
With [ProTable](file:///Users/struggler/Documents/project/front-project/智慧幕墙/smart-ai/frontend/app/admin/components/ProTable.vue) (see [ProTable Development Guide](file:///Users/struggler/Documents/project/front-project/智慧幕墙/smart-ai/docs/PROTABLE_GUIDE.md) for advanced configurations), you can render a full CRUD page by simply providing columns and schema:

```html
<template>
  <pro-table
    title="Products"
    api-path="/api/v1/products"
    permission-prefix="system:product"
    :columns="columns"
    :form-schema="formSchema"
  />
</template>

<script setup>
const columns = [
  { title: "Product Name", key: "name", search: true },
  { title: "Price", key: "price" },
  { title: "Status", key: "status", render: (row) => row.status === 1 ? 'Active' : 'Disabled' }
]

const formSchema = {
  name: { label: "Product Name", type: "input", required: true },
  price: { label: "Price", type: "number", required: true },
  status: { label: "Status", type: "select", options: [{ label: "Active", value: 1 }, { label: "Disabled", value: 0 }] }
}
</script>
```

---

## 🛡️ Coding & Commit Guidelines

This repository follows Conventional Commits. Ensure all commits comply with this standard:

```
feat: add product batch export function
fix: resolve type hint TypeError under Python 3.9
docs: update readme guidelines on ProTable schema
```

---

## 📄 License
This project is open-sourced under the MIT License.
