<template>
  <div class="chat-window">
    <!-- 左侧：会话列表 -->
    <div class="sidebar">
      <SessionList />
    </div>

    <!-- 右侧：聊天区域 -->
    <div class="chat-section">
      <div class="chat-header">
        <div class="header-left">
          <h2>💬 AI 智能对话</h2>
          <p v-if="chatStore.currentSession">
            {{ chatStore.currentSession.title || "新对话" }}
          </p>
          <p v-else>与 AI 助手交流,获取编程学习帮助</p>
        </div>

        <!-- ⭐⭐⭐ 修改：上下文信息显示 ⭐⭐⭐ -->
        <div class="context-info" v-if="chatStore.hasMessages">
          <div class="context-badge">
            <span class="badge-icon">🧠</span>
            <span class="badge-text">
              <!-- ⭐ 修改：显示对话轮数，无上限 -->
              上下文: {{ chatStore.currentContextLength }}
            </span>
          </div>

          <!-- ❌ 删除：进度条（不再需要） -->
          <!-- <div class="context-bar">
            <div
              class="context-fill"
              :style="{ width: contextUsagePercent + '%' }"
              :class="{ warning: contextUsagePercent > 80 }"
            ></div>
          </div> -->

          <button
            class="clear-context-btn"
            @click="handleClearContext"
            title="清除上下文（创建新会话）"
          >
            🗑️ 新对话
          </button>
        </div>
      </div>

      <div class="chat-container">
        <div class="chat-messages" ref="messagesContainer">
          <!-- 空状态提示 -->
          <div v-if="chatStore.messages.length === 0" class="empty-state">
            <div class="empty-icon">💬</div>
            <h3>开始新对话</h3>
            <p>在下方输入框输入消息，开始与 AI 助手交流</p>
          </div>

          <!-- ⭐ 消息列表（修复 key） -->
          <ChatMessage
            v-for="(msg, index) in chatStore.messages"
            :key="`${msg.created_at}-${index}`"
            :type="msg.role"
            :content="msg.content"
            :timestamp="msg.created_at"
            :isStreaming="
              index === chatStore.messages.length - 1 && chatStore.isStreaming
            "
          />
        </div>

        <ChatInput />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from "vue";
import { useChatStore } from "../stores/chat";
import SessionList from "./SessionList.vue";
import ChatMessage from "./ChatMessage.vue";
import ChatInput from "./ChatInput.vue";

const chatStore = useChatStore();
const messagesContainer = ref(null);

// ❌ 删除：上下文使用百分比计算
// const contextUsagePercent = computed(() => {
//   if (chatStore.maxContextLength === 0) return 0;
//   return Math.min(
//     100,
//     (chatStore.currentContextLength / chatStore.maxContextLength) * 100,
//   );
// });

// ========== 生命周期 ==========

onMounted(async () => {
  // ⭐ 组件挂载时加载会话列表
  console.log("📋 ChatWindow 挂载，加载会话列表...");
  await chatStore.loadSessions();
});

// ========== 监听器 ==========

// 自动滚动到底部（新消息时）
watch(
  () => chatStore.messages.length,
  () => {
    nextTick(() => {
      scrollToBottom();
    });
  },
);

// ⭐ 监听消息内容变化（流式输出时也滚动）
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

// ⭐ 监听当前会话变化（切换会话时滚动）
watch(
  () => chatStore.currentSession,
  () => {
    nextTick(() => {
      scrollToBottom();
    });
  },
);

// ========== 方法 ==========

/**
 * 滚动到底部
 */
function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}

/**
 * ⭐ 清除上下文处理（创建新会话）
 */
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
/* ========== 整体布局 ========== */
.chat-window {
  display: flex;
  height: 100vh;
  background: #f0f2f5;
}

/* ========== 左侧：会话列表 ========== */
.sidebar {
  width: 280px;
  background: white;
  border-right: 1px solid #e0e0e0;
  flex-shrink: 0;
  overflow: hidden;
}

/* ========== 右侧：聊天区域 ========== */
.chat-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  margin: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

/* ========== 聊天头部 ========== */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  gap: 20px;
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

/* ========== 上下文信息 ========== */
.context-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.context-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: white;
}

.badge-icon {
  font-size: 18px;
}

/* ❌ 删除：进度条样式（不再需要） */
/* .context-bar { ... } */
/* .context-fill { ... } */
/* .context-fill.warning { ... } */

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
  white-space: nowrap;
}

.clear-context-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.4);
  transform: translateY(-1px);
}

/* ========== 聊天容器 ========== */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ========== 空状态 ========== */
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
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
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

/* ========== 滚动条样式 ========== */
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

/* ========== 响应式设计 ========== */
@media (max-width: 768px) {
  .chat-window {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    height: 200px;
    border-right: none;
    border-bottom: 1px solid #e0e0e0;
  }

  .chat-section {
    margin: 0;
    border-radius: 0;
  }

  .chat-header {
    flex-direction: column;
    gap: 12px;
  }

  .context-info {
    width: 100%;
    justify-content: space-between;
  }

  .context-bar {
    flex: 1;
    max-width: 120px;
  }
}
</style>
