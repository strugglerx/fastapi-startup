/**
 * 权限校验辅助函数
 */

/**
 * 判断当前登录用户是否拥有指定权限
 * @param {string} permission 权限编码/标识
 * @returns {boolean}
 */
export function hasPermission(permission) {
  try {
    const raw = localStorage.getItem("smartai_admin_user")
    if (!raw) return false
    const user = JSON.parse(raw)
    if (!user) return false
    
    // 超级管理员角色或种子管理员拥有所有权限
    if (user.role === "admin" || user.fixed || (user.permissions && user.permissions.includes("*"))) {
      return true
    }
    
    if (!user.permissions || !Array.isArray(user.permissions)) {
      return false
    }
    
    return user.permissions.includes(permission)
  } catch (e) {
    console.error("[auth] hasPermission error:", e)
    return false
  }
}
