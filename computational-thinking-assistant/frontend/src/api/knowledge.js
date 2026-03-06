/**
 * 知识库管理 API
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

// 获取 Token
function getAuthHeaders() {
  const token = localStorage.getItem("token");
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export const knowledgeAPI = {
  /**
   * 获取文档列表
   */
  async getDocuments() {
    const response = await fetch(`${API_BASE_URL}/knowledge/documents`, {
      method: "GET",
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  },

  /**
   * ⭐⭐⭐ 获取指定文档的知识块（包含引用统计）⭐⭐⭐
   */
  async getDocumentChunks(filename) {
    console.log(`📡 API 请求: /knowledge/documents/${filename}`);

    const response = await fetch(
      `${API_BASE_URL}/knowledge/documents/${encodeURIComponent(filename)}`,
      {
        method: "GET",
        headers: getAuthHeaders(),
      },
    );

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const result = await response.json();

    // ⭐⭐⭐ 调试：打印返回数据 ⭐⭐⭐
    console.log("📦 API 返回:", result);

    if (result.data && result.data.chunks) {
      console.log(`✅ 成功获取 ${result.data.chunks.length} 个知识块`);

      // 打印每个知识块的引用数据
      result.data.chunks.forEach((chunk, index) => {
        console.log(`   知识块 ${index + 1}:`, {
          id: chunk.id,
          chapter: chunk.chapter,
          content_length: chunk.content?.length || 0,
          retrieved_count: chunk.retrieved_count,
          last_retrieved_at: chunk.last_retrieved_at,
        });
      });
    }

    return result;
  },

  /**
   * 上传文档
   */
  async uploadDocument(file) {
    const formData = new FormData();
    formData.append("file", file);

    const token = localStorage.getItem("token");

    const response = await fetch(`${API_BASE_URL}/knowledge/upload`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        // ⚠️ 注意：不要设置 Content-Type，让浏览器自动设置
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "上传失败");
    }

    return response.json();
  },

  /**
   * 删除文档
   */
  async deleteDocument(filename) {
    const response = await fetch(
      `${API_BASE_URL}/knowledge/documents/${encodeURIComponent(filename)}`,
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

  /**
   * 同步知识库目录（补导入新增文件、清理已删文件记录）
   */
  async syncDocuments() {
    const response = await fetch(`${API_BASE_URL}/knowledge/sync`, {
      method: "POST",
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || "同步失败");
    }

    return response.json();
  },
};
