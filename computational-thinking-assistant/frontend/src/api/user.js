/**
 * 用户管理 API（管理员）
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

function getAuthHeaders() {
  const token = localStorage.getItem("token");
  return {
    Authorization: `Bearer ${token}`,
  };
}

export const userAPI = {
  /**
   * 获取所有用户列表
   */
  async getAllUsers() {
    const response = await fetch(`${API_BASE_URL}/admin/users`, {
      method: "GET",
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  },

  /**
   * ⭐⭐⭐ 新增：创建用户 ⭐⭐⭐
   */
  async createUser(userData) {
    const response = await fetch(`${API_BASE_URL}/admin/users`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "创建用户失败");
    }

    return response.json();
  },

  /**
   * ⭐⭐⭐ 新增：更新用户完整信息 ⭐⭐⭐
   */
  async updateUser(userId, userData) {
    const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "更新用户失败");
    }

    return response.json();
  },

  /**
   * 修改用户角色（保持兼容）
   */
  async changeUserRole(userId, newRole) {
    const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/role`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...getAuthHeaders(),
      },
      body: JSON.stringify({ role: newRole }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "修改角色失败");
    }

    return response.json();
  },

  /**
   * 启用/禁用用户
   */
  async toggleUserStatus(userId, isActive) {
    const response = await fetch(
      `${API_BASE_URL}/admin/users/${userId}/status`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify({ is_active: isActive }),
      },
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "切换状态失败");
    }

    return response.json();
  },

  /**
   * 删除用户
   */
  async deleteUser(userId) {
    const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
      method: "DELETE",
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "删除用户失败");
    }

    return response.json();
  },

  /**
   * 获取所有教师列表
   */
  async getTeachers() {
    const response = await fetch(`${API_BASE_URL}/admin/teachers`, {
      method: "GET",
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  },

  /**
   * 获取所有学生列表（管理员用）
   */
  async getStudents() {
    const response = await fetch(`${API_BASE_URL}/admin/users`, {
      method: "GET",
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const result = await response.json();
    // 在前端过滤学生
    if (result.status === "success") {
      result.data.users = result.data.users.filter((u) => u.role === "student");
    }
    return result;
  },
};
