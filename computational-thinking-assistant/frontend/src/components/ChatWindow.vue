<template>
  <div class="chat-section">
    <div class="chat-header">
      <div class="header-left">
        <h2>💬 AI 智能对话</h2>
        <p>与 AI 助手交流,获取编程学习帮助</p>
      </div>

      <!-- ⭐ 新增：上下文信息显示 -->
      <div class="context-info" v-if="chatStore.hasContext">
        <div class="context-badge">
          <span class="badge-icon">🧠</span>
          <span class="badge-text">
            上下文: {{ chatStore.contextInfo.history_length }}/{{
              chatStore.contextInfo.max_context
            }}
          </span>
        </div>
        <div class="context-bar">
          <div
            class="context-fill"
            :style="{ width: chatStore.contextUsage + '%' }"
            :class="{ warning: chatStore.contextUsage > 80 }"
          ></div>
        </div>
        <button
          class="clear-context-btn"
          @click="handleClearContext"
          title="清除上下文"
        >
          🗑️ 清除上下文
        </button>
      </div>
    </div>

    <div class="chat-container">
      <div class="chat-messages" ref="messagesContainer">
        <ChatMessage
          v-for="(msg, index) in chatStore.messages"
          :key="index"
          :type="msg.type"
          :content="msg.content"
          :timestamp="msg.timestamp"
          :isStreaming="msg.isStreaming"
        />
      </div>

      <ChatInput />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from "vue";
import { useChatStore } from "../stores/chat";
import ChatMessage from "./ChatMessage.vue";
import ChatInput from "./ChatInput.vue";

const chatStore = useChatStore();
const messagesContainer = ref(null);

// 自动滚动到底部
watch(
  () => chatStore.messages.length,
  () => {
    nextTick(() => {
      if (messagesContainer.value) {
        messagesContainer.value.scrollTop =
          messagesContainer.value.scrollHeight;
      }
    });
  }
);

// ⭐ 监听消息内容变化（流式输出时也滚动）
watch(
  () => chatStore.messages.map((m) => m.content).join(""),
  () => {
    nextTick(() => {
      if (messagesContainer.value && chatStore.isStreaming) {
        messagesContainer.value.scrollTop =
          messagesContainer.value.scrollHeight;
      }
    });
  },
  { deep: true }
);

// ⭐ 清除上下文处理
const handleClearContext = async () => {
  if (confirm("确定要清除当前对话上下文吗？这将开始一个全新的对话。")) {
    await chatStore.clearContext();
  }
};
</script>

<style scoped>
.chat-section {
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

/* ⭐ 新增样式 */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
  gap: 20px;
}

.header-left h2 {
  font-size: 20px;
  margin-bottom: 5px;
  color: #333;
}

.header-left p {
  color: #666;
  font-size: 14px;
}

/* ⭐ 上下文信息样式 */
.context-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.context-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: #495057;
}

.badge-icon {
  font-size: 16px;
}

.context-bar {
  width: 100px;
  height: 6px;
  background: #e9ecef;
  border-radius: 3px;
  overflow: hidden;
}

.context-fill {
  height: 100%;
  background: linear-gradient(90deg, #28a745, #20c997);
  transition: width 0.3s ease;
}

.context-fill.warning {
  background: linear-gradient(90deg, #ffc107, #ff6b6b);
}

.clear-context-btn {
  padding: 6px 12px;
  background: #fff;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  color: #6c757d;
  transition: all 0.2s ease;
}

.clear-context-btn:hover {
  background: #f8f9fa;
  border-color: #adb5bd;
  color: #495057;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: 500px;
  background: #f8f9fa;
  border-radius: 10px;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.chat-messages::-webkit-scrollbar {
  width: 8px;
}

.chat-messages::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 4px;
}
</style>
