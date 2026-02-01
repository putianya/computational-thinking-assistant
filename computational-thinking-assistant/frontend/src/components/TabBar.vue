<template>
  <div class="tab-bar">
    <div
      v-for="tab in tabs"
      :key="tab.id"
      :class="['tab-item', { active: activeTab === tab.id }]"
      @click="$emit('switch', tab.id)"
    >
      <i :class="tab.icon"></i>
      <span class="tab-label">{{ tab.label }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
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

defineEmits(["switch"]);
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
  top: 2px; /* 与底部边框对齐 */
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

/* 响应式 */
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
    display: none; /* 移动端隐藏文字，只显示图标 */
  }
}
</style>
