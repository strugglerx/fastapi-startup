# RBAC 重设计 + 数据表清理 开发计划

> 跨 session 备忘。AI agent 接手前先读本文件 + `backend/CLAUDE.md`。
> 起点 commit：`fd0bbc7 refactor(rbac): merge /me/grants into /me/menus`（dev 分支）。
> 决策日期：2026-06-17。

## 背景：之前哪里"想错了"

一套"三真相源分离"的动态 RBAC 菜单系统：
- `frontend/app/admin/routes.js`（开发者）→ 只写路由存在性（path / `meta.code` / fallback 名·图标）
- `sys_resource`（admin）→ 菜单结构（name/icon/parent/order/visible）
- `role_resource`（admin）→ 哪个身份能看哪些 code

**症结**（导致反复修"无限重定向"）：
1. "admin 不被锁死"的兜底写了三遍：`ensure_seed_resources` 强制 visible + `ADMIN_WHITELIST_CODES` union 进 grants + `_sync_default_grants` 把所有资源写进 `role_resource(admin)`。三者干同一件事，且第三个会让 admin 的关联表持续漂移。
2. `min_role` 是死字段（注释自己说"只在 seed 用"）。
3. 白名单（profile / 系统菜单）硬编码在 service 常量里，不是数据驱动。
4. `grant_codes` 号称"含 invisible 子页"，其实只对 admin 成立（靠 auto-grant）。

## 已定方向（用户确认）

- **RBAC**：保留三表（sys_resource / sys_role / role_resource），只理顺语义。
- **清理范围**：删死表 + 历史冗余列。
- **UUID 方案：否决**。`code` 必须稳定可读（它是 routes.js↔DB 的 join key）；重复已被 `sync_from_client` 硬 reject。改进 = 把 `routes.js` 的 `_assertUniqueCodes` 从 console.error 升级为抛错。

## ⚠️ 重要修正（grep 实测）

"历史冗余列一起清"里，**Agent 的 ~20 个 Java 兼容列其实没死**——`agent_service.py` 的字段白名单 + providers(`coze_provider`/`factory`/`openai`) + `chat_service` 全程在用。删它 = 重构 Agent 功能，与 RBAC 无关、风险高。
- **本次不动 Agent 列**。要做另开独立任务。
- 真正能安全删的死东西：`AiTool` / `AgentTool`（后端零引用）、`SysUser.token`（未引用）、`SysResource.min_role`（RBAC 重设计顺手删）。

> 前提：本项目自动迁移**只加列不删列**。删 models.py 的类/列 = 仅代码层，**DB 既有表/数据不丢**，可逆。

## 核心设计：admin 真·绕过 + 白名单数据化

- **admin = god / bypass**：`get_my_grants(admin)` / `get_my_menu_tree(admin)` 直接取所有 `use_yn='Y'` 资源，**不查 role_resource、不 union 白名单**。→ 删 `_sync_default_grants`，admin 不再往 `role_resource` 堆行（旧行变惰性死行，无害）。
- **非 admin** = `role_resource(role)` ∪ `{public_grant=True 的 code}`。
- **白名单数据化**：`SysResource` 新增 `public_grant`（Boolean），`profile` seed 设 True，取代硬编码 `LOGIN_WHITELIST_CODES`。
- `ADMIN_WHITELIST_CODES` → 改名 `SYSTEM_MENU_CODES=("roles","admins","system")`，仅用于 seed 时"逃生菜单强制 visible"。
- `get_my_menu_tree` 的"带出父级 group"逻辑对所有身份生效（让被授权的子菜单也能挂到分组标题下）。

## 前端：显式"初始化菜单并同步"取代静默 auto-sync

- 删 `useAdminMenu._fetchAll` 里的 admin 静默 `resourceApi.sync(...)` 副作用。
- `useAdminMenu` 新增：`pendingSyncCodes`（admin 才算：discoverResources() 里不在 grants 的 code）、`initAndSync()`（sync→reload）。
- `App.vue`：admin 且 `pendingSyncCodes.length>0` 时，content 区上方挂 banner「检测到 N 个页面未纳入菜单 →〔初始化并同步〕」，点击 loading→成功后 banner 自动消失。
- `AdminSystemView` 的手动「同步路由清单」按钮保留（菜单编辑器入口）。
- 注意：新部署时 admin 至少能看到 seed 出来的「系统管理」分组（逃生入口永远在），不是全空。

## 执行清单（✅ 代码全部完成于 2026-06-17）

### Step 1 — backend/app/db/models.py
- [x] 删 `AiTool`、`AgentTool` 两个类
- [x] `SysUser` 删 `token` 列
- [x] `SysResource` 删 `min_role`，加 `public_grant = Column(Boolean, default=False)`

### Step 2 — backend/app/service/resource_service.py
- [x] 删 `VALID_ROLES`（死常量）
- [x] 删 `LOGIN_WHITELIST_CODES`；`ADMIN_WHITELIST_CODES`→`SYSTEM_MENU_CODES=("roles","admins","system")`
- [x] `_resource_to_dict`：去 `min_role`，加 `public_grant`
- [x] `ensure_seed_resources`：seed 加 profile.public_grant=True；逃生菜单 force-visible 用 `SYSTEM_MENU_CODES`；去 `min_role=`；删 `_sync_default_grants(db)` 调用
- [x] 新增 `_granted_codes(db, user)`：admin→全部 use_yn='Y'；其他→role_resource ∪ public_grant
- [x] `get_my_grants` / `get_my_menu_tree` 改用 `_granted_codes`；去白名单 union；新增 `_build_menu_tree` 共用，group 带出对所有身份生效
- [x] 删 `_sync_default_grants` 方法
- [x] `sync_from_client`：去 `min_role=`；修 docstring（visible 实际语义）
- [x] `create_resource` / `update_resource`：去 min_role（update 改授 `public_grant`）

### Step 3 — backend/app/api/v1/resource.py
- [x] `CreateResourceReq` / `UpdateResourceReq` 去 `min_role`，改 `public_grant`

### Step 4 — 前端
- [x] `useAdminMenu.js`：删静默 auto-sync；加 `pendingSyncCodes` + `initAndSync`
- [x] `App.vue`：加初始化 banner（amber 提示条 + 「初始化并同步」按钮）
- [x] `routes.js`：`_assertUniqueCodes` 改抛错（用户已自行改）

### Step 5 — 验证
- [x] 后端 SQLite import 冒烟：public_grant 在 / min_role 去 / AiTool·AgentTool·SysUser.token 去 / `_granted_codes`·`_build_menu_tree` 在
- [x] `py_compile` 三个后端文件 + grep 全仓库无残留引用
- [x] 前端 `@vue/compiler-sfc` 编译 App.vue + babelParse 三个 JS 文件，全过
- [ ] **运行时未验证（需起前后端实际登录）**：admin 视角 grants=全集 + 新部署见「系统管理」+ banner；member 视角只见授权菜单 + profile、进未授权子页被弹 /profile 不死循环

## 暂不做 / 待办
- Agent ~20 个 Java 兼容列的精简（需重构 agent_service + providers，独立任务）
- 子页授权"继承父菜单"（②，看是否需要细粒度再定）
- action（按钮级）权限
- sync 架构层改造（构建期生成 JSON / 启动读），现仅靠 admin 浏览器 push
