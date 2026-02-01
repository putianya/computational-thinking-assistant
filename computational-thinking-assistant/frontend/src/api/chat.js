import axios from "axios";

// 基础 URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  withCredentials: true,
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error("API 错误:", error);
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

// ========== 聊天 API ==========

export const chatAPI = {
  /**
   * ⭐⭐⭐ 流式发送消息（修复版）⭐⭐⭐
   */
  async sendMessageStream(
    message,
    sessionId,
    maxContext,
    onChunk,
    onDone,
    onError,
  ) {
    const token = localStorage.getItem("token");

    console.log("📤 发送流式请求:", {
      message: message.substring(0, 30),
      sessionId,
    });

    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          Accept: "text/event-stream",
        },
        credentials: "include",
        body: JSON.stringify({
          message,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      let newSessionId = sessionId;
      let buffer = "";
      let firstChunkReceived = false; // ⭐⭐⭐ 修复：使用驼峰命名 ⭐⭐⭐
      const startTime = Date.now();

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          console.log("📥 流式读取完成");
          break;
        }

        const text = decoder.decode(value, { stream: true });
        buffer += text;

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;

          const jsonStr = line.slice(6).trim();
          if (!jsonStr) continue;

          try {
            const data = JSON.parse(jsonStr);

            // ⭐⭐⭐ 修复：变量名改为 firstChunkReceived ⭐⭐⭐
            if (!firstChunkReceived && data.type === "content") {
              firstChunkReceived = true;
              const latency = Date.now() - startTime;
              console.log(`⚡ 前端首字节延迟: ${latency}ms`);
            }

            switch (data.type) {
              case "session":
                newSessionId = data.session_id;
                console.log("📍 会话 ID:", newSessionId);
                break;

              case "content":
                if (data.content && onChunk) {
                  onChunk(data.content);
                }
                break;

              case "done":
                console.log("✅ 服务器发送完成信号");
                if (onDone) {
                  onDone(newSessionId);
                }
                return;

              case "error":
                console.error("❌ 服务器错误:", data.message);
                if (onError) {
                  onError(new Error(data.message));
                }
                return;
            }
          } catch (parseError) {
            // ⭐⭐⭐ 这个警告现在应该不会出现了 ⭐⭐⭐
            console.warn("⚠️ JSON 解析失败:", jsonStr, parseError);
          }
        }
      }

      if (onDone) {
        onDone(newSessionId);
      }
    } catch (error) {
      console.error("❌ 流式请求失败:", error);
      if (onError) {
        onError(error);
      }
    }
  },

  // ========== 会话管理 API ==========

  async getSessions() {
    return apiClient.get("/sessions");
  },

  async createNewSession() {
    return apiClient.post("/sessions/new");
  },

  async activateSession(sessionId) {
    return apiClient.post(`/sessions/${sessionId}/activate`);
  },

  async deleteSession(sessionId) {
    return apiClient.delete(`/sessions/${sessionId}`);
  },

  async renameSession(sessionId, newTitle) {
    return apiClient.put(`/sessions/${sessionId}`, { title: newTitle });
  },

  async getSessionMessages(sessionId, limit = 50) {
    return apiClient.get(`/sessions/${sessionId}/messages`, {
      params: { limit },
    });
  },

  async getActiveSession() {
    return apiClient.get("/sessions/active");
  },
};

export default chatAPI;
