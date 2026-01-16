<template>
  <div class="app-container">
    <header class="app-header">
      <h1>🎓 计算思维课程助手系统</h1>
      <p>基于大语言模型的智能教学辅助平台 v1.0.0</p>
    </header>

    <main class="app-main">
      <SystemTest />
      <ChatWindow />
    </main>

    <footer class="app-footer">
      <span class="status-indicator"></span>
      系统运行中 | Powered by OpenAI GPT
    </footer>
  </div>
</template>

<script setup>
import ChatWindow from "./components/ChatWindow.vue";
import SystemTest from "./components/SystemTest.vue";
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 30px;
  text-align: center;
}

.app-header h1 {
  font-size: 28px;
  margin-bottom: 10px;
  font-weight: 600;
}

.app-header p {
  font-size: 14px;
  opacity: 0.9;
}

.app-main {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.app-footer {
  background: #f8f9fa;
  padding: 12px 30px;
  text-align: center;
  font-size: 12px;
  color: #666;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
}

.status-indicator {
  width: 8px;
  height: 8px;
  background: #28a745;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>
