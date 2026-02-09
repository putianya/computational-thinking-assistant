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
      throw new Error("登录请求失败");
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
      throw new Error("注册请求失败");
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
      throw new Error("Token 验证失败");
    }

    return response.json();
  },
};
