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
   * 测试系统连接
   */
  async testConnection() {
    try {
      const response = await fetch(`${API_BASE_URL}/test`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      return response.json();
    } catch (error) {
      console.error("❌ 系统测试失败:", error);
      throw error;
    }
  },

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
    onMeta,
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
      let firstChunkReceived = false;
      const startTime = Date.now();
      let sawRagMeta = false;

      // ⭐⭐⭐ 新增：累积所有内容（即使前端不显示）⭐⭐⭐
      let accumulatedContent = "";

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          console.log("📥 流式读取完成");
          console.log(`📊 后端总共生成: ${accumulatedContent.length} 字符`);
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

              case "rag_meta": {
                sawRagMeta = true;
                const refs = data.referenced_chunks || [];
                console.group(
                  `🧠 对话模式=${data.mode} | 置信度模式=${data.confidence_mode}`,
                );
                console.log("question_type:", data.question_type);
                console.log("needs_rag:", data.needs_rag);
                console.log("max_score:", data.max_score, "threshold:", data.threshold);
                console.log("raw_result_count:", data.raw_result_count);
                console.log("used_result_count:", data.used_result_count);
                console.log("referenced_chunk_ids:", data.referenced_chunk_ids || []);
                if (refs.length > 0) {
                  console.table(
                    refs.map((x) => ({
                      chunk_id: x.chunk_id,
                      score: x.score,
                      source: x.source,
                      chapter: x.chapter,
                      section: x.section,
                    })),
                  );
                } else {
                  console.log("本轮未引用知识块");
                }
                if (data.skip_reason) {
                  console.log("skip_reason:", data.skip_reason);
                }
                console.groupEnd();

                if (onMeta) {
                  onMeta(data);
                }
                break;
              }

              case "content":
                if (data.content) {
                  // ⭐ 始终累积内容（后台记录）
                  accumulatedContent += data.content;

                  // ⭐ 只有在有回调时才调用（前端可能已切走）
                  if (onChunk) {
                    onChunk(data.content);
                  }
                }
                break;

              case "done":
                console.log("✅ 服务器发送完成信号");
                if (!sawRagMeta) {
                  console.warn("⚠️ 本轮未收到 rag_meta，已使用兼容兜底信息");
                  if (onMeta) {
                    onMeta({
                      type: "rag_meta",
                      mode: "unknown",
                      confidence_mode: "none",
                      question_type: "unknown",
                      needs_rag: null,
                      skip_reason: "前端未收到后端RAG元信息（兼容兜底）",
                      max_score: 0,
                      threshold: null,
                      raw_result_count: 0,
                      used_result_count: 0,
                      referenced_chunk_ids: [],
                      referenced_chunks: [],
                    });
                  }
                }
                console.log(
                  `📊 完整回答长度: ${accumulatedContent.length} 字符`,
                );

                if (onDone) {
                  // ⭐ 传递完整内容给 onDone
                  onDone(newSessionId, accumulatedContent);
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
            console.warn("⚠️ JSON 解析失败:", jsonStr, parseError);
          }
        }
      }

      if (onDone) {
        // ⭐ 即使没有明确的 done 信号，也传递完整内容
        onDone(newSessionId, accumulatedContent);
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
