import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const chatAPI = {
  // 测试系统状态
  async testConnection() {
    const response = await api.get("/test");
    return response.data;
  },

  // ⭐⭐⭐ 发送流式消息 ⭐⭐⭐
  async sendMessageStream(message, sessionId, onChunk, onDone, onError) {
    try {
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message,
          session_id: sessionId,
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

  // ⭐ 新增：清除上下文
  async clearContext(sessionId) {
    const response = await api.post("/chat/clear-context", {
      session_id: sessionId,
    });
    return response.data;
  },

  // ⭐ 新增：获取上下文信息
  async getContextInfo(sessionId) {
    const response = await api.get(`/chat/context-info/${sessionId}`);
    return response.data;
  },
};
