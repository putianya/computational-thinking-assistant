<template>
  <div class="user-management">
    <div class="header">
      <h1>👥 用户管理</h1>
      <div class="header-actions">
        <button @click="handleRefresh" class="refresh-btn">
          <i class="fas fa-sync-alt"></i>
          刷新
        </button>
        <!-- ⭐⭐⭐ 新增：添加用户按钮 ⭐⭐⭐ -->
        <button @click="handleAddUser" class="add-user-btn">
          <i class="fas fa-user-plus"></i>
          添加用户
        </button>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="isLoading" class="loading">
      <i class="fas fa-spinner fa-spin"></i>
      加载中...
    </div>

    <!-- 空状态 -->
    <div v-else-if="users.length === 0" class="empty-state">
      <div class="empty-icon">👥</div>
      <p>暂无用户数据</p>
    </div>

    <!-- 用户列表 -->
    <div v-else class="users-table">
      <table>
        <thead>
          <tr>
            <th @click="handleSort('id')" class="sortable">
              ID
              <span class="sort-icon">
                <i
                  v-if="sortField === 'id' && sortOrder === 'asc'"
                  class="fas fa-caret-up"
                ></i>
                <i
                  v-else-if="sortField === 'id' && sortOrder === 'desc'"
                  class="fas fa-caret-down"
                ></i>
                <i v-else class="fas fa-sort"></i>
              </span>
            </th>
            <th @click="handleSort('username')" class="sortable">
              用户名
              <span class="sort-icon">
                <i
                  v-if="sortField === 'username' && sortOrder === 'asc'"
                  class="fas fa-caret-up"
                ></i>
                <i
                  v-else-if="sortField === 'username' && sortOrder === 'desc'"
                  class="fas fa-caret-down"
                ></i>
                <i v-else class="fas fa-sort"></i>
              </span>
            </th>
            <th @click="handleSort('nickname')" class="sortable">
              昵称
              <span class="sort-icon">
                <i
                  v-if="sortField === 'nickname' && sortOrder === 'asc'"
                  class="fas fa-caret-up"
                ></i>
                <i
                  v-else-if="sortField === 'nickname' && sortOrder === 'desc'"
                  class="fas fa-caret-down"
                ></i>
                <i v-else class="fas fa-sort"></i>
              </span>
            </th>
            <th @click="handleSort('role')" class="sortable">
              角色
              <span class="sort-icon">
                <i
                  v-if="sortField === 'role' && sortOrder === 'asc'"
                  class="fas fa-caret-up"
                ></i>
                <i
                  v-else-if="sortField === 'role' && sortOrder === 'desc'"
                  class="fas fa-caret-down"
                ></i>
                <i v-else class="fas fa-sort"></i>
              </span>
            </th>
            <th>邮箱</th>
            <th @click="handleSort('is_active')" class="sortable">
              状态
              <span class="sort-icon">
                <i
                  v-if="sortField === 'is_active' && sortOrder === 'asc'"
                  class="fas fa-caret-up"
                ></i>
                <i
                  v-else-if="sortField === 'is_active' && sortOrder === 'desc'"
                  class="fas fa-caret-down"
                ></i>
                <i v-else class="fas fa-sort"></i>
              </span>
            </th>
            <th @click="handleSort('created_at')" class="sortable">
              注册时间
              <span class="sort-icon">
                <i
                  v-if="sortField === 'created_at' && sortOrder === 'asc'"
                  class="fas fa-caret-up"
                ></i>
                <i
                  v-else-if="sortField === 'created_at' && sortOrder === 'desc'"
                  class="fas fa-caret-down"
                ></i>
                <i v-else class="fas fa-sort"></i>
              </span>
            </th>
            <th>操作</th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.id }}</td>
            <td>
              <strong>{{ user.username }}</strong>
            </td>
            <td>{{ user.nickname || "-" }}</td>
            <td>
              <span class="role-badge" :class="`role-${user.role}`">
                {{ user.role_display }}
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
              <!-- ⭐ 修改：编辑完整信息 -->
              <button
                @click="handleEditUser(user)"
                class="action-btn edit-btn"
                title="编辑用户"
              >
                <i class="fas fa-user-edit"></i>
              </button>

              <!-- 启用/禁用 -->
              <button
                @click="handleToggleStatus(user)"
                class="action-btn"
                :class="user.is_active ? 'disable-btn' : 'enable-btn'"
                :title="user.is_active ? '禁用' : '启用'"
              >
                <i :class="user.is_active ? 'fas fa-ban' : 'fas fa-check'"></i>
              </button>

              <!-- 删除 -->
              <button
                @click="handleDelete(user)"
                class="action-btn delete-btn"
                title="删除用户"
              >
                <i class="fas fa-trash"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- ⭐⭐⭐ 新增/编辑用户对话框 ⭐⭐⭐ -->
    <div v-if="showUserDialog" class="modal-overlay" @click="closeUserDialog">
      <div class="modal-content large-modal" @click.stop>
        <div class="modal-header">
          <h3>{{ isEditMode ? "编辑用户" : "添加用户" }}</h3>
          <button class="close-btn" @click="closeUserDialog">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="modal-body">
          <!-- 用户名 -->
          <div class="form-group">
            <label>
              <i class="fas fa-user"></i> 用户名 <span class="required">*</span>
            </label>
            <input
              type="text"
              v-model="userForm.username"
              :disabled="isEditMode"
              placeholder="请输入用户名"
              required
            />
          </div>

          <!-- 昵称 -->
          <div class="form-group">
            <label> <i class="fas fa-id-card"></i> 昵称 </label>
            <input
              type="text"
              v-model="userForm.nickname"
              placeholder="请输入昵称（可选）"
            />
          </div>

          <!-- 邮箱 -->
          <div class="form-group">
            <label> <i class="fas fa-envelope"></i> 邮箱 </label>
            <input
              type="email"
              v-model="userForm.email"
              placeholder="请输入邮箱（可选）"
            />
          </div>

          <!-- 密码 -->
          <div class="form-group">
            <label>
              <i class="fas fa-lock"></i> 密码
              <span v-if="!isEditMode" class="required">*</span>
              <span v-else style="color: #999; font-size: 12px"
                >（留空则不修改）</span
              >
            </label>
            <input
              type="password"
              v-model="userForm.password"
              :placeholder="isEditMode ? '留空则不修改密码' : '请输入密码'"
            />
          </div>

          <!-- 角色 -->
          <div class="form-group">
            <label>
              <i class="fas fa-user-tag"></i> 角色
              <span class="required">*</span>
            </label>
            <select v-model="userForm.role" required>
              <option value="student">学生</option>
              <option value="teacher">教师</option>
              <option value="admin">管理员</option>
            </select>
          </div>

          <!-- 状态 -->
          <div v-if="isEditMode" class="form-group">
            <label>
              <input type="checkbox" v-model="userForm.is_active" />
              <span>账户启用</span>
            </label>
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeUserDialog" class="cancel-btn">取消</button>
          <button
            @click="confirmUserAction"
            :disabled="isSaving"
            class="save-btn"
          >
            {{ isSaving ? "保存中..." : isEditMode ? "保存修改" : "创建用户" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useAuthStore } from "../stores/user";
import { userAPI } from "../api/user";

const authStore = useAuthStore();
const users = ref([]);
const isLoading = ref(false);

// 排序状态
const sortField = ref("id");
const sortOrder = ref("asc");

// ⭐⭐⭐ 新增/编辑用户状态 ⭐⭐⭐
const showUserDialog = ref(false);
const isEditMode = ref(false);
const editingUser = ref(null);
const isSaving = ref(false);

const userForm = ref({
  username: "",
  nickname: "",
  email: "",
  password: "",
  role: "student",
  is_active: true,
});

onMounted(() => {
  loadUsers();
});

/**
 * 加载用户列表
 */
async function loadUsers() {
  isLoading.value = true;
  try {
    console.log("📋 加载用户列表...");

    const response = await userAPI.getAllUsers({
      sort_by: sortField.value,
      order: sortOrder.value,
    });

    if (response.status === "success") {
      users.value = response.data.users;
      sortUsersLocally();
      console.log(`✅ 加载成功，共 ${users.value.length} 个用户`);
    } else {
      alert("加载失败: " + response.message);
    }
  } catch (error) {
    console.error("❌ 加载用户失败:", error);
    alert("加载失败: " + error.message);
  } finally {
    isLoading.value = false;
  }
}

/**
 * 前端排序
 */
function sortUsersLocally() {
  const field = sortField.value;
  const order = sortOrder.value;

  users.value.sort((a, b) => {
    let aVal = a[field];
    let bVal = b[field];

    if (aVal == null) aVal = "";
    if (bVal == null) bVal = "";

    if (typeof aVal === "string") {
      aVal = aVal.toLowerCase();
      bVal = bVal.toLowerCase();
    }

    if (aVal < bVal) return order === "asc" ? -1 : 1;
    if (aVal > bVal) return order === "asc" ? 1 : -1;
    return 0;
  });
}

/**
 * 处理排序
 */
function handleSort(field) {
  console.log(`🔄 排序: ${field}`);

  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === "asc" ? "desc" : "asc";
  } else {
    sortField.value = field;
    sortOrder.value = "asc";
  }

  loadUsers();
}

