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
   * ⭐⭐⭐ 新增：发送学习心跳 ⭐⭐⭐
   */
  async sendHeartbeat(page = "chat", sessionId = null) {
    try {
      const response = await fetch(`${API_BASE_URL}/analytics/heartbeat`, {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify({ page, session_id: sessionId }),
      });
      return response.json();
    } catch (error) {
      // 心跳失败不影响主流程，静默处理
      console.debug("💓 心跳发送失败（静默）");
      return null;
    }
  },

  /**
   * ⭐⭐⭐ 新增：获取学生列表 ⭐⭐⭐
   */
  async getStudents() {
    const response = await fetch(`${API_BASE_URL}/analytics/students`, {
      method: "GET",
      headers: getAuthHeaders(),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  },

  /**
   * 获取学习概览数据
   * @param {number} days - 天数
   * @param {number|null} userId - 指定学生ID（不传则获取汇总）
   */
  async getOverview(days = 30, userId = null) {
    let url = `${API_BASE_URL}/analytics/overview?days=${days}`;
    if (userId) url += `&user_id=${userId}`;

    const response = await fetch(url, {
      method: "GET",
      headers: getAuthHeaders(),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  },

  /**
   * 获取学习趋势图表数据
   */
  async getLearningTrend(days = 30, userId = null) {
    let url = `${API_BASE_URL}/analytics/trend?days=${days}`;
    if (userId) url += `&user_id=${userId}`;

    const response = await fetch(url, {
      method: "GET",
      headers: getAuthHeaders(),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  },

  /**
   * 获取知识点掌握度数据
   */
  async getKnowledgeMastery(days = 30, userId = null) {
    let url = `${API_BASE_URL}/analytics/knowledge-mastery?days=${days}`;
    if (userId) url += `&user_id=${userId}`;

    const response = await fetch(url, {
      method: "GET",
      headers: getAuthHeaders(),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  },

  /**
   * 获取薄弱环节分析
   */
  async getWeaknessAnalysis(days = 30, userId = null) {
    let url = `${API_BASE_URL}/analytics/weakness?days=${days}`;
    if (userId) url += `&user_id=${userId}`;

    const response = await fetch(url, {
      method: "GET",
      headers: getAuthHeaders(),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  },

  /**
   * 获取错误分布数据
   */
  async getErrorDistribution(userId = null) {
    let url = `${API_BASE_URL}/analytics/error-distribution`;
    if (userId) url += `?user_id=${userId}`;

    const response = await fetch(url, {
      method: "GET",
      headers: getAuthHeaders(),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  },

  /**
   * 获取代码质量趋势
   */
  async getCodeQualityTrend(days = 30, userId = null) {
    let url = `${API_BASE_URL}/analytics/code-quality?days=${days}`;
    if (userId) url += `&user_id=${userId}`;

    const response = await fetch(url, {
      method: "GET",
      headers: getAuthHeaders(),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  },

  /**
   * 获取活动热力图数据
   */
  async getActivityHeatmap(days = 90, userId = null) {
    let url = `${API_BASE_URL}/analytics/activity-heatmap?days=${days}`;
    if (userId) url += `&user_id=${userId}`;

    const response = await fetch(url, {
      method: "GET",
      headers: getAuthHeaders(),
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  },
};
