# Changelog

本项目所有显著变更记录于此。

格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

---

## [Unreleased]

### 安全

- **审计日志脱敏**（关键修复）：之前 `audit_log` 中间件直接把请求体原文写入 `sys_audit_log.request_body`，导致 `/auth/login`、`/me/password`、`/auth/forgot-password` 等接口的密码 / 验证码 / token **明文落库**。
  - `middleware/audit_log.py` 新增 `scrub_request_body()`：JSON body 递归 mask `password / passwd / pwd / old_password / new_password / token / access_token / refresh_token / secret / code / authorization` 等键；非 JSON body 命中敏感路径直接 `[REDACTED]`；其他原文截断到 4000。
  - 启动时一次性 `AuditService.scrub_history()` 对历史 `request_body` 跑同样的脱敏；Redis 标记 `audit_scrub_done` 30 天，重启不会重复跑。

### UI 改进

- **菜单管理按钮 pill 可点击性增强**：橙色按钮 pill 加 hover 高亮 + cursor:pointer + title 提示"点击编辑按钮权限"，避免用户误以为按钮节点不能在 UI 里配置。

### 新增

- **菜单字段 `admin_sidebar_hidden`**：替代之前在 guards.js 里硬编码的 `ADMIN_ONLY_PATHS`，让"哪些菜单不出现在 admin 侧栏"由数据决定：
  - `sys_menu` 新增 `admin_sidebar_hidden` 列（auto-migrate）；`/api/menu/sync` / `POST /api/menu/` / `PATCH /api/menu/{menu_key}` / `PUT /api/menu/{id}` 均接受 `adminSidebarHidden` 字段
  - 菜单管理 UI 增加"管理员侧栏隐藏"开关
  - 仅控制侧栏显隐，**不**拦截 URL 访问与角色授权（管理员仍可直接通过 URL 进入）
- **管理员调试开关：显示全部菜单**：admin 头像下拉新增「调试：显示全部菜单」选项，开启后忽略所有 `adminSidebarHidden` 标记；写入 `sessionStorage`，关闭浏览器或刷新会话即恢复。开发阶段无需反复改菜单配置。
- **`guards.js` 简化**：删除 `ADMIN_ONLY_PATHS` 硬编码；路由访问完全由 SysRoleMenu 授权决定（未授权 → 路由未注册 → 自然 404）。

### 配置

- **品牌名统一由 env 驱动**：
  - 后端 `APP_NAME`（`AppConfig.name`，默认 `智慧AI 探索平台`）— 密码重置邮件主题/落款读取；启动日志打印 `应用名: ...`。
  - 前端 `VITE_APP_NAME`（`frontend/.env.example`，默认同上）— 浏览器 tab title（admin + login）、登录页品牌名 / 登录标题、admin 侧栏品牌名、dashboard 欢迎横幅全部读取。
  - 共享读取点：`frontend/app/shared/app-meta.js` 暴露 `APP_NAME` 常量供两个入口复用；`vite.config.js` 用 `loadEnv` 注入 MPA 标题。

### 安全

- **密码强度策略**：`app/core/security.py:validate_password_strength` —— 长度 8-128、至少含 1 字母+1 数字、不允许全相同字符。接入 `change_password` / `reset_password` / `create_admin` / `register`。
- **找回密码（邮箱验证码流）**：
  - 新增 `POST /api/v1/auth/forgot-password` 与 `POST /api/v1/auth/reset-password`，6 位数字验证码 / 10 分钟有效 / 一次性 / 1 分钟内同邮箱仅 1 次。
  - 新增 `MailConfig`（环境变量 `SMTP_HOST` / `SMTP_PORT` / `SMTP_USERNAME` / `SMTP_PASSWORD` / `SMTP_SENDER` / `SMTP_USE_TLS` / `SMTP_USE_SSL`）与 `app/core/mailer.py`。
  - SMTP 未配置时所有依赖邮件的接口返回 HTTP 503 + `code=10030` 友好提示"邮件服务暂未开通"。
  - 登录页（`LoginCard.vue`）"忘记密码"链接改为真正的两步重置流程（发码 / 输码 + 新密码）。
