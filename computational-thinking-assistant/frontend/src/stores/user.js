import { defineStore } from "pinia";
import { ref } from "vue";
import { authAPI } from "../api/auth";
import { useChatStore } from "./chat";

// ⭐ 改回 useAuthStore
export const useAuthStore = defineStore("user", () => {
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

        // ⭐⭐⭐ 新增：保存用户信息到 localStorage（包含角色）⭐⭐⭐
        localStorage.setItem("user", JSON.stringify(response.user));

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
    const savedUser = localStorage.getItem("user"); // ⭐ 新增

    if (!savedToken) {
      console.log("⚠️ 没有保存的 Token，跳过自动登录");
      return false;
    }

    try {
      isLoading.value = true;
      console.log("🔄 尝试自动登录...");

      // ⭐⭐⭐ 优化：优先使用本地缓存的用户信息 ⭐⭐⭐
      if (savedUser) {
        try {
          user.value = JSON.parse(savedUser);
          isLoggedIn.value = true;
          token.value = savedToken;
          console.log("✅ 使用缓存用户信息:", user.value.username);
          console.log("   角色:", user.value.role_display);

          // 加载会话列表
          const chatStore = useChatStore();
          await chatStore.loadSessions();

          return true;
        } catch (e) {
          console.warn("⚠️ 解析缓存用户信息失败，尝试验证 Token");
        }
      }

      // 如果没有缓存或解析失败，验证 Token

      const response = await authAPI.verifyToken(savedToken);

      if (response.status === "success") {
        isLoggedIn.value = true;
        token.value = savedToken;
        user.value = {
          id: response.user_id,
          username: response.username,
          role: response.role || "student", // ⭐ 确保有角色信息
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

    // ⭐ 清除认证相关的 localStorage
    localStorage.removeItem("token");
    localStorage.removeItem("user");

    // ⭐⭐⭐ 新增：清除代码分析相关的 localStorage ⭐⭐⭐
    localStorage.removeItem("code_analyzer_draft");
    localStorage.removeItem("code_analysis_type");
    localStorage.removeItem("code_analysis_result");
    localStorage.removeItem("code_chat_history");

    console.log("🗑️ 已清除代码分析数据");

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

  // ========== ⭐⭐⭐ 权限检查方法（完善版）⭐⭐⭐ ==========

  /**
   * 检查用户是否有指定权限
   *
   * @param {string} action - 权限名称
   * @returns {boolean}
   */
  function hasPermission(action) {
    // 如果用户信息中包含权限列表，直接检查
    if (user.value?.permissions && Array.isArray(user.value.permissions)) {
      return user.value.permissions.includes(action);
    }

    // 否则根据角色判断（后备方案）
    const permissionMap = {
      // 基础功能（所有角色）
      ask: ["student", "teacher", "admin"],
      view_knowledge: ["student", "teacher", "admin"],
      view_sessions: ["student", "teacher", "admin"],
      create_session: ["student", "teacher", "admin"],

      // 知识库管理（教师、管理员）
      upload_doc: ["teacher", "admin"],
      manage_knowledge: ["teacher", "admin"],
      delete_knowledge: ["teacher", "admin"],
      edit_knowledge: ["teacher", "admin"],
      view_knowledge_stats: ["teacher", "admin"],

      // 用户管理（仅管理员）
      manage_users: ["admin"],
      view_all_sessions: ["admin"],
      delete_user: ["admin"],
      change_user_role: ["admin"],
      view_system_stats: ["admin"],
    };

    const allowedRoles = permissionMap[action] || [];
    return allowedRoles.includes(user.value?.role);
  }

  /**
   * 检查用户是否有指定角色
   */
  function hasRole(role) {
    return user.value?.role === role;
  }

  /**
   * 检查用户是否有任意一个角色
   */
  function hasAnyRole(roles) {
    if (!user.value?.role) return false;
    return roles.includes(user.value.role);
  }

  /**
   * 检查是否是教师
   */
  function isTeacher() {
    return user.value?.role === "teacher";
  }

  /**
   * 检查是否是管理员
   */
  function isAdmin() {
    return user.value?.role === "admin";
  }

  /**
   * 检查是否是学生
   */
  function isStudent() {
    return user.value?.role === "student";
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

    // ⭐ 新增：权限检查方法
    hasPermission,
    hasRole,
    hasAnyRole,
    isTeacher,
    isAdmin,
    isStudent,
  };
});
