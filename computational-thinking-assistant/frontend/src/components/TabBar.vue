<template>
  <div class="tab-bar">
    <div
      v-for="tab in tabs"
      :key="tab.id"
      :class="['tab-item', { active: activeTab === tab.id }]"
      @click="handleTabSwitch(tab.id)"
    >
      <i :class="tab.icon"></i>
      <span class="tab-label">{{ tab.label }}</span>
    </div>
  </div>
</template>

<script setup>
import { useChatStore } from "../stores/chat";

// ⭐⭐⭐ 保留原有的 props 定义 ⭐⭐⭐
const props = defineProps({
  tabs: {
    type: Array,
    required: true,
    // 格式: [{ id: 'chat', label: '💬 对话', icon: 'fas fa-comments' }]
  },
  activeTab: {
    type: String,
    required: true,
  },
});

// ⭐⭐⭐ 保留原有的 emit 定义 ⭐⭐⭐
const emit = defineEmits(["switch"]);

// ⭐⭐⭐ 新增：获取 chat store ⭐⭐⭐
const chatStore = useChatStore();

// ⭐⭐⭐ 新增：处理标签切换 ⭐⭐⭐
function handleTabSwitch(tabId) {
  if (tabId === props.activeTab) return;

  console.log("📑 切换标签:", props.activeTab, "→", tabId);

  // 区分切走和切回
  if (props.activeTab === "chat" && chatStore.isStreaming) {
    // 从对话切走：暂停UI更新
    console.log("⏸️ 从对话切走，暂停流式显示");
    chatStore.abortCurrentStream();
  } else if (tabId === "chat" && chatStore.isStreaming) {
    // 切回对话：恢复UI更新，追赶进度
    console.log("▶️ 切回对话，恢复流式显示");
    chatStore.resumeStream();
  }

  emit("switch", tabId);
}
</script>

<style scoped>
.tab-bar {
  display: flex;
  background: white;
  border-bottom: 2px solid #e0e0e0;
  padding: 0 20px;
  gap: 8px;
  flex-shrink: 0;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 24px;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.3s;
  font-size: 15px;
  font-weight: 500;
  color: #666;
  position: relative;
  top: 2px;
}

.tab-item:hover {
  background: #f5f7fa;
  color: #667eea;
}

.tab-item.active {
  color: #667eea;
  border-bottom-color: #667eea;
  background: #f0f4ff;
}

.tab-item i {
  font-size: 18px;
}

@media (max-width: 768px) {
  .tab-bar {
    overflow-x: auto;
    padding: 0 12px;
  }

  .tab-item {
    flex-shrink: 0;
    padding: 12px 16px;
    font-size: 14px;
  }

  .tab-label {
    display: none;
  }
}
</style>
