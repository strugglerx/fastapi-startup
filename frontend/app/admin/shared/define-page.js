/**
 * 页面元信息 —— 仅代码字段
 * @typedef {Object} PageMeta
 * @property {string}      menuKey
 * @property {string}      path
 * @property {string}      component
 * @property {boolean}     [cacheable=false]
 */

/**
 * 后端返回的运行时菜单项（扁平）
 * @typedef {Object} MenuItem
 * @property {string}      menuKey
 * @property {string|null} parentKey
 * @property {string}      title
 * @property {string}      path
 * @property {string}      component
 * @property {string|null} icon
 * @property {number}      sort
 * @property {boolean}     hidden
 * @property {boolean}     cacheable
 * @property {"code"|"ui"} source
 * @property {boolean}     enabled
 */

/**
 * 前端构建出的菜单树节点
 * @typedef {MenuItem & { children: MenuNode[] }} MenuNode
 */

/**
 * 定义一个页面，允许声明默认的中文标题、父级分组、图标等（作为首次同步的默认值）
 * @param {PageMeta} meta
 * @returns {PageMeta}
 */
export function definePage(meta) {
  if (!meta || typeof meta.menuKey !== "string" || !meta.menuKey) {
    throw new Error("[definePage] menuKey 必填")
  }
  if (typeof meta.path !== "string" || !meta.path.startsWith("/")) {
    throw new Error(`[definePage] path 必须以 / 开头：${meta.menuKey}`)
  }
  if (typeof meta.component !== "string" || !meta.component) {
    throw new Error(`[definePage] component 必填：${meta.menuKey}`)
  }
  return {
    menuKey: meta.menuKey,
    parentKey: meta.parentKey ?? null,
    title: meta.title ?? meta.menuKey,
    path: meta.path,
    component: meta.component,
    icon: meta.icon ?? null,
    sort: meta.sort ?? 9999,
    hidden: meta.hidden ?? false,
    cacheable: meta.cacheable ?? false,
    buttons: Array.isArray(meta.buttons) ? meta.buttons : [],
  }
}
