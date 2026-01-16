<template>
  <div class="chat-input-area">
    <input
      v-model="message"
      type="text"
      placeholder="输入你的问题,按回车发送..."
      @keypress.enter="handleSend"
      :disabled="chatStore.isLoading || chatStore.isStreaming"
    />

    <!-- ⭐ 流式/普通切换开关 -->
    <label class="stream-toggle">
      <input type="checkbox" v-model="useStreaming" />
      <span class="toggle-label">⚡ 流式输出</span>
    </label>

    <button
      @click="handleSend"
      :disabled="
        chatStore.isLoading || chatStore.isStreaming || !message.trim()
      "
    >
      <span v-if="chatStore.isStreaming">⏳ 接收中...</span>
      <span v-else-if="chatStore.isLoading">📤 发送中...</span>
      <span v-else>发送</span>
    </button>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useChatStore } from "../stores/chat";

const chatStore = useChatStore();
const message = ref("");
const useStreaming = ref(true); // ⭐ 默认使用流式输出

const handleSend = async () => {
  if (!message.value.trim() || chatStore.isLoading || chatStore.isStreaming)
    return;

  const msg = message.value;
  message.value = "";

  // ⭐ 根据开关选择发送方式
  if (useStreaming.value) {
    await chatStore.sendMessageStream(msg);
  } else {
    await chatStore.sendMessage(msg);
  }
};
</script>

<style scoped>
.chat-input-area {
  display: flex;
  gap: 10px;
  padding: 20px;
  background: white;
  border-top: 1px solid #e9ecef;
  align-items: center;
}

input[type="text"] {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #dee2e6;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: all 0.3s ease;
}

input[type="text"]:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* ⭐ 流式输出开关样式 */
.stream-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  user-select: none;
  padding: 8px 12px;
  border-radius: 6px;
  transition: background 0.2s;
}

.stream-toggle:hover {
  background: #f8f9fa;
}

.stream-toggle input[type="checkbox"] {
  cursor: pointer;
}

.toggle-label {
  font-size: 13px;
  color: #495057;
  white-space: nowrap;
}

button {
  padding: 12px 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
  white-space: nowrap;
}

button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}
</style>
