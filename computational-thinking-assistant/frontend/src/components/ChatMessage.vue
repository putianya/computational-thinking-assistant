<template>
  <div class="chat-message" :class="messageClass">
    <div class="message-avatar">
      <span class="avatar-icon">{{ avatarIcon }}</span>
    </div>

    <div class="message-content-wrapper">
      <div class="message-header">
        <span class="message-sender">{{ senderName }}</span>
        <span class="message-time">{{ formattedTime }}</span>
      </div>

      <div class="message-content" :class="{ streaming: isStreaming }">
        <div
          v-if="type === 'assistant'"
          class="markdown-body"
          v-html="renderedContent"
        ></div>
        <div v-else class="plain-text">{{ content }}</div>

        <!-- 流式输出光标 -->
        <span v-if="isStreaming" class="typing-cursor">▊</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { marked } from "marked";

// ========== Props ==========
const props = defineProps({
  type: {
    type: String,
    required: true,
    validator: (value) => ["user", "assistant"].includes(value),
  },
  content: {
    type: String,
    required: true,
  },
  timestamp: {
    type: [String, Date, Number], // ⭐ 支持多种类型
    default: null,
  },
  isStreaming: {
    type: Boolean,
    default: false,
  },
});

// ========== 计算属性 ==========

/**
 * 消息样式类
 */
const messageClass = computed(() => {
  return props.type === "user" ? "message-user" : "message-assistant";
});

/**
 * 头像图标
 */
const avatarIcon = computed(() => {
  return props.type === "user" ? "👤" : "🤖";
});

/**
 * 发送者名称
 */
const senderName = computed(() => {
  return props.type === "user" ? "我" : "AI 助手";
});

/**
 * ⭐ 格式化时间（修复）
 */
const formattedTime = computed(() => {
  if (!props.timestamp) {
    return "";
  }

  try {
    let date;

    // ⭐ 处理不同类型的 timestamp
    if (props.timestamp instanceof Date) {
      date = props.timestamp;
    } else if (typeof props.timestamp === "number") {
      date = new Date(props.timestamp);
    } else if (typeof props.timestamp === "string") {
      date = new Date(props.timestamp);
    } else {
      return "";
    }

    // ⭐ 检查日期是否有效
    if (isNaN(date.getTime())) {
      console.warn("⚠️ 无效的时间戳:", props.timestamp);
      return "";
    }

    return date.toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch (error) {
    console.error("❌ 时间格式化错误:", error, props.timestamp);
    return "";
  }
});

/**
 * 渲染 Markdown（仅 AI 消消息）
 */
const renderedContent = computed(() => {
  if (props.type !== "assistant") {
    return props.content;
  }

  try {
    // 配置 marked
    marked.setOptions({
      breaks: true,
      gfm: true,
      headerIds: false,
      mangle: false,
    });

    return marked.parse(props.content);
  } catch (error) {
    console.error("❌ Markdown 渲染错误:", error);
    return props.content;
  }
});
</script>

<style scoped>
/* ========== 消息容器 ========== */
.chat-message {
  display: flex;
  gap: 12px;
  padding: 16px 0;
  animation: fadeIn 0.3s ease;
}

/* ⭐ 新增：用户消息右对齐 */
.message-user {
  flex-direction: row-reverse; /* 反转布局方向 */
  justify-content: flex-start;
}

/* ⭐ 新增：AI 消息左对齐 */
.message-assistant {
  flex-direction: row;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ========== 头像 ========== */
.message-avatar {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.message-user .message-avatar {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  box-shadow: 0 2px 8px rgba(245, 87, 108, 0.3);
}

.avatar-icon {
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.2));
}

/* ========== 内容区域 ========== */
.message-content-wrapper {
  flex: 1;
  min-width: 0;
  /* ⭐ 新增：用户消息右对齐内容 */
  display: flex;
  flex-direction: column;
}

/* ⭐ 新增：用户消息的头部右对齐 */
.message-user .message-content-wrapper {
  align-items: flex-end;
}

/* ⭐ 新增：AI 消息的头部左对齐 */
.message-assistant .message-content-wrapper {
  align-items: flex-start;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

/* ⭐ 新增：用户消息时间在左边 */
.message-user .message-header {
  flex-direction: row-reverse;
}

.message-sender {
  font-weight: 600;
  font-size: 14px;
  color: #333;
}

.message-user .message-sender {
  color: #f5576c;
}

.message-assistant .message-sender {
  color: #667eea;
}

.message-time {
  font-size: 12px;
  color: #999;
}

/* ========== 消息内容 ========== */
.message-content {
  padding: 12px 16px;
  border-radius: 12px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  word-wrap: break-word;
  position: relative;
  line-height: 1.6;
  max-width: 80%; /* ⭐ 限制最大宽度，避免过宽 */
}

.message-user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  /* ⭐ 新增：用户消息圆角调整（左上角更圆） */
  border-radius: 18px 18px 4px 18px;
}

.message-assistant .message-content {
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  /* ⭐ 新增：AI 消息圆角调整（右上角更圆） */
  border-radius: 18px 18px 18px 4px;
}

/* ========== 纯文本内容 ========== */
.plain-text {
  white-space: pre-wrap;
  font-size: 15px;
}

/* ========== Markdown 渲染 ========== */
.markdown-body {
  font-size: 15px;
  color: #333;
}

.markdown-body :deep(p) {
  margin: 0 0 12px 0;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(code) {
  background: #f1f3f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 14px;
  font-family: "Consolas", "Monaco", "Courier New", monospace;
  color: #e83e8c;
}

.markdown-body :deep(pre) {
  background: #2d2d2d;
  color: #f8f8f2;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
  color: inherit;
  font-size: 13px;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.markdown-body :deep(li) {
  margin: 4px 0;
}

.markdown-body :deep(blockquote) {
  border-left: 4px solid #667eea;
  padding-left: 16px;
  margin: 12px 0;
  color: #666;
  font-style: italic;
}

.markdown-body :deep(a) {
  color: #667eea;
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  margin: 16px 0 12px 0;
  font-weight: 600;
  color: #333;
}

.markdown-body :deep(h1) {
  font-size: 24px;
}

.markdown-body :deep(h2) {
  font-size: 20px;
}

.markdown-body :deep(h3) {
  font-size: 18px;
}

/* ========== 流式输出效果 ========== */
.message-content.streaming {
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  }
  50% {
    box-shadow: 0 4px 16px rgba(102, 126, 234, 0.2);
  }
}

.typing-cursor {
  display: inline-block;
  width: 8px;
  height: 16px;
  background: #667eea;
  margin-left: 4px;
  animation: blink 1s step-end infinite;
  vertical-align: middle;
}

/* ⭐ 新增：用户消息的光标颜色调整 */
.message-user .typing-cursor {
  background: white;
}

@keyframes blink {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}

/* ========== 响应式设计 ========== */
@media (max-width: 768px) {
  .chat-message {
    gap: 8px;
    padding: 12px 0;
  }

  .message-avatar {
    width: 36px;
    height: 36px;
    font-size: 18px;
  }

  .message-content {
    padding: 10px 14px;
    font-size: 14px;
    max-width: 85%; /* ⭐ 移动端稍微宽一点 */
  }

  .markdown-body,
  .plain-text {
    font-size: 14px;
  }
}
</style>
