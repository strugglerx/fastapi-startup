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
- 登录成功后，前端会通过 `/api/v1/menu/list` 获取当前用户角色所拥有的**启用菜单列表**，并通过 `router/dynamic.js` 进行**动态注册**。
- 如果用户没有某菜单的权限，该路由将不会被加入 Vue Router 中，用户手动在浏览器输入 URL 会直接导航至 **404 页面**。
- 目录命名约定：`_` 开头的目录为私有组件（如 `_shared`），大写 PascalCase 文件为页面级子组件，不作为独立路由自动注册。

---

## 🎨 通用 CRUD 提效组件 (ProTable)

为了减少增删改查页面的重复代码，前端统一封装了 `frontend/app/admin/components/ProTable.vue`。

### ProTable 功能点：
1. **自动挂载权限**：
   通过配置 `permission-prefix="system:product"`，组件内的编辑按钮会自动绑定 `v-auth="'system:product:update'"`，删除按钮自动绑定 `v-auth="'system:product:delete'"`，新建按钮自动绑定 `v-auth="'system:product:create'"`。
2. **弹窗与抽屉双模式**：
   支持 `form-type="modal"` 与 `form-type="drawer"`，大表单右侧 Drawer 打开，体验更自然。
3. **字段 Tab 分组**：
   表单字段配置 `tab: "基础信息"` / `tab: "扩展配置"` 即可自动在弹窗中渲染 Tab 切换，告别超长表单。
4. **多样化搜索与联动**：
   支持 `input`、`number`、`select`、`daterange`（自动映射 `startKey`/`endKey`）等搜索字段。
5. **动态行权限与操作控制**：
   支持 `canEdit`, `shouldShowEdit`, `canDelete`, `shouldShowDelete` 函数，根据行状态精确控制操作按钮显示与禁用。

---

## ⚠️ Naive UI Modal 布局陷阱（`preset="card"`）

不是组件 bug，是**默认行为**：内容超长时，整个弹窗（含 header / footer）一起滚出视口，底部「保存 / 取消」会看不见。

### 两种场景，两种做法

| 场景 | 做法 |
|------|------|
| 简单表单，整块内容滚动即可 | 开 `content-scrollable` + 给 Modal 设固定高度 |
| **左右分栏 / 多区域各自滚动** | **不要**开 `content-scrollable`；Modal 固定高度 + 内部 flex 分栏各自 `overflow-y: auto` |

`content-scrollable` 会把**整块 card 内容**包进一个滚动容器，左右栏无法各自 `height: 100%` 独立滚动，左栏配置会被一起滚走。

### 推荐写法（复杂弹窗 + 固定 footer）

```vue
<NModal
  preset="card"
  class="my-modal"
  :segmented="{ content: true, footer: true }"
  :style="{ width: 'min(900px, calc(100vw - 32px))', height: 'min(800px, 85vh)' }"
>
  <div class="my-dialog">…</div>
  <template #footer>…</template>
</NModal>
```

```css
/* class 加在 NModal 上，会落到 .n-card 根节点 */
:global(.my-modal) {
  display: flex !important;
  flex-direction: column !important;
  height: min(800px, 85vh) !important;
  max-height: min(800px, 85vh) !important;
  overflow: hidden !important;
}
:global(.my-modal > .n-card-header),
:global(.my-modal > .n-card__footer) {
  flex-shrink: 0 !important;
}
:global(.my-modal > .n-card-content) {
  flex: 1 !important;
  min-height: 0 !important;      /* flex 子项 overflow 生效的关键 */
  overflow: hidden !important;
  display: flex !important;
  flex-direction: column !important;
}
.my-dialog { flex: 1; min-height: 0; height: 100%; overflow: hidden; display: flex; flex-direction: column; }
.my-main   { flex: 1; min-height: 0; height: 100%; overflow: hidden; display: flex; }
.my-side   { height: 100%; overflow-y: auto; }   /* 左栏独立滚 */
.my-body   { flex: 1; min-height: 0; overflow-y: auto; }  /* 右栏独立滚 */
```

**记忆口诀**：Modal 定高 → card-content `min-height: 0` → 要滚的区域自己 `overflow-y: auto`；分栏布局别开 `content-scrollable`。
