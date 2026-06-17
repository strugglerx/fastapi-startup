export const Layout = () => import("../components/Layout/index.vue")

export const constantRoutes = [
  { path: "/login", name: "Login", component: () => import("../views/error/404/index.vue"), meta: { hidden: true } },
  { path: "/404", name: "NotFound", component: () => import("../views/error/404/index.vue"), meta: { hidden: true } },
  {
    path: "/",
    name: "Root",
    component: Layout,
    children: [],
  },
]
