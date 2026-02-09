import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/user";

const Login = () => import("../components/Login.vue");
const Register = () => import("../components/Register.vue");
const ChatWindow = () => import("../components/ChatWindow.vue");
const CodeAnalyzer = () => import("../components/CodeAnalyzer.vue"); // ⭐ 新增：代码分析器

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
  // ⭐⭐⭐ 主应用：所有功能都在标签页中 ⭐⭐⭐
  {
    path: "/",
    name: "Home",
    component: ChatWindow, // ⭐ 包含标签栏 + 动态内容
    meta: { requiresAuth: true },
  },
  // ⭐⭐⭐ 新增：代码分析器 ⭐⭐⭐
  {
    path: "/code-analyzer",
    name: "CodeAnalyzer",
    component: CodeAnalyzer,
    meta: { requiresAuth: true }, // 需要登录
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// 路由守卫（保持不变）
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();

  console.log("🧭 导航守卫:", from.path, "→", to.path);
  console.log("🔐 登录状态:", authStore.isLoggedIn);

  if (to.meta.requiresAuth) {
    if (!authStore.isLoggedIn) {
      console.log("❌ 未登录，重定向到登录页");
      next({ name: "Login", query: { redirect: to.fullPath } });
      return;
    }

    console.log("✅ 已登录，允许访问");
    next();
  } else {
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
