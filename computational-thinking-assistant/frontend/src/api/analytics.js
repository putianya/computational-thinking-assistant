/**
 * 学习分析 API
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

function getAuthHeaders() {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export const analyticsAPI = {
  /**
   * 获取学习概览数据
   */
  async getOverview(days = 30) {
    const response = await fetch(
      `${API_BASE_URL}/analytics/overview?days=${days}`,
      {
        method: "GET",
        headers: getAuthHeaders(),
      },
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  },

  /**
   * 获取学习趋势图表数据
   */
  async getLearningTrend(days = 30) {
    const response = await fetch(
      `${API_BASE_URL}/analytics/trend?days=${days}`,
      {
        method: "GET",
        headers: getAuthHeaders(),
      },
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  },

  /**
   * 获取知识点掌握度数据
   */
  async getKnowledgeMastery(days = 30) {
    const response = await fetch(
      `${API_BASE_URL}/analytics/knowledge-mastery?days=${days}`,
      {
        method: "GET",
        headers: getAuthHeaders(),
      },
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  },

  /**
   * 获取薄弱环节分析
   */
  async getWeaknessAnalysis(days = 30) {
    const response = await fetch(
      `${API_BASE_URL}/analytics/weakness?days=${days}`,
      {
        method: "GET",
        headers: getAuthHeaders(),
      },
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  },

  /**
   * 获取错误分布数据
   */
  async getErrorDistribution() {
    const response = await fetch(
      `${API_BASE_URL}/analytics/error-distribution`,
      {
        method: "GET",
        headers: getAuthHeaders(),
      },
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  },

  /**
   * 获取代码质量趋势
   */
  async getCodeQualityTrend(days = 30) {
    const response = await fetch(
      `${API_BASE_URL}/analytics/code-quality?days=${days}`,
      {
        method: "GET",
        headers: getAuthHeaders(),
      },
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  },

  /**
   * 获取活动热力图数据
   */
  async getActivityHeatmap(days = 90) {
    const response = await fetch(
      `${API_BASE_URL}/analytics/activity-heatmap?days=${days}`,
      {
        method: "GET",
        headers: getAuthHeaders(),
      },
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  },
};
