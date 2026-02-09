<template>
  <div class="chat-input-area">
    <!-- ⭐ 草稿提示移到输入框上方 -->
    <div v-if="hasDraft" class="draft-notice">
      <i class="fas fa-info-circle"></i>
      检测到未发送的草稿
      <button @click="clearDraft" class="btn-clear-draft">清除</button>
    </div>

    <!-- ⭐ 输入框和按钮横向排列 -->
    <div class="input-row">
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
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from "vue";
import { useChatStore } from "../stores/chat";

const chatStore = useChatStore();
const message = ref("");

// ⭐ localStorage 键名
const DRAFT_KEY = "chat_input_draft";

// ⭐ 计算属性：是否有草稿
const hasDraft = computed(() => {
  return message.value.trim().length > 0;
});

// ⭐ 组件挂载时恢复草稿
onMounted(() => {
  const savedDraft = localStorage.getItem(DRAFT_KEY);
  if (savedDraft) {
    message.value = savedDraft;
    console.log("✅ 恢复聊天草稿:", savedDraft.substring(0, 30) + "...");
  }
});

// ⭐ 监听输入变化，自动保存草稿（防抖优化）
let saveTimer = null;
watch(message, (newValue) => {
  // 清除之前的定时器
  if (saveTimer) {
    clearTimeout(saveTimer);
  }

  // 500ms 后保存（防止频繁写入）
  saveTimer = setTimeout(() => {
    if (newValue.trim()) {
      localStorage.setItem(DRAFT_KEY, newValue);
      console.log("💾 保存聊天草稿");
    } else {
      localStorage.removeItem(DRAFT_KEY);
      console.log("🗑️ 清除聊天草稿");
    }
  }, 500);
});

// ⭐ 发送消息时清除草稿
const handleSend = async () => {
  if (!message.value.trim() || chatStore.isLoading || chatStore.isStreaming)
    return;

  const msg = message.value;
  message.value = "";

  // ⭐ 清除草稿
  localStorage.removeItem(DRAFT_KEY);
  console.log("📤 发送消息，清除草稿");

  await chatStore.sendMessageStream(msg);
};

// ⭐ 手动清除草稿
const clearDraft = () => {
  if (confirm("确定要清除草稿吗？")) {
    message.value = "";
    localStorage.removeItem(DRAFT_KEY);
    console.log("🗑️ 手动清除草稿");
  }
};
</script>

<style scoped>
.chat-input-area {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 20px;
  background: white;
  border-top: 1px solid #e9ecef;
}

/* ⭐ 草稿提示样式 */
.draft-notice {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: #fff3cd;
  border: 1px solid #ffc107;
  border-radius: 6px;
  font-size: 13px;
  color: #856404;
}

.draft-notice i {
  color: #ffc107;
}

.btn-clear-draft {
  padding: 4px 12px;
  background: transparent;
  color: #856404;
  border: 1px solid #856404;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  margin-left: auto;
}

.btn-clear-draft:hover {
  background: #856404;
  color: white;
}

/* ⭐ 输入框和按钮横向排列 */
.input-row {
  display: flex;
  gap: 10px;
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
  flex-shrink: 0; /* ⭐ 防止按钮被压缩 */
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
