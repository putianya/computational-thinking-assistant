<template>
  <div class="app-container">
    <!-- 未登录状态：显示路由视图（Login/Register） -->
    <router-view v-if="!authStore.isLoggedIn" />

    <!-- 已登录状态：显示完整应用界面 -->
    <template v-else>
      <header class="app-header">
        <div class="header-left">
          <h1>🎓 计算思维课程助手系统</h1>
          <p>基于大语言模型的智能教学辅助平台 v1.0.0</p>
        </div>
        <div class="header-right">
          <span class="user-info">👤 {{ authStore.user?.username }}</span>
          <button @click="handleLogout" class="logout-btn">退出登录</button>
        </div>
      </header>

      <main class="app-main">
        <SystemTest />
        <ChatWindow />
      </main>

      <footer class="app-footer">
        <span class="status-indicator"></span>
        系统运行中 | Powered by OpenAI GPT
      </footer>
    </template>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "./stores/user";
import ChatWindow from "./components/ChatWindow.vue";
import SystemTest from "./components/SystemTest.vue";

const router = useRouter();
const authStore = useAuthStore();

// 页面加载时自动登录
onMounted(async () => {
  console.log("🚀 应用启动，尝试自动登录...");
  const success = await authStore.autoLogin();

  if (success) {
    console.log("✅ 自动登录成功，跳转到首页");
    router.push("/");
  } else {
    console.log("📭 无有效登录状态，跳转到登录页");
    router.push("/login");
  }
});

// 退出登录
function handleLogout() {
  if (confirm("确定要退出登录吗？")) {
    authStore.logout();
    router.push("/login");
  }
}
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
  padding: 20px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.header-left h1 {
  font-size: 24px;
  margin-bottom: 5px;
  font-weight: 600;
}

.header-left p {
  font-size: 13px;
  opacity: 0.9;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-info {
  font-size: 14px;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.2);
  padding: 8px 16px;
  border-radius: 20px;
}

.logout-btn {
  background: rgba(255, 255, 255, 0.3);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.5);
  padding: 8px 20px;
  border-radius: 20px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.4);
  border-color: white;
  transform: translateY(-2px);
}

.logout-btn:active {
  transform: translateY(0);
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