- **Token 静默续期**：
  - 后端新增 `POST /api/v1/auth/refresh`（需登录，限流 30/60s）。
  - 前端 `api/token-refresh.js`：解 JWT `exp`，在剩余 ≤ 10 分钟时主动续期，并发请求共用同一 Promise；接入 `fetch.js` request 拦截器；refresh 接口本身跳过避免递归。
- **限流降级日志**：`RateLimiter` 在 Redis 故障时输出结构化日志（`rate_limiter.degraded limiter=... path=... method=... identifier=... reason=...`），便于监控告警提取。
- **登录失败账号锁定**：连续 5 次失败（10 分钟窗口）锁定账号 15 分钟，返回 429；Redis 不可用时降级到不锁定。实现位于 `app/service/user_service.py`（`_check_login_lock` / `_record_login_fail` / `_clear_login_fail`）。
- **敏感写接口限流**：
  - `PUT /api/v1/me/password` → 5 次 / 60 秒
  - `POST /api/v1/admins/{id}/reset-password` → 10 次 / 60 秒
  - `DELETE /api/v1/admins/{id}` → 20 次 / 60 秒
  - `PUT /api/menu/role-grants` → 30 次 / 60 秒
- **dashboard admin-only 守卫**：`frontend/app/admin/router/guards.js` 新增 `ADMIN_ONLY_PATHS`，非 admin 直接访问 `/dashboard` 时自动跳到其第一个授权菜单；根入口 `/` / `/404` 也跳第一个授权菜单（admin 第一项通常仍是 dashboard）。

### 新增

- **菜单组织 UI 化**：
  - 后端：`sys_menu` 新增 `source` 字段；`POST /api/menu/sync` 收紧为只同步 `menuKey/path/component/cacheable`；新增 `PATCH /api/menu/{menu_key}`、`POST /api/menu/groups`、`DELETE /api/menu/{menu_key}`；启动期把既有 `component="__group__"` 菜单迁为 `source="ui"`
  - 前端：`definePage()` 禁止在 `page.js` 写 `title/icon/parentKey/sort/hidden`；清理现有 page.js；系统设置新增“菜单管理”UI，支持分组创建、运维字段编辑、拖拽调整父级/排序、删除 UI 分组
  - 图标：引入 `@vicons/lucide`，新增 `shared/icon-library.js` 与 `IconPicker.vue`，侧栏/页签改为 Vue 组件图标渲染，移除旧 `icon-registry.js`
  - 文档：`docs/admin-platform-mvp.md` 新增 ADR-011，明确所有非代码可推导字段均由 UI 维护
- 重建 `sys_role` 表，恢复 UI 可配置角色（推翻 ADR-009 轻量 RBAC）
- 新增 系统设置页 + 同步菜单按钮
- 账号管理：搜索 / 角色筛选 / 状态筛选 / 行内启停 / 编辑账号 / 最后登录列
- `User.last_login_at` 字段（自动 ALTER）
- UI 文案：「软删除」 → 「删除」
- **轻量角色-菜单关联**：
  - 后端：新增 `sys_role_menu` 表；`GET /api/menu/list` 按当前用户 `role` 过滤菜单；新增 `GET /api/menu/role-grants` 与 `PUT /api/menu/role-grants` 授权 API；账号 `PUT /api/v1/admins/{id}` 继续支持 role 编辑
  - 前端：角色管理页改为 admin/member 菜单树授权；账号管理页新增"改角色"操作；删除 `system/user` 重复占位页面
  - 文档：`docs/admin-platform-mvp.md` 补充轻量 RBAC DDL、API 契约与 ADR-009