/**
 * 刷新用户列表
 */
function handleRefresh() {
  loadUsers();
}

/**
 * 格式化日期
 */
function formatDate(dateStr) {
  if (!dateStr) return "-";
  return new Date(dateStr).toLocaleString("zh-CN");
}

/**
 * ⭐⭐⭐ 新增：打开添加用户对话框 ⭐⭐⭐
 */
function handleAddUser() {
  console.log("➕ 打开添加用户对话框");

  isEditMode.value = false;
  editingUser.value = null;

  userForm.value = {
    username: "",
    nickname: "",
    email: "",
    password: "",
    role: "student",
    is_active: true,
  };

  showUserDialog.value = true;
}

/**
 * ⭐⭐⭐ 新增：打开编辑用户对话框 ⭐⭐⭐
 */
function handleEditUser(user) {
  console.log("✏️ 打开编辑用户对话框:", user.username);

  isEditMode.value = true;
  editingUser.value = user;

  userForm.value = {
    username: user.username,
    nickname: user.nickname || "",
    email: user.email || "",
    password: "", // 密码留空
    role: user.role,
    is_active: user.is_active,
  };

  showUserDialog.value = true;
}

/**
 * ⭐⭐⭐ 新增：关闭用户对话框 ⭐⭐⭐
 */
