import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "../stores/user";
import Login from "../components/Login.vue";
import Register from "../components/Register.vue";
import ChatWindow from "../components/ChatWindow.vue";
import KnowledgeBase from "../components/KnowledgeBase.vue";

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
  // ⭐⭐⭐ 知识库管理路由 ⭐⭐⭐
  {
    path: "/knowledge",
    name: "Knowledge",
    component: KnowledgeBase,
    meta: {
      requiresAuth: true,
      requiresRole: ["teacher", "admin"], // ⭐ 只有教师和管理员可访问
    },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// ⭐⭐⭐ 增强型全局前置导航守卫（支持角色权限检查）⭐⭐⭐
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore();

  console.log("🧭 导航守卫:", from.path, "→", to.path);
  console.log("🔐 登录状态:", authStore.isLoggedIn);

  // ========== 1. 需要认证的路由 ==========
  if (to.meta.requiresAuth) {
    if (!authStore.isLoggedIn) {
      console.log("❌ 未登录，重定向到登录页");
      next({ name: "Login", query: { redirect: to.fullPath } });
      return;
    }

    // ⭐⭐⭐ 2. 检查角色权限 ⭐⭐⭐
    if (to.meta.requiresRole && to.meta.requiresRole.length > 0) {
      const userRole = authStore.user?.role;

      console.log("🔑 检查角色权限:");
      console.log("   用户角色:", userRole);
      console.log("   需要角色:", to.meta.requiresRole);

      if (!userRole || !to.meta.requiresRole.includes(userRole)) {
        console.log("❌ 权限不足，重定向到首页");
        alert("您没有权限访问此页面，需要教师或管理员权限。");
        next({ name: "Home" });
        return;
      }

      console.log("✅ 权限检查通过");
    }

    console.log("✅ 已登录，允许访问");
    next();
  }
  // ========== 3. 不需要认证的路由（登录、注册）==========
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
