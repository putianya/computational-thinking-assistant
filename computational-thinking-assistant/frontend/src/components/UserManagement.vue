<template>
  <div class="user-management">
    <div class="header">
      <h1>👥 用户管理</h1>
      <button @click="handleRefresh" class="refresh-btn">
        <i class="fas fa-sync-alt"></i>
        刷新
      </button>
    </div>

    <!-- 加载中 -->
    <div v-if="isLoading" class="loading">
      <i class="fas fa-spinner fa-spin"></i>
      加载中...
    </div>

    <!-- 用户列表 -->
    <div v-else class="users-table">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>用户名</th>
            <th>昵称</th>
            <th>角色</th>
            <th>邮箱</th>
            <th>状态</th>
            <th>注册时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>{{ user.username }}</td>
            <td>{{ user.nickname || "-" }}</td>
            <td>
              <span class="role-badge" :class="`role-${user.role}`">
                {{ getRoleDisplay(user.role) }}
              </span>
            </td>
            <td>{{ user.email || "-" }}</td>
            <td>
              <span
                class="status-badge"
                :class="user.is_active ? 'active' : 'inactive'"
              >
                {{ user.is_active ? "正常" : "禁用" }}
              </span>
            </td>
            <td>{{ formatDate(user.created_at) }}</td>
            <td class="actions">
              <button
                @click="handleEditRole(user)"
                class="action-btn edit-btn"
                title="修改角色"
              >
                <i class="fas fa-user-edit"></i>
              </button>
              <button
                @click="handleToggleStatus(user)"
                class="action-btn"
                :class="user.is_active ? 'disable-btn' : 'enable-btn'"
                :title="user.is_active ? '禁用' : '启用'"
              >
                <i :class="user.is_active ? 'fas fa-ban' : 'fas fa-check'"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useAuthStore } from "../stores/user";

const authStore = useAuthStore();
const users = ref([]);
const isLoading = ref(false);

onMounted(() => {
  loadUsers();
});

async function loadUsers() {
  isLoading.value = true;
  try {
    // TODO: 调用后端 API 获取用户列表
    console.log("加载用户列表...");
    alert("⚠️ 用户管理功能正在开发中");
  } catch (error) {
    console.error("加载用户失败:", error);
    alert("加载失败: " + error.message);
  } finally {
    isLoading.value = false;
  }
}

function getRoleDisplay(role) {
  const roleMap = {
    student: "学生",
    teacher: "教师",
    admin: "管理员",
  };
  return roleMap[role] || role;
}

function formatDate(dateStr) {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleDateString("zh-CN");
}

function handleRefresh() {
  loadUsers();
}

function handleEditRole(user) {
  alert(`⚠️ 修改用户 ${user.username} 的角色功能正在开发中`);
}

function handleToggleStatus(user) {
  const action = user.is_active ? "禁用" : "启用";
  if (confirm(`确定要${action}用户 ${user.username} 吗？`)) {
    alert(`⚠️ ${action}用户功能正在开发中`);
  }
}
</script>

<style scoped>
.user-management {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.refresh-btn {
  padding: 10px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #999;
}

.users-table {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  background: #f5f5f5;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #666;
  border-bottom: 2px solid #e0e0e0;
}

td {
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.role-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.role-student {
  background: #e3f2fd;
  color: #1976d2;
}

.role-teacher {
  background: #f3e5f5;
  color: #7b1fa2;
}

.role-admin {
  background: #ffebee;
  color: #c62828;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.active {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-badge.inactive {
  background: #ffebee;
  color: #c62828;
}

.actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.edit-btn {
  background: #e3f2fd;
  color: #1976d2;
}

.disable-btn {
  background: #ffebee;
  color: #c62828;
}

.enable-btn {
  background: #e8f5e9;
  color: #2e7d32;
}
</style>