function closeUserDialog() {
  console.log("❌ 关闭用户对话框");
  showUserDialog.value = false;
  isEditMode.value = false;
  editingUser.value = null;

  userForm.value = {
    username: "",
    nickname: "",
    email: "",
    password: "",
    role: "student",
    is_active: true,
  };
}

/**
 * ⭐⭐⭐ 新增：确认创建/编辑用户 ⭐⭐⭐
 */
async function confirmUserAction() {
  // 验证必填字段
  if (!userForm.value.username) {
    alert("请输入用户名");
    return;
  }

  if (!isEditMode.value && !userForm.value.password) {
    alert("请输入密码");
    return;
  }

  if (!userForm.value.role) {
    alert("请选择角色");
    return;
  }

  try {
    isSaving.value = true;

    if (isEditMode.value) {
      // 编辑模式
      console.log("🔄 更新用户:", editingUser.value.username);

      const updateData = {
        nickname: userForm.value.nickname,
        email: userForm.value.email,
        role: userForm.value.role,
        is_active: userForm.value.is_active,
      };

      // 如果输入了新密码，一并更新
      if (userForm.value.password) {
        updateData.password = userForm.value.password;
      }

      const response = await userAPI.updateUser(
        editingUser.value.id,
        updateData,
      );

      if (response.status === "success") {
        alert(response.message);
        closeUserDialog();
        loadUsers();
      } else {
        alert("更新失败: " + response.message);
      }
    } else {
      // 新增模式
      console.log("➕ 创建用户:", userForm.value.username);

      const response = await userAPI.createUser(userForm.value);

      if (response.status === "success") {
        alert(response.message);
        closeUserDialog();
        loadUsers();
      } else {
        alert("创建失败: " + response.message);
      }
    }
  } catch (error) {
    console.error("❌ 操作失败:", error);
    alert("操作失败: " + error.message);
  } finally {
    isSaving.value = false;
  }
}

/**
 * 启用/禁用用户
 */
async function handleToggleStatus(user) {
  const action = user.is_active ? "禁用" : "启用";
  const newStatus = !user.is_active;

  if (!confirm(`确定要${action}用户 ${user.username} 吗？`)) {
    return;
  }

  try {
    console.log(`🔄 ${action}用户: ${user.username}`);

    const response = await userAPI.toggleUserStatus(user.id, newStatus);

    if (response.status === "success") {
      alert(response.message);
      loadUsers();
    } else {
      alert(`${action}失败: ` + response.message);
    }
  } catch (error) {
    console.error(`❌ ${action}用户失败:`, error);
    alert(`${action}失败: ` + error.message);
  }
}

/**
 * 删除用户
 */
async function handleDelete(user) {
  if (
    !confirm(
      `⚠️ 危险操作！\n确定要删除用户 ${user.username} 吗？\n此操作不可恢复！`,
    )
  ) {
    return;
  }

  if (
    !confirm(
      `再次确认：真的要删除用户 ${user.username} 吗？\n用户的所有数据（会话、消息）都会被删除！`,
    )
  ) {
    return;
  }

  try {
    console.log(`🗑️ 删除用户: ${user.username}`);

    const response = await userAPI.deleteUser(user.id);

    if (response.status === "success") {
      alert(response.message);
      loadUsers();
    } else {
      alert("删除失败: " + response.message);
    }
  } catch (error) {
    console.error("❌ 删除用户失败:", error);
    alert("删除失败: " + error.message);
  }
}
</script>

