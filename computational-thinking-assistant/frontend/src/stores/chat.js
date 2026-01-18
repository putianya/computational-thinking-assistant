import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { chatAPI } from "../api/chat";

export const useChatStore = defineStore("chat", () => {
  const messages = ref([
    {
      type: "bot",
      content:
        "你好！我是计算思维课程助手,可以帮你:\n• 解答 C 语言编程问题\n• 分析代码错误\n• 讲解数据结构和算法\n有什么可以帮你的吗?",
      timestamp: new Date(),
    },
  ]);

  const isLoading = ref(false);
  const isStreaming = ref(false);
  const sessionId = ref(null);
  const contextInfo = ref({ history_length: 0, max_context: 10 });
  const streamingMessageIndex = ref(-1);

  // ⭐ 计算属性：是否有上下文
  const hasContext = computed(() => contextInfo.value.history_length > 0);

  // ⭐ 计算属性：上下文使用率
  const contextUsage = computed(() => {
    const { history_length, max_context } = contextInfo.value;
    return Math.min((history_length / max_context) * 100, 100);
  });

  // ⭐⭐⭐ 发送消息（流式） ⭐⭐⭐
  async function sendMessageStream(userMessage) {
    if (!userMessage.trim() || isLoading.value || isStreaming.value) return;

    // 1️⃣ 添加用户消息
    messages.value.push({
      type: "user",
      content: userMessage,
      timestamp: new Date(),
    });

    // 2️⃣ 添加空的 bot 消息（用于流式填充）
    messages.value.push({
      type: "bot",
      content: "",
      timestamp: new Date(),
      isStreaming: true, // ⭐ 标记为流式
    });

    streamingMessageIndex.value = messages.value.length - 1;
    isStreaming.value = true;
    isLoading.value = true;

    try {
      // 3️⃣ 调用流式 API
      await chatAPI.sendMessageStream(
        userMessage,
        sessionId.value,

        // ⭐ onChunk: 接收到内容块
        (chunk) => {
          const msgIndex = streamingMessageIndex.value;
          if (msgIndex >= 0 && messages.value[msgIndex]) {
            messages.value[msgIndex].content += chunk;
          }
        },

        // ⭐ onDone: 完成
        (newSessionId) => {
          if (!sessionId.value) {
            sessionId.value = newSessionId;
          }

          const msgIndex = streamingMessageIndex.value;
          if (msgIndex >= 0 && messages.value[msgIndex]) {
            messages.value[msgIndex].isStreaming = false;
          }

          isStreaming.value = false;
          isLoading.value = false;
          streamingMessageIndex.value = -1;

          // ⭐ 更新上下文信息
          updateContextInfo();
        },

        // ⭐ onError: 错误处理
        (error) => {
          const msgIndex = streamingMessageIndex.value;
          if (msgIndex >= 0) {
            messages.value[msgIndex].content = `❌ 发送失败: ${error.message}`;
            messages.value[msgIndex].isStreaming = false;
          }

          isStreaming.value = false;
          isLoading.value = false;
          streamingMessageIndex.value = -1;
        },
      );
    } catch (error) {
      console.error("发送流式消息失败:", error);
      isStreaming.value = false;
      isLoading.value = false;
    }
  }

  // ⭐ 更新上下文信息
  async function updateContextInfo() {
    if (!sessionId.value) return;

    try {
      const response = await chatAPI.getContextInfo(sessionId.value);
      if (response.status === "success") {
        contextInfo.value = {
          history_length: response.history_length,
          max_context: response.max_context,
        };
      }
    } catch (error) {
      console.error("获取上下文信息失败:", error);
    }
  }

  // ⭐ 清除上下文
  async function clearContext() {
    if (!sessionId.value) return;

    try {
      const response = await chatAPI.clearContext(sessionId.value);
      if (response.status === "success") {
        // 重置状态
        messages.value = [
          {
            type: "bot",
            content: "上下文已清除！让我们开始新的对话吧 😊",
            timestamp: new Date(),
          },
        ];
        contextInfo.value = { history_length: 0, max_context: 10 };
        return true;
      }
    } catch (error) {
      console.error("清除上下文失败:", error);
      return false;
    }
  }

  // ⭐ 开始新会话
  function startNewSession() {
    sessionId.value = null;
    messages.value = [
      {
        type: "bot",
        content:
          "你好！我是计算思维课程助手,可以帮你:\n• 解答 C 语言编程问题\n• 分析代码错误\n• 讲解数据结构和算法\n有什么可以帮你的吗?",
        timestamp: new Date(),
      },
    ];
    contextInfo.value = { history_length: 0, max_context: 10 };
  }

  return {
    messages,
    isLoading,
    isStreaming,
    sessionId,
    contextInfo,
    hasContext,
    contextUsage,
    sendMessageStream,
    clearContext,
    startNewSession,
    updateContextInfo,
  };
});
