<template>
  <div :class="['message', type]">
    <div class="message-content">
      <div class="message-text" v-html="formattedContent"></div>

      <!-- ⭐ 流式输出时的光标动画 -->
      <span v-if="isStreaming" class="cursor-blink">▊</span>

      <span class="message-time">{{ formattedTime }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  type: String,
  content: String,
  timestamp: Date,
  isStreaming: {
    type: Boolean,
    default: false,
  },
});

const formattedContent = computed(() => {
  return props.content.replace(/\n/g, "<br>");
});

const formattedTime = computed(() => {
  return props.timestamp.toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  });
});
</script>

<style scoped>
.message {
  display: flex;
  animation: messageIn 0.3s ease;
}

@keyframes messageIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.message.user {
  justify-content: flex-end;
}

.message.bot {
  justify-content: flex-start;
}

.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
  position: relative;
}

.message.user .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.message.bot .message-content {
  background: white;
  color: #333;
  border: 1px solid #e9ecef;
  border-bottom-left-radius: 4px;
}

.message-time {
  display: block;
  font-size: 11px;
  opacity: 0.7;
  margin-top: 5px;
  text-align: right;
}

/* ⭐ 流式输出光标动画 */
.cursor-blink {
  display: inline-block;
  margin-left: 2px;
  animation: blink 1s infinite;
  color: #667eea;
  font-weight: bold;
}

@keyframes blink {
  0%,
  50% {
    opacity: 1;
  }
  51%,
  100% {
    opacity: 0;
  }
}
</style>
