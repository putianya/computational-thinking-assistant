/**
 * 认证相关 API
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

/**
 * ⭐ 新增：获取存储的 Token
 */
export function getToken() {
  return localStorage.getItem("token");
}

/**
 * ⭐ 新增：设置 Token
 */
export function setToken(token) {
  localStorage.setItem("token", token);
}

/**
 * ⭐ 新增：移除 Token
 */
export function removeToken() {
  localStorage.removeItem("token");
}

// ⭐ 确保这个函数存在
function getAuthHeaders() {
  const token = localStorage.getItem("token");
  const headers = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  return headers;
}

export const authAPI = {
  /**
   * 用户登录
   */
  async login(username, password) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "登录失败");
    }

    return response.json();
  },

  /**
   * 用户注册
   */
  async register(username, password, email = "", nickname = "") {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        username,
        password,
        email: email || undefined,
        nickname: nickname || undefined,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "注册失败");
    }

    return response.json();
  },

  /**
   * 验证 Token
   */
  async verifyToken(token) {
    const response = await fetch(`${API_BASE_URL}/auth/verify`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ token }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "Token 验证失败");
    }

    return response.json();
  },

  // ⭐⭐⭐ 确认这个方法存在 ⭐⭐⭐
  async logout() {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || "退出登录失败");
      }

      return response.json();
    } catch (error) {
      console.error("❌ 退出登录 API 调用失败:", error);
      // ⭐ 即使失败也返回成功（前端会强制清除本地数据）
      return { status: "success", message: "已清除本地数据" };
    }
  },
};

// ❌❌❌ 删除这一行（如果存在）❌❌❌
// export { authAPI };  // ← 这行会导致重复导出错误！
