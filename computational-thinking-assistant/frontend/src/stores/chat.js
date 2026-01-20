import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { chatAPI } from "../api/chat";

export const useChatStore = defineStore("chat", () => {
  // ========== 现有状态 ==========
  const messages = ref([]); // 当前会话的消息
  const isStreaming = ref(false);
  const currentReply = ref("");

  // ========== ⭐ 新增状态 ⭐ ==========
  const sessions = ref([]); // 所有会话列表
  const currentSession = ref(null); // 当前会话对象
  const isLoadingSessions = ref(false);

  // 会话和上下文设置
  const sessionId = ref(null);
  const maxContextLength = ref(
    parseInt(localStorage.getItem("maxContextLength")) || 10,
  );

  // ========== 计算属性 ==========
  const currentContextLength = computed(() => {
    return Math.floor(messages.value.length / 2); // 对话轮数
  });

  const hasMessages = computed(() => {
    return messages.value.length > 0;
  });

  const activeSessions = computed(() => {
    return sessions.value.filter((s) => s.is_active);
  });

  const archivedSessions = computed(() => {
    return sessions.value.filter((s) => !s.is_active);
  });

  // ========== ⭐ 新增方法：会话管理 ⭐ ==========

  /**
   * 加载会话列表（登录后调用）
   */
  async function loadSessions() {
    try {
      isLoadingSessions.value = true;
      console.log("📋 加载会话列表...");

      const response = await chatAPI.getSessions();

      if (response.status === "success") {
        sessions.value = response.sessions;
        console.log(`✅ 加载了 ${sessions.value.length} 个会话`);

        // ⭐ 找到当前活跃会话
        const activeSession = sessions.value.find((s) => s.is_active);

        if (activeSession) {
          currentSession.value = activeSession;
          sessionId.value = activeSession.session_id;

          // ⭐ 加载该会话的消息
          await loadSessionMessages(activeSession.session_id);
          console.log(`✅ 当前会话: ${activeSession.title}`);
        } else {
          console.log("📝 没有活跃会话，将在首次发送消息时创建");
        }
      }
    } catch (error) {
      console.error("❌ 加载会话列表失败:", error);
    } finally {
      isLoadingSessions.value = false;
    }
  }

  /**
   * 加载指定会话的消息
   */
  async function loadSessionMessages(sessionId, limit = 50) {
    try {
      console.log(`📬 加载会话消息: ${sessionId}`);

      const response = await chatAPI.getSessionMessages(sessionId, limit);

      if (response.status === "success") {
        messages.value = response.messages;
        console.log(`✅ 加载了 ${messages.value.length} 条消息`);
      }
    } catch (error) {
      console.error("❌ 加载会话消息失败:", error);
      messages.value = [];
    }
  }

  /**
   * 切换会话
   */
  async function switchSession(sessionId) {
    try {
      console.log(`🔄 切换到会话: ${sessionId}`);

      const response = await chatAPI.activateSession(sessionId);

      if (response.status === "success") {
        // ⭐ 更新当前会话
        currentSession.value = response.session;
        this.sessionId = response.session.session_id;

        // ⭐ 更新消息列表
        messages.value = response.messages;

        // ⭐ 更新会话列表中的 is_active 状态
        sessions.value = sessions.value.map((s) => ({
          ...s,
          is_active: s.session_id === sessionId,
        }));

        console.log(`✅ 已切换到会话: ${response.session.title}`);
      }
    } catch (error) {
      console.error("❌ 切换会话失败:", error);
      throw error;
    }
  }

  /**
   * 创建新会话（替代原来的 clearContext）
   */
  async function createNewSession() {
    try {
      console.log("📝 创建新会话...");

      const response = await chatAPI.createNewSession();

      if (response.status === "success") {
        // ⭐ 更新当前会话
        currentSession.value = response.session;
        sessionId.value = response.session.session_id;

        // ⭐ 清空消息列表
        messages.value = [];
        currentReply.value = "";

        // ⭐ 更新会话列表
        sessions.value = sessions.value.map((s) => ({
          ...s,
          is_active: false,
        }));
        sessions.value.unshift(response.session); // 添加到列表开头

        console.log(`✅ 新会话已创建: ${response.session.session_id}`);
      }
    } catch (error) {
      console.error("❌ 创建新会话失败:", error);
      throw error;
    }
  }

  /**
   * 删除会话
   */
  async function deleteSession(sessionIdToDelete) {
    try {
      console.log(`🗑️ 删除会话: ${sessionIdToDelete}`);

      const response = await chatAPI.deleteSession(sessionIdToDelete);

      if (response.status === "success") {
        // ⭐ 从列表中移除
        sessions.value = sessions.value.filter(
          (s) => s.session_id !== sessionIdToDelete,
        );

        console.log("✅ 会话已删除");
      }
    } catch (error) {
      console.error("❌ 删除会话失败:", error);
      throw error;
    }
  }

  // ========== ⭐ 修改：发送消息 ⭐ ==========

  /**
   * 发送消息
   */
  async function sendMessageStream(userMessage) {
    if (!userMessage.trim()) return;

    // 确保有当前会话
    if (!currentSession.value) {
      console.log("📝 没有活跃会话，创建新会话...");
      await createNewSession();
    }

    // ⭐ 立即显示用户消息（使用 ISO 字符串格式）
    const userMsg = {
      role: "user",
      content: userMessage,
      created_at: new Date().toISOString(), // ⭐ ISO 字符串格式
    };
    messages.value.push(userMsg);

    try {
      isStreaming.value = true;
      currentReply.value = "";

      // ⭐ 准备助手消息占位（使用 ISO 字符串格式）
      const assistantMsg = {
        role: "assistant",
        content: "",
        created_at: new Date().toISOString(), // ⭐ ISO 字符串格式
      };
      messages.value.push(assistantMsg);

      const assistantIndex = messages.value.length - 1;

      await chatAPI.sendMessageStream(
        userMessage,
        sessionId.value,
        maxContextLength.value,
        // onChunk
        (chunk) => {
          currentReply.value += chunk;
          messages.value[assistantIndex].content = currentReply.value;
        },
        // onDone
        (returnedSessionId) => {
          console.log("✅ 流式响应完成");

          if (returnedSessionId && returnedSessionId !== sessionId.value) {
            sessionId.value = returnedSessionId;
            if (currentSession.value) {
              currentSession.value.session_id = returnedSessionId;
            }
          }

          isStreaming.value = false;
          currentReply.value = "";

          // 重新加载会话列表
          loadSessions();
        },
        // onError
        (error) => {
          console.error("❌ 流式响应错误:", error);
          isStreaming.value = false;
          currentReply.value = "";

          messages.value[assistantIndex].content =
            "抱歉，发生了错误：" + error.message;
        },
      );
    } catch (error) {
      console.error("❌ 发送消息失败:", error);
      isStreaming.value = false;
      currentReply.value = "";
    }
  }

  /**
   * 清除当前对话（已废弃，使用 createNewSession 代替）
   */
  async function clearContext() {
    await createNewSession();
  }

  /**
   * 重置 Store（登出时调用）
   */
  function resetStore() {
    messages.value = [];
    sessions.value = [];
    currentSession.value = null;
    sessionId.value = null;
    isStreaming.value = false;
    currentReply.value = "";
    console.log("🔄 Chat Store 已重置");
  }

  // ========== 导出 ==========
  return {
    // 状态
    messages,
    sessions,
    currentSession,
    isStreaming,
    currentReply,
    sessionId,
    maxContextLength,
    isLoadingSessions,

    // 计算属性
    currentContextLength,
    hasMessages,
    activeSessions,
    archivedSessions,

    // 方法
    loadSessions,
    loadSessionMessages,
    switchSession,
    createNewSession,
    deleteSession,
    sendMessageStream,
    clearContext,
    resetStore,
  };
});
