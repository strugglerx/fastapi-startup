/**
 * 前端展示元信息——由 frontend/.env 的 VITE_APP_NAME 注入。
 * 同时被 admin 与 login 两个入口共享，避免硬编码品牌名。
 */
export const APP_NAME = import.meta.env.VITE_APP_NAME || "智慧AI 探索平台"