- **Admin Platform MVP 架构**（`docs/admin-platform-mvp.md` v1.1）：代码优先 + 动态菜单 + 动态路由
  - 后端：新增 `sys_menu` 表 + `GET /api/menu/list` + `POST /api/menu/sync`（`backend/app/db/models.py` `SysMenu`、`backend/app/service/menu_service.py`、`backend/app/api/menu.py`）；旧 `sys_resource` RBAC 已整套移除（见「移除」）
  - 前端：`frontend/app/admin/` 子应用按文档全量重写
    - `shared/define-page.js`：`PageMeta` JSDoc + `definePage()`，页面元数据唯一真实源
    - `router/`：`constant-routes.js` / `guards.js` / `dynamic.js` / `index.js`，动态 `addRoute` + KeepAlive 包名
    - `stores/`：`menu.js`（模块级 `ref` 单例 + composable，建树 + `_loading` 去重）、`keep-alive.js`、`user.js`
    - `components/Layout/`：naive-ui 主布局 + Sidebar
    - `views/`：dashboard / system/user / system/role / profile / error/404 示例页 + `page.js`
  - 同步脚本：`frontend/scripts/sync-menu.mjs` —— 扫描 `views/**/page.js`、校验 `menuKey` 冲突 / `path` / 父子 / `component` 文件存在性，节点直跑（`#/admin/...` 别名经 `data:` URL 改写）
  - `frontend/package.json`：新增 `sync:menu` 脚本与 `globby` devDependency（用户执行 `pnpm install` 后可用）

### 移除

- 旧 `frontend/app/admin/routes.js`、`router.js`、`composables/useAdminMenu.js`：被新的 `router/` 与 `stores/menu.js` 取代
- 旧 `frontend/app/admin/views/Admin*View.vue` / `_PlaceholderView.vue`：内容迁到新 `views/<module>/<sub>/index.vue` 形态
- **整套旧 RBAC 拔除（彻底白纸，身份只留硬编码 admin|member）**：
  - 数据模型：删 `SysResource` / `SysRole` / `RoleResource` 三表（远端 `smart_ai_v2` 对应表已 `DROP`，行数据备份在 `/tmp`）
  - 后端：删 `resource_service.py` / `role_service.py`、`api/v1/resource.py` / `role.py`、`/me/menus` / `/me/grants` 端点、启动期 `ensure_seed_resources` / `ensure_seed_roles` 种子
  - `user_service`：角色校验由查 `sys_role` 改为硬编码 `ALLOWED_ROLES=("admin","member")`；鉴权本就只看 `user.role` 字符串，未受影响
  - 前端：删 `api/resource.js` / `api/role.js`、孤儿组件 `AccountTable.vue`，清理 `api/index.js` 导出
  - 保留模型：`User` / `AccessKey` / `SysMenu`

- **权限管理页面**（`AdminAuthorityView.vue`）：
  - 资源管理：支持查看、创建、编辑、删除菜单/页面/操作资源
  - 角色授权：支持为 admin/member 角色分配资源权限（树形勾选）
- **API 层重构**（`frontend/app/admin/api/`）：
  - 新增 `auth.js`、`admin.js`、`chat.js`、`provider.js`、`sys-user.js`、`resource.js`、`base.js`、`feedback.js` 等模块
  - 统一错误处理：拦截器自动处理 401 跳登录、业务码非 0 弹错
  - 修复响应拦截器逻辑：后端返回 HTTP 状态码作为 code，前端改为只检查 `code: 0` 为成功

### 修复

- **响应拦截器误判**：前端错误地认为 `code: 200` 也是成功，导致所有非 200 响应被当作错误处理
- **重复导入**：`AdminProvidersView.vue` 中 `notifySuccess` 重复导入

### 移除

