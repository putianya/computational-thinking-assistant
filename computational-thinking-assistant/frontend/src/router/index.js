import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/user";
import Login from "../components/Login.vue";
import Register from "../components/Register.vue";
import ChatWindow from "../components/ChatWindow.vue";

const routes = [
  {
    path: "/login",
    name: "Login",
    component: Login,
    meta: { requiresAuth: false },
  },
  {
    path: "/register",
    name: "Register",
    component: Register,
    meta: { requiresAuth: false },
  },
  {
    path: "/",
    name: "Home",
    component: ChatWindow,
    meta: { requiresAuth: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// 全局前置导航守卫
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();

  console.log("🧭 导航守卫:", from.path, "→", to.path);
  console.log("🔐 登录状态:", authStore.isLoggedIn);

  // 需要认证的路由
  if (to.meta.requiresAuth) {
    if (!authStore.isLoggedIn) {
      console.log("❌ 未登录，重定向到登录页");
      next({ name: "Login", query: { redirect: to.fullPath } });
    } else {
      console.log("✅ 已登录，允许访问");
      next();
    }
  }
  // 不需要认证的路由（登录、注册）
  else {
    // 如果已登录，访问登录或注册页时重定向到首页
    if (
      authStore.isLoggedIn &&
      (to.name === "Login" || to.name === "Register")
    ) {
      console.log("✅ 已登录，重定向到首页");
      next({ name: "Home" });
    } else {
      console.log("✅ 允许访问");
      next();
    }
  }
});

export default router;
