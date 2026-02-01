/**
 * 知识库管理 API
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

// 获取 Token
function getAuthHeaders() {
  const token = localStorage.getItem("token");
  return {
    Authorization: `Bearer ${token}`,
  };
}

export const knowledgeAPI = {
  /**
   * 获取知识块列表
   */
  async getChunks(params = {}) {
    const { page = 1, per_page = 20, source, chapter, search } = params;

    const queryParams = new URLSearchParams({
      page: page.toString(),
      per_page: per_page.toString(),
    });

    if (source) queryParams.append("source", source);
    if (chapter) queryParams.append("chapter", chapter);
    if (search) queryParams.append("search", search);

    const response = await fetch(
      `${API_BASE_URL}/knowledge/chunks?${queryParams}`,
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
   * 上传文档
   */
  async uploadDocument(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/knowledge/upload`, {
      method: "POST",
      headers: getAuthHeaders(),
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "上传失败");
    }

    return response.json();
  },

  /**
   * 删除知识块
   */
  async deleteChunk(chunkId) {
    const response = await fetch(
      `${API_BASE_URL}/knowledge/chunks/${chunkId}`,
      {
        method: "DELETE",
        headers: getAuthHeaders(),
      },
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "删除失败");
    }

    return response.json();
  },

  /**
   * 编辑知识块
   */
  async updateChunk(chunkId, data) {
    const response = await fetch(
      `${API_BASE_URL}/knowledge/chunks/${chunkId}`,
      {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...getAuthHeaders(),
        },
        body: JSON.stringify(data),
      },
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "更新失败");
    }

    return response.json();
  },

  /**
   * 获取统计信息
   */
  async getStats() {
    const response = await fetch(`${API_BASE_URL}/knowledge/stats`, {
      method: "GET",
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  },
};
