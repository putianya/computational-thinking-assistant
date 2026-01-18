<template>
  <div class="chat-input-area">
    <input
      v-model="message"
      type="text"
      placeholder="输入你的问题,按回车发送..."
      @keypress.enter="handleSend"
      :disabled="chatStore.isLoading || chatStore.isStreaming"
    />

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

const handleSend = async () => {
  if (!message.value.trim() || chatStore.isLoading || chatStore.isStreaming)
    return;

  const msg = message.value;
  message.value = "";

  await chatStore.sendMessageStream(msg);
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
