import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { chatAPI } from "../api/chat";

export const useChatStore = defineStore("chat", () => {
  // ========== 状态 ==========
  const messages = ref([]);
  const isStreaming = ref(false);
  const currentReply = ref("");

  const sessions = ref([]);
  const currentSession = ref(null);
  const isLoadingSessions = ref(false);

  const sessionId = ref(null);

  // ========== 计算属性 ==========

  // 对话轮数 = 消息数 / 2
  const currentContextLength = computed(() => {
    return Math.floor(messages.value.length / 2);
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

  // ========== 会话管理方法 ==========

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

        // 找到当前活跃会话
        const activeSession = sessions.value.find((s) => s.is_active);

        if (activeSession) {
          currentSession.value = activeSession;
          sessionId.value = activeSession.session_id;

          // 加载该会话的消息
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
   * @param {string} targetSessionId - 目标会话ID
   */
  async function switchSession(targetSessionId) {
    try {
      console.log("🔄 切换到会话:", targetSessionId);

      // 1. 调用 API 切换会话
      const result = await chatAPI.activateSession(targetSessionId);

      // 2. 检查返回数据
      if (!result || !result.session) {
        console.error("❌ 切换会话失败: 返回数据无效", result);
        throw new Error("切换会话失败：服务器返回数据无效");
      }

      // 3. 更新当前会话信息
      currentSession.value = result.session;
      sessionId.value = result.session.session_id;

      // 4. 更新消息列表
      messages.value = result.messages || [];

      // 5. 清空当前回复
      currentReply.value = "";

      // 6. 更新会话列表中的 is_active 状态
      sessions.value = sessions.value.map((s) => ({
        ...s,
        is_active: s.session_id === targetSessionId,
      }));

      console.log("✅ 会话切换成功");
      console.log("   当前会话:", currentSession.value);
      console.log("   消息数量:", messages.value.length);

      return true;
    } catch (error) {
      console.error("❌ 切换会话失败:", error);
      throw error;
    }
  }

  /**
   * 创建新会话
   */
  async function createNewSession() {
    try {
      console.log("📝 创建新会话...");

      const response = await chatAPI.createNewSession();

      if (response.status === "success") {
        // 更新当前会话
        currentSession.value = response.session;
        sessionId.value = response.session.session_id;

        // 清空消息列表
        messages.value = [];
        currentReply.value = "";

        // 更新会话列表
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
   * @param {string} sessionIdToDelete - 要删除的会话 ID
   * @returns {Promise<boolean>} 删除是否成功
   */
  async function deleteSession(sessionIdToDelete) {
    try {
      console.log(`🗑️ 删除会话: ${sessionIdToDelete}`);

      const isCurrentSession = sessionId.value === sessionIdToDelete;
      console.log(`   是否删除当前会话: ${isCurrentSession}`);

      // 1. 调用 API 删除
      const result = await chatAPI.deleteSession(sessionIdToDelete);

      if (result.status === "success") {
        console.log("✅ 服务器删除成功");

        // 2. 从本地列表中移除
        sessions.value = sessions.value.filter(
          (s) => s.session_id !== sessionIdToDelete,
        );
        console.log(`   删除后剩余会话数: ${sessions.value.length}`);

        // 3. 如果删除的是当前会话，需要切换或清空
        if (isCurrentSession) {
          console.log("⚠️ 删除的是当前会话");

          // 3.1 如果还有其他会话，切换到第一个
          if (sessions.value.length > 0) {
            console.log("🔄 切换到下一个会话");
            const nextSession = sessions.value[0];

            try {
              await switchSession(nextSession.session_id);
            } catch (switchError) {
              console.error("❌ 切换会话失败:", switchError);

              // 手动设置当前会话
              currentSession.value = nextSession;
              sessionId.value = nextSession.session_id;

              // 重新加载消息
              try {
                const msgs = await chatAPI.getSessionMessages(
                  nextSession.session_id,
                );
                messages.value = msgs;
              } catch (msgError) {
                console.error("❌ 加载消息失败:", msgError);
                messages.value = [];
              }
            }
          }
          // 删除所有会话后，显示空白页
          else {
            console.log("📭 所有会话已删除，显示空白页");

            // 清空状态
            currentSession.value = null;
            sessionId.value = null;
            messages.value = [];
            currentReply.value = "";

            console.log('💡 提示：点击"新对话"按钮创建新会话');
          }
        } else {
          console.log("✅ 删除的是其他会话，无需切换");
        }

        return true;
      } else {
        throw new Error(result.message || "删除失败");
      }
    } catch (error) {
      console.error("❌ 删除失败:", error);
      return false;
    }
  }

  /**
   * 重命名会话
   * @param {string} sessionId - 会话 ID
   * @param {string} newTitle - 新标题
   */
  async function renameSession(sessionId, newTitle) {
    try {
      console.log(`✏️ 重命名会话: ${sessionId} -> ${newTitle}`);

      const response = await chatAPI.renameSession(sessionId, newTitle);

      if (response.status === "success") {
        // 更新本地会话列表
        const sessionIndex = sessions.value.findIndex(
          (s) => s.session_id === sessionId,
        );

        if (sessionIndex !== -1) {
          sessions.value[sessionIndex].title = newTitle;
        }

        // 如果是当前会话，也更新
        if (
          currentSession.value &&
          currentSession.value.session_id === sessionId
        ) {
          currentSession.value.title = newTitle;
        }

        console.log("✅ 重命名成功");
        return true;
      } else {
        console.error("❌ 重命名失败:", response.message);
        return false;
      }
    } catch (error) {
      console.error("❌ 重命名会话失败:", error);
      throw error;
    }
  }

  // ========== 消息发送方法 ==========

  /**
   * ⭐⭐⭐ 发送流式消息（修复版）⭐⭐⭐
   */
  async function sendMessageStream(message) {
    if (!message.trim()) return;

    try {
      console.log(`💬 发送消息: ${message}`);
      console.log(`📍 当前会话: ${sessionId.value}`);

      // 1. 立即添加用户消息到界面
      const userMessage = {
        id: Date.now(),
        role: "user",
        content: message,
        created_at: new Date().toISOString(),
      };
      messages.value.push(userMessage);

      // 2. 添加 AI 消息占位符
      const aiMessageIndex = messages.value.length; // ⭐ 记录索引
      const aiMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content: "",
        created_at: new Date().toISOString(),
      };
      messages.value.push(aiMessage);

      // 3. 设置流式状态
      isStreaming.value = true;
      currentReply.value = "";

      // 4. 调用 API（流式输出）
      await chatAPI.sendMessageStream(
        message,
        sessionId.value,
        null,

        // ⭐⭐⭐ onChunk：每收到一块内容，立即更新 ⭐⭐⭐
        (chunk) => {
          currentReply.value += chunk;
          // ⭐ 直接修改数组中的对象，触发响应式更新
          messages.value[aiMessageIndex].content = currentReply.value;
        },

        // onDone：流式结束
        async (newSessionId) => {
          console.log(`✅ 流式输出完成，会话ID: ${newSessionId}`);

          // ⭐⭐⭐ 如果是新创建的会话，需要重新加载会话列表 ⭐⭐⭐
          if (newSessionId && newSessionId !== sessionId.value) {
            sessionId.value = newSessionId;
            console.log(`📍 更新会话ID: ${newSessionId}`);

            // ⭐ 重新加载会话列表，显示新创建的会话
            console.log("🔄 重新加载会话列表...");
            await loadSessions();
            console.log("✅ 会话列表已更新");
          }

          isStreaming.value = false;
          currentReply.value = "";
        },

        // onError：错误处理
        (error) => {
          console.error("❌ 流式输出错误:", error);
          messages.value[aiMessageIndex].content =
            `抱歉，发生错误：${error.message}`;
          isStreaming.value = false;
        },
      );
    } catch (error) {
      console.error("❌ 发送消息失败:", error);
      isStreaming.value = false;
      currentReply.value = "";
      throw error;
    }
  }

  /**
   * ⭐⭐⭐ 新增：续写上次回答 ⭐⭐⭐
   */
  async function continueLastMessage() {
    console.log("🔄 Store: 开始续写请求");

    // 1. 检查是否有会话
    if (!sessionId.value) {
      console.warn("⚠️  无当前会话，无法续写");
      throw new Error("请先开始一个对话");
    }

    // 2. 检查是否有消息
    if (messages.value.length === 0) {
      console.warn("⚠️  无历史消息，无法续写");
      throw new Error("没有可续写的内容");
    }

    // 3. 检查是否正在流式输出
    if (isStreaming.value) {
      console.warn("⚠️  正在生成中，请稍候");
      return;
    }

    // 4. 发送"继续"消息（复用 sendMessageStream 方法）
    console.log('📤 发送续写指令: "继续"');
    await sendMessageStream("继续");
  }

  // ========== 工具方法 ==========

  /**
   * 清除上下文（实际是创建新会话）
   */
  async function clearContext() {
    try {
      console.log("🗑️ 清除上下文（创建新会话）...");

      // 调用创建新会话 API
      await createNewSession();

      console.log("✅ 上下文已清除");
    } catch (error) {
      console.error("❌ 清除上下文失败:", error);
      throw error;
    }
  }

  /**
   * 重置整个 Store（登出时调用）
   */
  function resetStore() {
    console.log("🔄 重置聊天 Store...");

    // 清空所有状态
    messages.value = [];
    sessions.value = [];
    currentSession.value = null;
    sessionId.value = null;
    isStreaming.value = false;
    currentReply.value = "";
    isLoadingSessions.value = false;

    console.log("✅ 聊天 Store 已重置");
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
    renameSession,
    sendMessageStream,
    continueLastMessage,
    clearContext,
    resetStore,
  };
});
