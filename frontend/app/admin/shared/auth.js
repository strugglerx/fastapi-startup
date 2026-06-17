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
    
    // 支持权限等级继承：如校验 system:admin:create，若用户已授权主菜单 system:admin 即可通过
    if (user.permissions.includes(permission)) {
      return true
    }
    
    if (permission.includes(":")) {
      const parts = permission.split(":")
      const parentPermission = parts.slice(0, -1).join(":")
      if (user.permissions.includes(parentPermission)) {
        return true
      }
    }
    
    return false
  } catch (e) {
    console.error("[auth] hasPermission error:", e)
    return false
  }
}