- **整条 AI Agent / C 端栈下线** —— 项目收敛为「纯后台管理（账号 + RBAC）」：
  - 数据模型：删 `Agent` / `AiProvider` / `AiConversation` / `AiMessage` / `SysUser` 五张表（仅代码层，自动迁移不删 DB 既有表/数据，可逆）
  - 后端：删 `agent_service` / `chat_service` / `conversation_service` / `provider_service` / `sys_user_service` 及对应 `api/v1` 路由；删 `core/providers/`（openai / coze / dify / factory）
  - 前端：删 `AdminAgentsView` / `AdminConversationsView` / `AdminProvidersView` / `AdminToolsView` / `AdminUsersView` 视图、`AgentChatTest` 组件、`agent/chat/conversation/provider/sys-user` api 客户端及对应路由
  - 保留：`User`（后台账号）/ `AccessKey` / `SysResource` / `SysRole` / `RoleResource`
- **后台菜单推到「准白纸」（为重新设计让路）** —— `ensure_seed_resources` 种子从 `g_settings/roles/admins/system/profile` 缩到只剩 `system`（菜单编辑器逃生入口，改为顶级）+ `profile`（永远可达）：
  - `SYSTEM_MENU_CODES` 缩为 `("system",)`；`routes.js` 仅留 `system` + `profile`
  - 落地/affix 锚点从 `dashboard` 迁到 `system`（`router.js` 跳转、`index.html` 重定向、`App.vue` `AFFIX_KEY`）
  - 远端 `sys_resource` 清掉 `g_settings/roles/admins/dashboard` 死行（备份在 `/tmp`），现存 `system` + `profile`
  - `AdminDashboardView` / `AdminAuthorityView`（roles）/ `AdminAdminsView`（admins）视图文件暂留磁盘但已不可达，待重设计时复用或删除；后端 `role` / `admin` API 仍在

---

## [1.1.0] — 2026-06-16

围绕"AI 驱动开发"做了一轮系统性升级：引入分层架构、现代化基础设施、补齐测试与文档。

### 新增

- **`app/service/` 业务逻辑层** —— 路由保持薄 Controller，事务/规则/外部调用统一沉淀到 service。
  - 示例实现：`UserService`（注册 / 登录 / 列表 / 删除）+ 配套薄路由 `api/v1/user.py`
- **`backend/CLAUDE.md`** —— AI Agent 工作手册：三层职责约束、添加接口流程、常见陷阱、配置项速查表
- **`CLAUDE.md`**（仓库根）—— Monorepo 入口指南
- **`schema/base.py`** —— 泛型 `BaseResponse[T]`，统一响应模型基类
- **`boot/openapi.py`** —— 通过 lazy override 注入 `x-tagGroups` 文档分组
- **`pyproject.toml`** —— pytest + ruff 配置（py39 目标，line-length 120）
- **测试套件扩展** 4 → 27 个：
  - `test_jwt.py` —— 签名/篡改/过期/格式校验
  - `test_security.py` —— bcrypt 哈希/校验/盐随机性
  - `test_errors.py` —— 404 / 405 / 响应包装防重 / 健康检查公开
  - `test_user_service.py` —— Service 层全覆盖（业务码断言）
  - `conftest.py` —— 共享 `TestClient` fixture

### 变更

- **`APP_USE_SQLITE=true` 才走 SQLite**，默认连 MySQL（之前是开发自动 SQLite / 生产 MySQL）
- **响应包装成功 code 改为 `0`**（之前是 `200`），与前端常见约定对齐
- **HTTP 状态码 + body code 分工明确**：
  - `APIException` 业务异常 → HTTP **永远 200**，body code 表达任意业务码（401/403/422/10001…）
  - `StarletteHTTPException`（路由不存在/方法错误）→ 保留真实 HTTP 状态码（404/405），方便 CDN/k8s/监控识别
