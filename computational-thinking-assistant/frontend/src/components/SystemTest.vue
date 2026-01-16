<template>
  <div class="test-section">
    <h2>🔧 系统测试</h2>
    <p>点击按钮测试后端连接和 OpenAI API 配置:</p>
    <button @click="handleTest" :disabled="isLoading">
      {{ isLoading ? "测试中..." : "测试系统状态" }}
    </button>

    <div v-if="result" class="result show">
      <div v-if="result.status === 'success'">
        <p class="success">✅ {{ result.message }}</p>
        <p class="info"><strong>时间:</strong> {{ result.timestamp }}</p>
        <p class="info"><strong>版本:</strong> {{ result.version }}</p>
        <p class="info"><strong>Python:</strong> {{ result.python_version }}</p>
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
</template>

<script setup>
import { ref } from "vue";
import { chatAPI } from "../api/chat";

const isLoading = ref(false);
const result = ref(null);
const errorMessage = ref("");

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
</script>

<style scoped>
.test-section {
  background: white;
  padding: 20px;
  border-radius: 10px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.test-section h2 {
  font-size: 20px;
  margin-bottom: 10px;
  color: #333;
}

.test-section p {
  color: #666;
  margin-bottom: 15px;
  font-size: 14px;
}

button {
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

button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

button:disabled {
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
