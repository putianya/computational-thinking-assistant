<template>
  <div class="chat-view">
    <!-- 左侧：会话列表 -->
    <div class="chat-sidebar">
      <SessionList />
    </div>

    <!-- 右侧：聊天区域 -->
    <div class="chat-main">
      <!-- 聊天头部 -->
      <div class="chat-header">
        <div class="header-left">
          <h2>💬 AI 智能对话</h2>
          <p v-if="chatStore.currentSession">
            {{ chatStore.currentSession.title }}
          </p>
          <p v-else>与 AI 助手交流，获取编程学习帮助</p>
        </div>

        <!-- 上下文信息 -->
        <div class="context-info" v-if="chatStore.hasMessages">
          <div class="context-badge">
            <span class="badge-icon">💬</span>
            <span>{{ chatStore.currentContextLength }} 轮对话</span>
          </div>

          <button @click="handleClearContext" class="clear-context-btn">
            🗑️ 新对话
          </button>
        </div>
      </div>

      <!-- 聊天容器 -->
      <div class="chat-container">
        <div class="chat-messages" ref="messagesContainer">
          <!-- 空状态 -->
          <div v-if="chatStore.messages.length === 0" class="empty-state">
            <div class="empty-icon">🤖</div>
            <h3>开始对话</h3>
            <p>向 AI 助手提问关于编程的任何问题</p>
          </div>

          <!-- 消息列表 -->
          <ChatMessage
            v-for="(msg, index) in chatStore.messages"
            :key="msg.id || index"
            :type="msg.role"
            :content="msg.content"
            :timestamp="msg.created_at"
            :is-streaming="
              chatStore.isStreaming && index === chatStore.messages.length - 1
            "
            @continue="handleContinue"
          />
        </div>

        <ChatInput />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from "vue";
import { useChatStore } from "../stores/chat";
import SessionList from "./SessionList.vue";
import ChatMessage from "./ChatMessage.vue";
import ChatInput from "./ChatInput.vue";

const chatStore = useChatStore();
const messagesContainer = ref(null);

onMounted(async () => {
  console.log("📋 ChatView 挂载，加载会话列表...");
  await chatStore.loadSessions();
});

// 监听器
watch(
  () => chatStore.messages.length,
  () => {
    nextTick(() => {
      scrollToBottom();
    });
  },
);

watch(
  () => chatStore.messages.map((m) => m.content).join(""),
  () => {
    nextTick(() => {
      if (chatStore.isStreaming) {
        scrollToBottom();
      }
    });
  },
  { deep: true },
);

watch(
  () => chatStore.currentSession,
  () => {
    nextTick(() => {
      scrollToBottom();
    });
  },
);

function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}

async function handleContinue() {
  console.log("🔄 触发续写请求");
  try {
    await chatStore.continueLastMessage();
    console.log("✅ 续写请求已发送");
  } catch (error) {
    console.error("❌ 续写失败:", error);
    alert("续写失败，请重试");
  }
}

async function handleClearContext() {
  if (
    confirm(
      "确定要开始新对话吗？\n当前对话将被归档，您可以在左侧会话列表中查看。",
    )
  ) {
    try {
      await chatStore.createNewSession();
      console.log("✅ 新对话已创建");
    } catch (error) {
      console.error("❌ 创建新对话失败:", error);
      alert("创建新对话失败，请重试");
    }
  }
}
</script>

<style scoped>
.chat-view {
  display: flex;
  height: 100%;
  background: #f0f2f5;
  overflow: hidden; /* ⭐ 关键：防止整体滚动 */
}

/* 左侧会话列表 */
.chat-sidebar {
  width: 280px;
  background: white;
  border-right: 1px solid #e0e0e0;
  flex-shrink: 0;
  overflow-y: auto;
}

/* 右侧聊天区域 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  margin: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden; /* ⭐ 关键：防止内容溢出 */
}

/* 聊天头部 */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  gap: 20px;
  flex-shrink: 0;
}

.header-left h2 {
  font-size: 22px;
  margin: 0 0 6px 0;
  font-weight: 600;
}

.header-left p {
  margin: 0;
  font-size: 14px;
  opacity: 0.9;
}

.context-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border-radius: 8px;
}

.context-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
}

.clear-context-btn {
  padding: 6px 14px;
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  color: white;
  transition: all 0.2s ease;
}

.clear-context-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

/* 聊天容器 */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
  overflow: hidden; /* ⭐ 关键：子元素自己处理滚动 */
}

.chat-messages {
  flex: 1;
  padding: 24px;
  overflow-y: auto; /* ⭐ 关键：只有消息区域可滚动 */
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  text-align: center;
  padding: 40px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
  opacity: 0.5;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  font-size: 20px;
  color: #666;
  font-weight: 500;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
  color: #999;
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar {
  width: 8px;
}

.chat-messages::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #d0d0d0;
  border-radius: 4px;
}

.chat-messages::-webkit-scrollbar-thumb:hover {
  background: #b0b0b0;
}

/* 响应式 */
@media (max-width: 768px) {
  .chat-view {
    flex-direction: column;
  }

  .chat-sidebar {
    width: 100%;
    height: 200px;
    border-right: none;
    border-bottom: 1px solid #e0e0e0;
  }

  .chat-main {
    margin: 0;
    border-radius: 0;
  }
}
</style>
