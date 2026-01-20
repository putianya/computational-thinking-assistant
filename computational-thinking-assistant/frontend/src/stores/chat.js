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
   * @param {string} targetSessionId - 目标会话ID
   */
  async function switchSession(targetSessionId) {
    try {
      console.log("🔄 切换到会话:", targetSessionId);

      // 1. 调用 API 切换会话
      const result = await chatAPI.activateSession(targetSessionId);

      // 2. ⭐ 检查返回数据
      if (!result || !result.session) {
        console.error("❌ 切换会话失败: 返回数据无效", result);
        throw new Error("切换会话失败：服务器返回数据无效");
      }

      // 3. 更新当前会话信息
      currentSession.value = result.session;
      sessionId.value = result.session.session_id; // ⭐ 使用 session_id 而不是 sessionId

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

      if (result.status === 'success') {
        console.log('✅ 服务器删除成功');

        // 2. 从本地列表中移除
        sessions.value = sessions.value.filter(s => s.session_id !== sessionIdToDelete);
        console.log(`   删除后剩余会话数: ${sessions.value.length}`);

        // 3. 如果删除的是当前会话，需要切换或清空
        if (isCurrentSession) {
          console.log('⚠️ 删除的是当前会话');

          // 3.1 如果还有其他会话，切换到第一个
          if (sessions.value.length > 0) {
            console.log('🔄 切换到下一个会话');
            const nextSession = sessions.value[0];
            
            try {
              await switchSession(nextSession.session_id);
            } catch (switchError) {
              console.error('❌ 切换会话失败:', switchError);
              
              // 手动设置当前会话
              currentSession.value = nextSession;
              sessionId.value = nextSession.session_id;
              
              // 重新加载消息
              try {
                const msgs = await chatAPI.getSessionMessages(nextSession.session_id);
                messages.value = msgs;
              } catch (msgError) {
                console.error('❌ 加载消息失败:', msgError);
                messages.value = [];
              }
            }
          }
          // ⭐⭐⭐ 修改：删除所有会话后，显示空白页（不自动创建新会话）⭐⭐⭐
          else {
            console.log('📭 所有会话已删除，显示空白页');
            
            // 清空状态
            currentSession.value = null;
            sessionId.value = null;
            messages.value = [];
            currentReply.value = '';
            
            // ⭐ 提示用户点击"新对话"按钮创建会话
            console.log('💡 提示：点击"新对话"按钮创建新会话');
          }
        } else {
          console.log('✅ 删除的是其他会话，无需切换');
        }

        return true;
      } else {
        throw new Error(result.message || '删除失败');
      }
    } catch (error) {
      console.error('❌ 删除失败:', error);
      return false;
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
