# Agent Progress

最后更新：2026-06-17 12:44 CST

## 当前目标

- 将项目初始化为 `SmartAI-explore / 智慧AI探索平台`。
- 前端登录页先作为新项目后台壳使用，后端继续沿用 FastAPI 脚手架结构。
- 后续 clear / compact / 新会话后，先读本文件恢复上下文。

## 已完成

- 登录页品牌改为 `SmartAI-explore`，中文名为 `智慧AI探索平台`。
- 登录页素材已替换：
  - `frontend/public/images/logo.png`：二维扁平 logo，已用 `rembg` 去背景。
  - `frontend/public/images/favicon.png` 与 `frontend/public/favicon.ico`：由 logo 生成。
  - `frontend/public/images/login-bg.png`：重新生成的暗色 AI 平台背景，四周接近纯黑，适配手电筒效果。
  - 四张轮播图已简化，第四项从 RAG/知识库改为“会话与工具追踪”。
- `frontend/app/login/components/LoginBackground.vue` 已改为参考项目同款机制：
  - 单张背景图。
  - 鼠标视差。
  - 手电筒径向遮罩。
  - 粒子层。
- 登录页 / 后台页标题、loader、侧栏品牌文案已统一。
- Vite 分包警告已处理：`AdminProfileView.vue` 在 `frontend/app/admin/App.vue` 中改为 `defineAsyncComponent`。

## 验证

- 已多次运行 `cd frontend && pnpm build`，最后一次构建通过且无 Vite 警告。

## 当前未提交状态提示

- 仓库当前在 `dev` 分支。
- 后端存在菜单相关改动，可能来自用户或其他会话：
  - `backend/app/db/models.py`
  - `backend/app/main.py`
  - `backend/app/api/menu.py`
  - `backend/app/service/menu_service.py`
- 不要在未确认的情况下回滚这些后端改动。

## 下一步建议

- 若继续前端登录页，可优先实际打开页面检查：
  - 背景四周是否自然融入黑底。
  - 手电筒移动是否和参考项目一致。
  - logo 在顶部、登录 loading、favicon 中是否足够清晰。
- 若继续后端，应先读 `backend/CLAUDE.md`，再围绕当前菜单改动确认接口和模型设计。

## 维护规则

- 阶段性完成、上下文快满、用户要 clear / 新开会话、任务中断前，更新本文件。
- 只记录恢复任务必需的信息，不写凭证、不写长日志、不替代正式文档。
