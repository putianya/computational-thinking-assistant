<template>
  <div class="test-section">
    <!-- ⭐ 修改：标题栏添加收起按钮 -->
    <div class="test-header">
      <h2>🔧 系统测试</h2>
      <button @click="handleCollapse" class="collapse-btn" title="收起">
        {{ isCollapsed ? "▼" : "▲" }}
      </button>
    </div>

    <!-- ⭐ 修改：可折叠的内容 -->
    <Transition name="collapse">
      <div v-show="!isCollapsed" class="test-content">
        <p>点击按钮测试后端连接和 OpenAI API 配置:</p>
        <button @click="handleTest" :disabled="isLoading" class="test-btn">
          {{ isLoading ? "测试中..." : "测试系统状态" }}
        </button>

        <div v-if="result" class="result show">
          <div v-if="result.status === 'success'">
            <p class="success">✅ {{ result.message }}</p>
            <p class="info"><strong>时间:</strong> {{ result.timestamp }}</p>
            <p class="info"><strong>版本:</strong> {{ result.version }}</p>
            <p class="info">
              <strong>Python:</strong> {{ result.python_version }}
            </p>
            <p class="info">
              <strong>OpenAI 配置:</strong>
              {{ result.openai_configured ? "已配置 ✓" : "未配置 ✗" }}
            </p>
          </div>
          <div v-else>
            <p class="error">❌ 测试失败: {{ errorMessage }}</p>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { chatAPI } from "../api/chat";

const isLoading = ref(false);
const result = ref(null);
const errorMessage = ref("");
const isCollapsed = ref(true); // ⭐⭐⭐ 修改：默认折叠（改为 true）⭐⭐⭐

const handleTest = async () => {
  isLoading.value = true;
  result.value = null;
  errorMessage.value = "";

  try {
    const data = await chatAPI.testConnection();
    result.value = data;
  } catch (error) {
    result.value = { status: "error" };
    errorMessage.value = error.message;
  } finally {
    isLoading.value = false;
  }
};

// 收起/展开切换
const handleCollapse = () => {
  isCollapsed.value = !isCollapsed.value;
};
</script>

<style scoped>
.test-section {
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

/* ⭐ 新增：标题栏样式 */
.test-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.test-section h2 {
  font-size: 20px;
  margin: 0;
  color: #333;
}

/* ⭐ 新增：收起按钮样式 */
.collapse-btn {
  padding: 4px 12px;
  background: #f8f9fa;
  color: #666;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  cursor: pointer;
  font-size: 16px;
  transition: all 0.2s;
  min-width: 40px;
}

.collapse-btn:hover {
  background: #e9ecef;
  color: #333;
  transform: scale(1.05);
}

/* ⭐ 新增：内容区域 */
.test-content {
  overflow: hidden;
}

.test-section p {
  color: #666;
  margin-bottom: 15px;
  font-size: 14px;
}

/* ⭐ 修改：测试按钮类名 */
.test-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.test-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.test-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.result {
  margin-top: 15px;
  padding: 15px;
  border-radius: 8px;
  background: #f8f9fa;
  border: 1px solid #dee2e6;
  animation: slideDown 0.3s ease;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ⭐ 新增：折叠动画 */
.collapse-enter-active,
.collapse-leave-active {
  transition: all 0.3s ease;
}

.collapse-enter-from,
.collapse-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-10px);
}

.collapse-enter-to,
.collapse-leave-from {
  opacity: 1;
  max-height: 500px;
  transform: translateY(0);
}

.success {
  color: #28a745;
  font-weight: 600;
}

.error {
  color: #dc3545;
  font-weight: 600;
}

.info {
  color: #666;
  margin: 5px 0;
}
</style>
