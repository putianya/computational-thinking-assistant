<template>
  <div class="login-page">
    <div class="login-container">
      <!-- 标题 -->
      <div class="login-header">
        <div class="logo">🎓</div>
        <h1>计算思维课程助手</h1>
        <p class="subtitle">欢迎回来！请登录您的账号</p>
      </div>

      <!-- 登录表单 -->
      <form @submit.prevent="handleLogin" class="login-form">
        <!-- 用户名输入框 -->
        <div class="form-group">
          <label for="username">
            <span class="icon">👤</span>
            用户名
          </label>
          <input
            id="username"
            v-model="formData.username"
            type="text"
            placeholder="请输入用户名"
            :disabled="loading"
            autocomplete="username"
          />
        </div>

        <!-- 密码输入框 -->
        <div class="form-group">
          <label for="password">
            <span class="icon">🔒</span>
            密码
          </label>
          <input
            id="password"
            v-model="formData.password"
            type="password"
            placeholder="请输入密码"
            :disabled="loading"
            autocomplete="current-password"
          />
        </div>

        <!-- 记住密码 -->
        <div class="form-options">
          <label class="remember-me">
            <input v-model="formData.rememberMe" type="checkbox" />
            <span>记住密码</span>
          </label>
        </div>

        <!-- 错误提示 -->
        <div v-if="errorMessage" class="error-message">
          ❌ {{ errorMessage }}
        </div>

        <!-- 登录按钮 -->
        <button type="submit" class="login-button" :disabled="loading">
          <span v-if="loading">🔄 登录中...</span>
          <span v-else>登录</span>
        </button>

        <!-- 注册链接 -->
        <div class="register-link">
          还没有账号？
          <a @click="goToRegister">立即注册</a>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/user";

const router = useRouter();
const authStore = useAuthStore();

// 数据
const formData = ref({
  username: "",
  password: "",
  rememberMe: false,
});

const loading = ref(false);
const errorMessage = ref("");

// 处理登录
async function handleLogin() {
  errorMessage.value = "";

  if (!formData.value.username.trim()) {
    errorMessage.value = "请输入用户名";
    return;
  }

  if (!formData.value.password.trim()) {
    errorMessage.value = "请输入密码";
    return;
  }

  loading.value = true;

  try {
    const result = await authStore.login(
      formData.value.username,
      formData.value.password,
      formData.value.rememberMe,
    );

    loading.value = false;

    if (result.success) {
      console.log("✅ 登录成功，跳转到主页");
      router.push("/");
    } else {
      errorMessage.value = result.message;
    }
  } catch (error) {
    loading.value = false;
    errorMessage.value = "登录失败，请稍后重试";
    console.error("❌ 登录错误:", error);
  }
}

// 跳转到注册页
function goToRegister() {
  router.push("/register");
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-container {
  width: 100%;
  max-width: 420px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  padding: 40px;
  animation: slideIn 0.5s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.logo {
  font-size: 48px;
  margin-bottom: 10px;
}

.login-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #333;
  margin: 0 0 8px 0;
}

.subtitle {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  display: flex;
  align-items: center;
  gap: 6px;
}

.form-group label .icon {
  font-size: 16px;
}

.form-group input {
  width: 100%;
  padding: 12px 16px;
  font-size: 14px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  outline: none;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.form-group input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-group input:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
}

.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #666;
  cursor: pointer;
  user-select: none;
}

.remember-me input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.error-message {
  padding: 12px 16px;
  background-color: #fee;
  border: 1px solid #fcc;
  border-radius: 8px;
  color: #c33;
  font-size: 14px;
  animation: shake 0.3s ease-in-out;
}

@keyframes shake {
  0%,
  100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-10px);
  }
  75% {
    transform: translateX(10px);
  }
}

.login-button {
  width: 100%;
  padding: 14px;
  font-size: 16px;
  font-weight: 600;
  color: white;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.login-button:active:not(:disabled) {
  transform: translateY(0);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.register-link {
  text-align: center;
  font-size: 14px;
  color: #666;
}

.register-link a {
  color: #667eea;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: color 0.3s ease;
}

.register-link a:hover {
  color: #764ba2;
  text-decoration: underline;
}

@media (max-width: 480px) {
  .login-container {
    padding: 30px 20px;
  }

  .login-header h1 {
    font-size: 20px;
  }

  .logo {
    font-size: 40px;
  }
}
</style>