- **`boot/middleware.py` → `boot/plugins.py`** —— 与 `app/middleware/`（业务中间件）命名解耦
- **生命周期切换为 `lifespan`** —— 替换所有过时的 `@app.on_event("startup")` 钩子
- **CORS 升级**：支持 `*` 通配 + 子域名正则 + 凭证模式；挂载为最外层中间件
- **`app/middleware/access_log.py`** —— 业务访问日志从 `__init__.py` 拆分到独立文件，并跳过 `/docs`、`/health` 等噪音路径
- **`db/models.py` 升级到 SQLAlchemy 2.0 `DeclarativeBase`** —— 消除启动 `MovedIn20Warning`
- **`hashed_password` 字段长度 60 → 128**（适配 bcrypt 输出 + 余量）
- **MySQL `auto_migrate_columns` 加强**：
  - 通过 `TypeDecorator.load_dialect_impl` 识别 `MEDIUMTEXT/LONGTEXT` 等扩展类型
  - 新增 `normalize_mysql_type` —— 忽略 `CHARACTER SET / UNSIGNED / 显示宽度` 等无意义差异，避免假性 `MODIFY`
  - 主键字段跳过类型修改（风险高）
- **`config.py` 瘦身** 220 行 → 100 行：7 个重复 `try/except` 块改为 `Field(default_factory)`；配置加载失败时全局兜底；启动概览改用 `logger` 输出
- **`api/v1/hello.py`** 升级到 Pydantic 响应模型（OpenAPI 文档更完整）
- **`schema/admin.py`** 加字段长度约束 + 清理噪音注释
- **`schema/token.py`** `exp/iat` 类型由 `datetime` 修正为 `int` Unix 时间戳（与 JWT 实际负载一致）
- **`requirements.txt`** —— 移除未使用的 `toml`、`asgiref`；新增 `httpx`、`orjson`
- **README.md / README_ZH.md** 同步本次架构变更（响应格式、目录结构、限流用法、Redis 用法、DB 切换逻辑）

### 修复

- **JWT `datetime.utcnow()` 弃用警告** —— 全面切换到 `datetime.now(timezone.utc)`（Python 3.12 兼容）
- **`verify_token` / `decode_token` 代码重复** —— 合并为单一 `_decode(verify_exp=...)` 私有函数
- **限流器模块顶层实例化导致 import 链崩溃** —— Redis 未启动也能 import；改为 `get_rate_limiter()` 懒加载单例
- **响应包装中间件丢失 headers** —— `JSONResponse` / `StreamingResponse` 重建时正确保留原始响应头（剔除 `content-length`、`content-type` 由框架重算）
- **`is_wrapped_response` 误判**：之前只检查 `code` 字段，业务字段名为 `code` 时会跳过包装。现要求同时包含 `code` + (`data` 或 `msg`)
- **健康检查 `/api/health` 之前 `allow_local_only` 导致负载均衡器探活 403** —— 现已改为公开
- **SQLite `init_sample_data` 重启时重复插入种子数据** —— 补充存在性检查

### 安全

- **密码哈希 MD5 → bcrypt**（直接使用 `bcrypt` 库，避开 passlib 1.7.4 与 bcrypt 5.x 的兼容问题）
- **JWT 默认密钥提示**：生产环境用默认密钥时打 warning（不阻断启动，遵循"配置缺失不影响启动"原则）

### 移除

- `boot/middleware.py`（已拆分到 `boot/plugins.py`）
- `app/library/queue/`（空骨架，待真实队列实现时再加回）

---

## [1.0.0] — 2026-01-06

首版发布。

### 新增

- FastAPI 0.115 + Uvicorn 启动框架
- JWT 鉴权（HMAC-SHA256 自实现）
- AccessKey + IP 限流（Redis Lua 原子脚本）
- Redis 连接池（同步 + 异步 + PubSub）
- MySQL / SQLite 双引擎自动切换
- 模型字段变更自动 `ALTER TABLE` 迁移
- 统一响应包装中间件 `{code, data}`
- 自动文档：Swagger UI / RapiDoc / OpenAPI JSON
- Docker + docker-compose + Makefile 一键启动
- 彩色日志 + 文件轮转