<style scoped>
.user-management {
  padding: 24px;
  background: #f5f5f5;
  height: 100%;
  overflow-y: auto;
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

.header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12px;
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
  transition: all 0.3s;
}

.refresh-btn:hover {
  background: #5568d3;
  transform: translateY(-2px);
}

.add-user-btn {
  padding: 10px 20px;
  background: #28a745;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;
}

.add-user-btn:hover {
  background: #218838;
  transform: translateY(-2px);
}

.loading,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #999;
  background: white;
  border-radius: 12px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
  opacity: 0.5;
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

tbody tr:hover {
  background: #f9fafb;
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

.edit-btn:hover {
  background: #bbdefb;
}

.disable-btn {
  background: #ffebee;
  color: #c62828;
}

.disable-btn:hover {
  background: #ffcdd2;
}

.enable-btn {
  background: #e8f5e9;
  color: #2e7d32;
}

.enable-btn:hover {
  background: #c8e6c9;
}

.delete-btn {
  background: #fce4ec;
  color: #e91e63;
}

.delete-btn:hover {
  background: #f8bbd0;
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #999;
}

.modal-body {
  padding: 24px;
  max-height: 60vh;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 20px; /* 增加底部间距 */
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px; /* 增加标签和输入框的间距 */
}

/* 复选框特殊处理 */
.form-group label input[type="checkbox"] {
  margin-right: 8px;
  width: 16px;
  height: 16px;
  vertical-align: middle;
}

/* 输入框样式 */
.form-group input[type="text"],
.form-group input[type="email"],
.form-group input[type="password"],
.form-group select {
  width: 100%;
  padding: 10px 12px;
  font-size: 14px;
  border: 1px solid #ddd;
  border-radius: 6px;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.form-group input:focus,
.form-group select:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* 下拉框样式 */
.form-group select {
  cursor: pointer;
  background-color: white;
  appearance: none; /* 移除默认样式 */
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23333' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 36px; /* 为下拉箭头留出空间 */
}

/* 模态框标题样式 */
.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

/* 模态框内容区域 */
.modal-body {
  padding: 24px;
  max-height: 60vh;
  overflow-y: auto;
}

/* 必填标记 */
.form-group label span.required {
  color: #ff4757;
  margin-left: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    margin: 20px auto;
  }

  .modal-body {
    padding: 16px;
  }

  .form-group label {
    font-size: 13px;
  }

  .form-group input,
  .form-group select {
    font-size: 13px;
    padding: 8px 10px;
  }
}

/* ========== ⭐⭐⭐ 优化：模态框底部按钮 ⭐⭐⭐ ========== */
.modal-footer {
  display: flex;
  justify-content: flex-end; /* ⭐ 按钮靠右对齐 */
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #eee;
  background: #fafafa; /* ⭐ 添加背景色区分 */
}

.modal-footer button {
  min-width: 100px; /* ⭐ 统一最小宽度 */
  padding: 10px 24px; /* ⭐ 增大内边距 */
  border: none;
  border-radius: 8px; /* ⭐ 更圆润的圆角 */
  font-size: 15px; /* ⭐ 稍微增大字号 */
  font-weight: 600; /* ⭐ 字体加粗 */
  cursor: pointer;
  transition: all 0.3s ease; /* ⭐ 平滑过渡 */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); /* ⭐ 添加阴影 */
}

/* 取消按钮 */
.cancel-btn {
  background: white;
  color: #666;
  border: 2px solid #ddd; /* ⭐ 添加边框 */
}

.cancel-btn:hover {
  background: #f5f5f5;
  border-color: #bbb;
  transform: translateY(-1px); /* ⭐ 轻微上浮 */
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.cancel-btn:active {
  transform: translateY(0); /* ⭐ 点击时恢复 */
}

/* 保存按钮 */
.save-btn {
  background: linear-gradient(
    135deg,
    #667eea 0%,
    #764ba2 100%
  ); /* ⭐ 渐变背景 */
  color: white;
  border: none;
}

.save-btn:hover:not(:disabled) {
  transform: translateY(-2px); /* ⭐ 更明显的上浮 */
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4); /* ⭐ 更强烈的阴影 */
}

.save-btn:active:not(:disabled) {
  transform: translateY(0);
}

.save-btn:disabled {
  background: #ccc; /* ⭐ 禁用状态灰色 */
  cursor: not-allowed;
  opacity: 0.6;
  box-shadow: none;
}

/* ========== 响应式优化 ========== */
@media (max-width: 768px) {
  .modal-footer {
    padding: 16px;
    gap: 8px;
  }

  .modal-footer button {
    min-width: 80px;
    padding: 8px 16px;
    font-size: 14px;
  }
}
</style>
