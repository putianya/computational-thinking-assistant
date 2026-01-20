import { defineStore } from "pinia";
import { ref } from "vue";
import { authAPI } from "../api/auth";
import { useChatStore } from "./chat";

// ⭐ 改回 useAuthStore
export const useAuthStore = defineStore("user", () => {
  // ← 这里改
  // ========== 状态 ==========
  const isLoggedIn = ref(false);
  const user = ref(null);
  const token = ref(null);
  const rememberMe = ref(false);
  const isLoading = ref(false);

  // ========== 方法 ==========

  /**
   * 用户登录
   */
  async function login(username, password, remember = false) {
    try {
      isLoading.value = true;
      console.log("🔐 尝试登录:", username);

      const response = await authAPI.login(username, password);

      if (response.status === "success") {
        isLoggedIn.value = true;
        user.value = response.user;
        token.value = response.token;
        rememberMe.value = remember;

        localStorage.setItem("token", response.token);

        if (remember) {
          localStorage.setItem("username", username);
          localStorage.setItem("rememberMe", "true");
        } else {
          localStorage.removeItem("username");
          localStorage.removeItem("rememberMe");
        }

        console.log("✅ 登录成功:", response.user.username);

        // ⭐ 加载会话列表
        const chatStore = useChatStore();
        console.log("📋 登录成功，开始加载会话列表...");
        await chatStore.loadSessions();
        console.log("✅ 会话列表加载完成");

        return {
          success: true,
          message: "登录成功",
          user: response.user,
        };
      } else {
        console.error("❌ 登录失败:", response.message);
        return {
          success: false,
          message: response.message || "登录失败",
        };
      }
    } catch (error) {
      console.error("❌ 登录异常:", error);

      let errorMessage = "登录失败，请检查网络连接";

      if (error.response) {
        if (error.response.status === 401) {
          errorMessage = "用户名或密码错误";
        } else if (error.response.status === 500) {
          errorMessage = "服务器错误，请稍后重试";
        } else {
          errorMessage = error.response.data?.message || "登录失败";
        }
      } else if (error.request) {
        errorMessage = "无法连接到服务器，请检查网络";
      }

      return {
        success: false,
        message: errorMessage,
      };
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * 自动登录（Token 验证）
   */
  async function autoLogin() {
    const savedToken = localStorage.getItem("token");

    if (!savedToken) {
      console.log("⚠️ 没有保存的 Token，跳过自动登录");
      return false;
    }

    try {
      isLoading.value = true;
      console.log("🔄 尝试自动登录...");

      const response = await authAPI.verifyToken(savedToken);

      if (response.status === "success") {
        isLoggedIn.value = true;
        token.value = savedToken;
        user.value = {
          id: response.user_id,
          username: response.username,
        };

        const savedRememberMe = localStorage.getItem("rememberMe");
        rememberMe.value = savedRememberMe === "true";

        console.log("✅ 自动登录成功:", response.username);

        // ⭐ 加载会话列表
        const chatStore = useChatStore();
        console.log("📋 自动登录成功，开始加载会话列表...");
        await chatStore.loadSessions();
        console.log("✅ 会话列表加载完成");

        return true;
      } else {
        console.warn("⚠️ Token 验证失败:", response.message);
        logout();
        return false;
      }
    } catch (error) {
      console.error("❌ 自动登录失败:", error);
      logout();
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * 用户登出
   */
  function logout() {
    console.log("👋 用户登出");

    isLoggedIn.value = false;
    user.value = null;
    token.value = null;

    localStorage.removeItem("token");

    // ⭐ 重置聊天 Store
    const chatStore = useChatStore();
    console.log("🔄 重置聊天 Store...");
    chatStore.resetStore();
    console.log("✅ 聊天 Store 已重置");
  }

  /**
   * 获取用户信息
   */
  async function fetchUserProfile() {
    try {
      console.log("📥 获取用户信息...");
      const response = await authAPI.getUserProfile();

      if (response.status === "success") {
        user.value = response.user;
        console.log("✅ 用户信息已更新");
        return response.user;
      } else {
        console.error("❌ 获取用户信息失败");
        return null;
      }
    } catch (error) {
      console.error("❌ 获取用户信息异常:", error);
      return null;
    }
  }

  /**
   * 更新用户信息
   */
  function updateUser(newUserData) {
    if (user.value) {
      user.value = { ...user.value, ...newUserData };
      console.log("✅ 用户信息已更新:", user.value);
    }
  }

  // ========== 导出 ==========
  return {
    // 状态
    isLoggedIn,
    user,
    token,
    rememberMe,
    isLoading,

    // 方法
    login,
    autoLogin,
    logout,
    fetchUserProfile,
    updateUser,
  };
});
