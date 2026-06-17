# Frontend Agent Guide (frontend/AGENTS.md)

欢迎开发 Vue3 + Naive UI 前端管理后台。编辑代码前请务必阅读本指南，遵循相关约定。

## 🔐 按钮级权限控制与授权

本脚手架支持接口级与前端按钮级的细粒度权限校验。

### 1. 使用 `v-auth` 指令（推荐）
在 Vue 模板中，你可以对需要受控的按钮或组件使用全局注册的自定义指令 `v-auth`。
如果当前登录用户没有相应的权限编码，该 DOM 元素将**被自动移除（不占位）**。

* **使用示例**：
  ```html
  <!-- 仅拥有账号创建权限的用户才能看见此按钮 -->
  <n-button v-auth="'system:admin:create'" type="primary">
    新建账号
  </n-button>
  ```
  *(注：指令接收的参数是字符串，包裹在双引号内的单引号中)*

---

### 2. 使用 `hasPermission` 编程式校验
如果需要在 JS 逻辑中或者 `v-if` 条件中动态判断权限，可以导入 `hasPermission` 工具函数。

* **使用示例**：
  ```javascript
  import { hasPermission } from '#/admin/shared/auth.js'

  // 在模板或者 JS 逻辑中使用
  if (hasPermission('system:role:update')) {
    // 执行编辑逻辑
  }
  ```

---

### 3. 页面权限与动态路由说明
- 页面级别的访问权限是**天然隔离**的。
- 登录成功后，前端会通过 `/api/menu/list` 获取当前用户角色所拥有的**启用菜单列表**，并通过 [router/dynamic.js](file:///Users/struggler/Documents/project/front-project/智慧幕墙/smart-ai/frontend/app/admin/router/dynamic.js) 进行**动态注册**。
- 如果用户没有某菜单的权限，该路由将不会被加入 Vue Router 中，用户手动在浏览器输入 URL 会直接导航至 **404 页面**。

---

## 🎨 通用 CRUD 提效组件 (ProTable)

为了减少增删改查页面的重复代码，前端统一封装了 [ProTable.vue](file:///Users/struggler/Documents/project/front-project/智慧幕墙/smart-ai/frontend/app/admin/components/ProTable.vue)。

### ProTable 功能点：
1. **自动挂载权限**：
   通过配置 `permission-prefix="system:product"`，组件内的编辑按钮会自动绑定 `v-auth="'system:product:update'"`，删除按钮自动绑定 `v-auth="'system:product:delete'"`，新建按钮自动绑定 `v-auth="'system:product:create'"`。
2. **状态自动化**：
   无需手动维护搜索表单对象、分页属性、加载状态、弹框状态以及 API 请求，只需声明 JSON Schema 即可渲染完整页面（见 [product/index.vue](file:///Users/struggler/Documents/project/front-project/智慧幕墙/smart-ai/frontend/app/admin/views/system/product/index.vue) 实例）。
