import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// ⭐ 请求拦截器：自动添加 Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

export const chatAPI = {
  // ========== 现有方法 ==========

  // 测试系统状态
  async testConnection() {
    const response = await api.get("/test");
    return response.data;
  },

  // ⭐⭐⭐ 发送流式消息 ⭐⭐⭐
  async sendMessageStream(
    message,
    sessionId,
    maxContext,
    onChunk,
    onDone,
    onError,
  ) {
    try {
      // ⭐ 获取 Token
      const token = localStorage.getItem("token");

      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: token ? `Bearer ${token}` : "", // ⭐ 添加认证
        },
        body: JSON.stringify({
          message,
          session_id: sessionId,
          max_context: maxContext, // ⭐ 传递上下文长度
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let buffer = "";
      let currentSessionId = sessionId;

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // ⭐ 处理 SSE 数据流
        const lines = buffer.split("\n");
        buffer = lines.pop() || ""; // 保留不完整的行

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));

              // ⭐ 根据不同类型处理
              if (data.type === "session") {
                currentSessionId = data.session_id;
              } else if (data.type === "content") {
                onChunk(data.content);
              } else if (data.type === "done") {
                onDone(currentSessionId);
              } else if (data.type === "error") {
                onError(new Error(data.message));
              }
            } catch (e) {
              console.error("解析 SSE 数据失败:", e);
            }
          }
        }
      }
    } catch (error) {
      onError(error);
    }
  },

  // 清除上下文（已废弃，保留兼容）
  async clearContext(sessionId) {
    const response = await api.post("/chat/clear-context", {
      session_id: sessionId,
    });
    return response.data;
  },

  // 获取上下文信息
  async getContextInfo(sessionId) {
    const response = await api.get(`/chat/context-info/${sessionId}`);
    return response.data;
  },

  // ========== ⭐ 新增：会话管理 API ⭐ ==========

  /**
   * 获取会话列表
   * @returns {Promise<{status: string, sessions: Array}>}
   */
  async getSessions() {
    try {
      const response = await api.get("/sessions");
      return response.data;
    } catch (error) {
      console.error("❌ 获取会话列表失败:", error);
      throw error;
    }
  },

  /**
   * 获取会话消息
   * @param {string} sessionId - 会话 ID
   * @param {number} limit - 消息数量限制
   * @returns {Promise<{status: string, messages: Array}>}
   */
  async getSessionMessages(sessionId, limit = 50) {
    try {
      const response = await api.get(`/sessions/${sessionId}/messages`, {
        params: { limit },
      });
      return response.data;
    } catch (error) {
      console.error("❌ 获取会话消息失败:", error);
      throw error;
    }
  },

  /**
   * 切换会话
   * @param {string} sessionId - 会话 ID
   * @returns {Promise<{status: string, session: Object, messages: Array}>}
   */
  async activateSession(sessionId) {
    try {
      const response = await api.post(`/sessions/${sessionId}/activate`);
      return response.data;
    } catch (error) {
      console.error("❌ 切换会话失败:", error);
      throw error;
    }
  },

  /**
   * 创建新会话（归档当前会话）
   * @returns {Promise<{status: string, session: Object}>}
   */
  async createNewSession() {
    try {
      const response = await api.post("/sessions/new");
      return response.data;
    } catch (error) {
      console.error("❌ 创建新会话失败:", error);
      throw error;
    }
  },

  /**
   * 删除会话
   * @param {string} sessionId - 会话 ID
   * @returns {Promise<{status: string, message: string, new_session?: Object}>}
   * @throws {Error} 删除失败时抛出错误
   */
  async deleteSession(sessionId) {
    try {
      // ⭐ 1. 显式检查 Token
      const token = localStorage.getItem("token");
      if (!token) {
        throw new Error("请先登录");
      }

      // ⭐ 2. 显式添加 Authorization 头（更安全）
      const response = await api.delete(`/sessions/${sessionId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      // ⭐ 3. 返回完整的响应数据
      return response.data;
    } catch (error) {
      // ⭐ 4. 详细的错误处理
      if (error.response) {
        const status = error.response.status;
        const message = error.response.data?.message || "删除会话失败";

        switch (status) {
          case 401:
            console.error("❌ 未授权：Token 可能已失效");
            // 可以触发重新登录
            localStorage.removeItem("token");
            throw new Error("登录已过期，请重新登录");

          case 403:
            console.error("❌ 权限不足：无法删除其他用户的会话");
            throw new Error("无权删除此会话");

          case 404:
            console.error("❌ 会话不存在");
            throw new Error("会话不存在或已被删除");

          case 500:
            console.error("❌ 服务器错误:", message);
            throw new Error("服务器错误，请稍后重试");

          default:
            console.error("❌ 删除会话失败:", message);
            throw new Error(message);
        }
      } else if (error.request) {
        // 请求已发送但未收到响应
        console.error("❌ 网络错误：未收到服务器响应");
        throw new Error("网络连接失败，请检查网络");
      } else {
        // 其他错误
        console.error("❌ 删除会话失败:", error.message);
        throw error;
      }
    }
  },
};
