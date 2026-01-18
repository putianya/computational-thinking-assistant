import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { authAPI } from "../api/auth";

export const useAuthStore = defineStore("user", () => {
  // 状态数据
  const user = ref(null);
  const token = ref(null);
  const rememberMe = ref(false);

  // 计算属性
  const isLoggedIn = computed(() => !!token.value);

  // 用户登录
  async function login(username, password, remember = false) {
    try {
      const response = await authAPI.login(username, password);

      if (response.status === "success") {
        token.value = response.token;
        user.value = response.user;
        rememberMe.value = remember;

        const storage = remember ? localStorage : sessionStorage;

        if (remember) {
          sessionStorage.removeItem("token");
          sessionStorage.removeItem("user");
          sessionStorage.removeItem("rememberMe");
        } else {
          localStorage.removeItem("token");
          localStorage.removeItem("user");
          localStorage.removeItem("rememberMe");
        }

        storage.setItem("token", response.token);
        storage.setItem("user", JSON.stringify(response.user));
        storage.setItem("rememberMe", remember.toString());

        console.log("✅ 登录成功:", response.user.username);

        return {
          success: true,
          message: response.message,
        };
      } else {
        return {
          success: false,
          message: response.message || "登录失败",
        };
      }
    } catch (error) {
      console.error("❌ 登录失败:", error);
      return {
        success: false,
        message: error.message || "登录请求失败",
      };
    }
  }

  // 用户注册
  async function register(username, password, email = "", nickname = "") {
    try {
      const response = await authAPI.register(
        username,
        password,
        email,
        nickname,
      );

      if (response.status === "success") {
        console.log("✅ 注册成功:", username);
        return {
          success: true,
          message: response.message,
        };
      } else {
        return {
          success: false,
          message: response.message || "注册失败",
        };
      }
    } catch (error) {
      console.error("❌ 注册失败:", error);
      return {
        success: false,
        message: error.message || "注册请求失败",
      };
    }
  }

  // 自动登录
  async function autoLogin() {
    try {
      let storedToken = null;
      let storedUser = null;
      let storedRememberMe = false;

      const localToken = localStorage.getItem("token");
      const sessionToken = sessionStorage.getItem("token");

      if (localToken) {
        storedToken = localToken;
        storedUser = localStorage.getItem("user");
        storedRememberMe = true;
        console.log("🔍 从 localStorage 恢复登录状态（记住密码）");
      } else if (sessionToken) {
        storedToken = sessionToken;
        storedUser = sessionStorage.getItem("user");
        storedRememberMe = false;
        console.log("🔍 从 sessionStorage 恢复登录状态（不记住密码）");
      } else {
        console.log("📭 没有找到本地 Token");
        return false;
      }

      if (!storedToken) {
        console.log("📭 Token 为空");
        return false;
      }

      console.log("🔍 找到本地 Token，验证中...");

      const response = await authAPI.verifyToken(storedToken);

      if (response.status === "success") {
        token.value = storedToken;
        user.value = JSON.parse(storedUser);
        rememberMe.value = storedRememberMe;

        console.log("✅ 自动登录成功:", user.value.username);
        return true;
      } else {
        console.log("❌ Token 已失效:", response.message);
        clearStorage();
        return false;
      }
    } catch (error) {
      console.error("❌ 自动登录失败:", error);
      clearStorage();
      return false;
    }
  }

  // 退出登录
  function logout() {
    user.value = null;
    token.value = null;
    rememberMe.value = false;
    clearStorage();
    console.log("✅ 已退出登录");
  }

  // 清除所有存储
  function clearStorage() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("rememberMe");

    sessionStorage.removeItem("token");
    sessionStorage.removeItem("user");
    sessionStorage.removeItem("rememberMe");
  }

  // 更新用户信息
  function updateUser(newUserData) {
    user.value = { ...user.value, ...newUserData };
    const storage = rememberMe.value ? localStorage : sessionStorage;
    storage.setItem("user", JSON.stringify(user.value));
  }

  return {
    user,
    token,
    isLoggedIn,
    rememberMe,
    login,
    register,
    autoLogin,
    logout,
    updateUser,
  };
});
