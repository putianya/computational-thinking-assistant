<template>
  <div class="register-page">
    <div class="register-container">
      <!-- 标题 -->
      <div class="register-header">
        <div class="logo">🎓</div>
        <h1>用户注册</h1>
        <p class="subtitle">加入计算思维课程助手</p>
      </div>

      <!-- 注册表单 -->
      <form @submit.prevent="handleRegister" class="register-form">
        <!-- 用户名 -->
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
          <span class="hint">3-20个字符，只能包含字母、数字、下划线</span>
        </div>

        <!-- 邮箱（可选） -->
        <div class="form-group">
          <label for="email">
            <span class="icon">📧</span>
            邮箱
          </label>
          <input
            id="email"
            v-model="formData.email"
            type="email"
            placeholder="example@email.com（可选）"
            :disabled="loading"
            autocomplete="email"
          />
          <span class="hint">可选，用于找回密码</span>
        </div>

        <!-- 密码 -->
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
            autocomplete="new-password"
          />
          <span class="hint">至少6个字符</span>
        </div>

        <!-- 确认密码 -->
        <div class="form-group">
          <label for="confirmPassword">
            <span class="icon">🔒</span>
            确认密码
          </label>
          <input
            id="confirmPassword"
            v-model="formData.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            :disabled="loading"
            autocomplete="new-password"
          />
        </div>

        <!-- 错误提示 -->
        <div v-if="errorMessage" class="error-message">
          ❌ {{ errorMessage }}
        </div>

        <!-- 成功提示 -->
        <div v-if="successMessage" class="success-message">
          ✅ {{ successMessage }}
        </div>

        <!-- 注册按钮 -->
        <button type="submit" class="register-button" :disabled="loading">
          <span v-if="loading">🔄 注册中...</span>
          <span v-else>注册</span>
        </button>

        <!-- 登录链接 -->
        <div class="login-link">
          已有账号？
          <a @click="goToLogin">立即登录</a>
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

const formData = ref({
  username: "",
  email: "",
  password: "",
  confirmPassword: "",
});

const loading = ref(false);
const errorMessage = ref("");
const successMessage = ref("");

function validateForm() {
  const { username, email, password, confirmPassword } = formData.value;

  if (!username.trim()) {
    return { valid: false, message: "请输入用户名" };
  }

  if (username.length < 3 || username.length > 20) {
    return { valid: false, message: "用户名长度应在3-20个字符之间" };
  }

  const usernameRegex = /^[a-zA-Z0-9_]+$/;
  if (!usernameRegex.test(username)) {
    return { valid: false, message: "用户名只能包含字母、数字、下划线" };
  }

  if (email.trim()) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return { valid: false, message: "邮箱格式不正确" };
    }
  }

  if (!password) {
    return { valid: false, message: "请输入密码" };
  }

  if (password.length < 6) {
    return { valid: false, message: "密码长度不能少于6个字符" };
  }

  if (!confirmPassword) {
    return { valid: false, message: "请确认密码" };
  }

  if (password !== confirmPassword) {
    return { valid: false, message: "两次输入的密码不一致" };
  }

  return { valid: true, message: "" };
}

async function handleRegister() {
  errorMessage.value = "";
  successMessage.value = "";

  const validation = validateForm();
  if (!validation.valid) {
    errorMessage.value = validation.message;
    return;
  }

  loading.value = true;

  try {
    const result = await authStore.register(
      formData.value.username,
      formData.value.password,
      formData.value.email.trim() || "",
      formData.value.username,
    );

    loading.value = false;

    if (result.success) {
      successMessage.value = "注册成功！2秒后跳转到登录页...";

      formData.value = {
        username: "",
        email: "",
        password: "",
        confirmPassword: "",
      };

      setTimeout(() => {
        router.push("/login");
      }, 2000);
    } else {
      errorMessage.value = result.message;
    }
  } catch (error) {
    loading.value = false;
    errorMessage.value = "注册失败，请稍后重试";
    console.error("❌ 注册错误:", error);
  }
}

function goToLogin() {
  router.push("/login");
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.register-container {
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

.register-header {
  text-align: center;
  margin-bottom: 30px;
}

.logo {
  font-size: 48px;
  margin-bottom: 10px;
}

.register-header h1 {
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

.register-form {
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

.hint {
  font-size: 12px;
  color: #999;
  margin-top: -4px;
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

.success-message {
  padding: 12px 16px;
  background-color: #d4edda;
  border: 1px solid #c3e6cb;
  border-radius: 8px;
  color: #155724;
  font-size: 14px;
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.register-button {
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

.register-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.register-button:active:not(:disabled) {
  transform: translateY(0);
}

.register-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.login-link {
  text-align: center;
  font-size: 14px;
  color: #666;
}

.login-link a {
  color: #667eea;
  font-weight: 600;
  cursor: pointer;
  text-decoration: none;
  transition: color 0.3s ease;
}

.login-link a:hover {
  color: #764ba2;
  text-decoration: underline;
}

@media (max-width: 480px) {
  .register-container {
    padding: 30px 20px;
  }

  .register-header h1 {
    font-size: 20px;
  }

  .logo {
    font-size: 40px;
  }
}
</style>
