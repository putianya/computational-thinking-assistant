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

  // ⭐⭐⭐ 新增：中断标志 ⭐⭐⭐
  const shouldAbortStream = ref(false);

  // ⭐⭐⭐ 新增：暂停期间的缓冲队列 ⭐⭐⭐
  const pendingChunks = ref([]); // 存储暂停期间收到的chunk

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

      // ⭐ 重置状态
      shouldAbortStream.value = false;
      pendingChunks.value = []; // ⭐ 清空缓冲队列

      // 1. 立即添加用户消息到界面
      const userMessage = {
        id: Date.now(),
        role: "user",
        content: message,
        created_at: new Date().toISOString(),
      };
      messages.value.push(userMessage);

      // 2. 添加 AI 消息占位符
      const aiMessageIndex = messages.value.length;
      const aiMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content: "",
        created_at: new Date().toISOString(),
        rag_meta: null,
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
        (chunk) => {
          // ⭐⭐⭐ 修改：根据暂停状态决定处理方式 ⭐⭐⭐
          if (shouldAbortStream.value) {
            // 暂停模式：将chunk存入缓冲队列
            console.log(
              `📦 chunk已缓冲（队列长度: ${pendingChunks.value.length + 1}）`,
            );
            pendingChunks.value.push(chunk);
            return;
          }

          // ⭐ 检查消息索引是否仍然有效
          if (aiMessageIndex >= messages.value.length) {
            console.warn("⚠️ 消息索引失效，停止更新UI");
            shouldAbortStream.value = true;
            return;
          }

          // ⭐ 检查消息类型是否正确
          if (messages.value[aiMessageIndex].role !== "assistant") {
            console.warn("⚠️ 消息类型不匹配，停止更新UI");
            shouldAbortStream.value = true;
            return;
          }

          // ✅ 正常模式：实时更新UI
          currentReply.value += chunk;
          messages.value[aiMessageIndex].content = currentReply.value;
        },
        async (newSessionId, fullContent) => {
          // ⭐⭐⭐ onDone: 即使暂停也执行完成逻辑 ⭐⭐⭐
          console.log("✅ 流式输出完成（后端）");
          console.log(
            `📊 完整内容长度: ${fullContent?.length || currentReply.value.length}`,
          );

          // ⭐ 如果是暂停状态，使用后端传来的完整内容
          if (shouldAbortStream.value && fullContent) {
            console.log("🔄 当前是暂停状态，使用后端完整内容");

            // 计算已显示的内容长度
            const displayedLength = currentReply.value.length;

            // 提取未显示的部分
            const remainingContent = fullContent.substring(displayedLength);

            if (remainingContent) {
              console.log(`📦 未显示内容长度: ${remainingContent.length}`);

              // ⭐⭐⭐ 将剩余内容拆分成chunk存入缓冲队列 ⭐⭐⭐
              const chunkSize = 5; // 每个chunk 5个字符
              for (let i = 0; i < remainingContent.length; i += chunkSize) {
                pendingChunks.value.push(
                  remainingContent.substring(i, i + chunkSize),
                );
              }

              console.log(
                `📦 缓冲队列已填充: ${pendingChunks.value.length} 个chunk`,
              );
            }

            // ⭐ 确保消息对象存在且使用完整内容
            if (aiMessageIndex < messages.value.length) {
              messages.value[aiMessageIndex].content = fullContent;
            }
          }

          // 重置状态
          isStreaming.value = false;
          shouldAbortStream.value = false;

          // 处理会话ID更新
          if (newSessionId && newSessionId !== sessionId.value) {
            console.log(`📍 会话ID更新: ${sessionId.value} -> ${newSessionId}`);
            sessionId.value = newSessionId;

            await loadSessions();

            const newSession = sessions.value.find(
              (s) => s.session_id === newSessionId,
            );
            if (newSession) {
              currentSession.value = newSession;
            }
          }
        },
        (error) => {
          // onError
          console.error("❌ 流式输出错误:", error);
          isStreaming.value = false;
          currentReply.value = "";
          shouldAbortStream.value = false;
          pendingChunks.value = []; // ⭐ 清空缓冲队列

          if (aiMessageIndex < messages.value.length) {
            messages.value[aiMessageIndex].content =
              "抱歉，回复时出现错误，请重试。";
          }
        },
        (meta) => {
          if (aiMessageIndex < messages.value.length) {
            messages.value[aiMessageIndex].rag_meta = meta;
          }
          console.log(
            `🧾 本轮摘要: mode=${meta.mode}, confidence=${meta.confidence_mode}, refs=${(meta.referenced_chunk_ids || []).length}`,
          );
        },
      );
    } catch (error) {
      console.error("❌ 发送消息失败:", error);
      isStreaming.value = false;
      currentReply.value = "";
      shouldAbortStream.value = false;
      pendingChunks.value = []; // ⭐ 清空缓冲队列
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

  // frontend/src/stores/chat.js

  // ⭐⭐⭐ 修复：只中断前端渲染，不中断后端流式输出 ⭐⭐⭐
  function abortCurrentStream() {
    console.log("🛑 中断前端流式显示（后端继续运行）");

    // ⭐ 只设置前端标志，不中断网络请求
    shouldAbortStream.value = true;
    // ⚠️ 不清空 currentReply，保留已显示的内容
    console.log("✅ 已显示内容保留:", currentReply.value.substring(0, 50));
    console.log("📦 开启缓冲队列，后续chunk将存入队列");
  }

  // ⭐⭐⭐ 新增：恢复流式显示（追赶进度）⭐⭐⭐
  function resumeStream() {
    if (!shouldAbortStream.value) {
      console.log("⚠️ 流式输出未暂停，无需恢复");
      return;
    }

    console.log("▶️ 恢复流式显示");
    console.log(`📦 缓冲队列中有 ${pendingChunks.value.length} 个待渲染chunk`);

    shouldAbortStream.value = false;

    // ⭐⭐⭐ 快速追赶：逐个渲染缓冲的chunk ⭐⭐⭐
    if (pendingChunks.value.length > 0) {
      console.log("🚀 开始追赶进度...");

      let chunkIndex = 0;
      const catchUpInterval = setInterval(() => {
        if (chunkIndex >= pendingChunks.value.length) {
          clearInterval(catchUpInterval);
          console.log("✅ 进度追上，恢复实时流式输出");
          pendingChunks.value = []; // 清空缓冲队列
          return;
        }

        // 逐个渲染缓冲的chunk（速度可调）
        const chunk = pendingChunks.value[chunkIndex];
        currentReply.value += chunk;

        // 更新对应的消息
        const aiMessageIndex = messages.value.length - 1;
        if (
          aiMessageIndex >= 0 &&
          messages.value[aiMessageIndex].role === "assistant"
        ) {
          messages.value[aiMessageIndex].content = currentReply.value;
        }

        chunkIndex++;
      }, 10); // ⭐ 每10ms渲染一个chunk（快速追赶）
    } else {
      console.log("✅ 无缓冲内容，直接恢复实时输出");
    }
  }

  // ⭐⭐⭐ 修改：sendMessageStream 方法 ⭐⭐⭐
  async function sendMessageStream(message) {
    if (!message.trim()) return;

    try {
      console.log(`💬 发送消息: ${message}`);
      console.log(`📍 当前会话: ${sessionId.value}`);

      // ⭐ 重置状态
      shouldAbortStream.value = false;
      pendingChunks.value = []; // ⭐ 清空缓冲队列

      // 1. 立即添加用户消息到界面
      const userMessage = {
        id: Date.now(),
        role: "user",
        content: message,
        created_at: new Date().toISOString(),
      };
      messages.value.push(userMessage);

      // 2. 添加 AI 消息占位符
      const aiMessageIndex = messages.value.length;
      const aiMessage = {
        id: Date.now() + 1,
        role: "assistant",
        content: "",
        created_at: new Date().toISOString(),
        rag_meta: null,
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
        (chunk) => {
          // ⭐⭐⭐ 修改：根据暂停状态决定处理方式 ⭐⭐⭐
          if (shouldAbortStream.value) {
            // 暂停模式：将chunk存入缓冲队列
            console.log(
              `📦 chunk已缓冲（队列长度: ${pendingChunks.value.length + 1}）`,
            );
            pendingChunks.value.push(chunk);
            return;
          }

          // ⭐ 检查消息索引是否仍然有效
          if (aiMessageIndex >= messages.value.length) {
            console.warn("⚠️ 消息索引失效，停止更新UI");
            shouldAbortStream.value = true;
            return;
          }

          // ⭐ 检查消息类型是否正确
          if (messages.value[aiMessageIndex].role !== "assistant") {
            console.warn("⚠️ 消息类型不匹配，停止更新UI");
            shouldAbortStream.value = true;
            return;
          }

          // ✅ 正常模式：实时更新UI
          currentReply.value += chunk;
          messages.value[aiMessageIndex].content = currentReply.value;
        },
        async (newSessionId, fullContent) => {
          // ⭐⭐⭐ onDone: 即使暂停也执行完成逻辑 ⭐⭐⭐
          console.log("✅ 流式输出完成（后端）");
          console.log(
            `📊 完整内容长度: ${fullContent?.length || currentReply.value.length}`,
          );

          // ⭐ 如果是暂停状态，使用后端传来的完整内容
          if (shouldAbortStream.value && fullContent) {
            console.log("🔄 当前是暂停状态，使用后端完整内容");

            // 计算已显示的内容长度
            const displayedLength = currentReply.value.length;

            // 提取未显示的部分
            const remainingContent = fullContent.substring(displayedLength);

            if (remainingContent) {
              console.log(`📦 未显示内容长度: ${remainingContent.length}`);

              // ⭐⭐⭐ 将剩余内容拆分成chunk存入缓冲队列 ⭐⭐⭐
              const chunkSize = 5; // 每个chunk 5个字符
              for (let i = 0; i < remainingContent.length; i += chunkSize) {
                pendingChunks.value.push(
                  remainingContent.substring(i, i + chunkSize),
                );
              }

              console.log(
                `📦 缓冲队列已填充: ${pendingChunks.value.length} 个chunk`,
              );
            }

            // ⭐ 确保消息对象存在且使用完整内容
            if (aiMessageIndex < messages.value.length) {
              messages.value[aiMessageIndex].content = fullContent;
            }
          }

          // 重置状态
          isStreaming.value = false;
          shouldAbortStream.value = false;

          // 处理会话ID更新
          if (newSessionId && newSessionId !== sessionId.value) {
            console.log(`📍 会话ID更新: ${sessionId.value} -> ${newSessionId}`);
            sessionId.value = newSessionId;

            await loadSessions();

            const newSession = sessions.value.find(
              (s) => s.session_id === newSessionId,
            );
            if (newSession) {
              currentSession.value = newSession;
            }
          }
        },
        (error) => {
          // onError
          console.error("❌ 流式输出错误:", error);
          isStreaming.value = false;
          currentReply.value = "";
          shouldAbortStream.value = false;
          pendingChunks.value = []; // ⭐ 清空缓冲队列

          if (aiMessageIndex < messages.value.length) {
            messages.value[aiMessageIndex].content =
              "抱歉，回复时出现错误，请重试。";
          }
        },
        (meta) => {
          if (aiMessageIndex < messages.value.length) {
            messages.value[aiMessageIndex].rag_meta = meta;
          }
          console.log(
            `🧾 本轮摘要: mode=${meta.mode}, confidence=${meta.confidence_mode}, refs=${(meta.referenced_chunk_ids || []).length}`,
          );
        },
      );
    } catch (error) {
      console.error("❌ 发送消息失败:", error);
      isStreaming.value = false;
      currentReply.value = "";
      shouldAbortStream.value = false;
      pendingChunks.value = []; // ⭐ 清空缓冲队列
      throw error;
    }
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
    shouldAbortStream, // ⭐⭐⭐ 添加这一行！⭐⭐⭐

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
    abortCurrentStream, // ⭐ 确保这个也导出了
    resumeStream,
    pendingChunks,
  };
});
