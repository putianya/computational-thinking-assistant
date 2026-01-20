<template>
  <div class="session-list">
    <!-- 顶部：新对话按钮 -->
    <div class="session-header">
      <button
        class="new-session-btn"
        @click="handleNewSession"
        title="开启新对话"
      >
        <i class="fas fa-plus"></i>
        <span>新对话</span>
      </button>
    </div>

    <!-- 会话列表 -->
    <div class="sessions-container">
      <!-- 有会话时显示列表 -->
      <div
        v-for="session in sessions"
        :key="session.session_id"
        class="session-item"
        :class="{ active: isCurrentSession(session.session_id) }"
        @click="handleSelectSession(session.session_id)"
      >
        <!-- 会话信息 -->
        <div class="session-info">
          <div class="session-icon">
            <i class="fas fa-comment-dots"></i>
          </div>
          <div class="session-content">
            <!-- ⭐ 修改：标题可编辑 -->
            <div class="session-title-wrapper">
              <!-- 正常显示模式 -->
              <div
                v-if="editingSessionId !== session.session_id"
                class="session-title"
                :title="session.title || '新对话'"
              >
                {{ session.title || "新对话" }}
              </div>

              <!-- 编辑模式 -->
              <input
                v-else
                ref="titleInput"
                v-model="editingTitle"
                type="text"
                class="session-title-input"
                maxlength="50"
                @click.stop
                @keyup.enter="confirmRename(session.session_id)"
                @keyup.esc="cancelRename"
                @blur="confirmRename(session.session_id)"
              />
            </div>

            <div class="session-meta">
              <span class="session-time">{{
                formatTime(session.updated_at)
              }}</span>
              <span v-if="session.message_count" class="session-count">
                {{ session.message_count }} 条消息
              </span>
            </div>
          </div>
        </div>

        <!-- ⭐ 修改：操作按钮区域 -->
        <div class="session-actions" @click.stop>
          <!-- 重命名按钮 -->
          <button
            class="action-btn rename-btn"
            @click="startRename(session.session_id, session.title)"
            title="重命名"
          >
            <i class="fas fa-edit"></i>
          </button>

          <!-- 删除按钮 -->
          <button
            class="action-btn delete-btn"
            @click="handleDeleteSession(session.session_id)"
            title="删除"
          >
            <i class="fas fa-trash-alt"></i>
          </button>
        </div>
      </div>

      <!-- 空状态：无会话时显示 -->
      <div v-if="sessions.length === 0" class="empty-state">
        <div class="empty-icon">
          <i class="fas fa-comments"></i>
        </div>
        <h3>暂无对话记录</h3>
        <p>点击上方"新对话"按钮开始聊天</p>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <ConfirmDialog
      v-if="showDeleteConfirm"
      title="确认删除"
      message="确定要删除这个会话吗？所有消息将被永久删除，此操作无法撤销。"
      confirmText="删除"
      cancelText="取消"
      :loading="isDeleting"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />
  </div>
</template>

<script setup>
import { computed, ref, nextTick } from "vue";
import { useChatStore } from "../stores/chat";
import ConfirmDialog from "./ConfirmDialog.vue";

const chatStore = useChatStore();

// ========== 数据 ==========
const sessions = computed(() => chatStore.sessions);
const currentSessionId = computed(() => chatStore.sessionId);

// 删除相关状态
const showDeleteConfirm = ref(false);
const sessionToDelete = ref(null);
const isDeleting = ref(false);

// 重命名相关状态
const editingSessionId = ref(null);
const editingTitle = ref("");
const titleInput = ref(null);
const isRenaming = ref(false); // ⭐ 新增：防止重复提交

/**
 * 判断是否为当前会话
 */
function isCurrentSession(sessionId) {
  return sessionId === currentSessionId.value;
}

/**
 * 创建新对话
 */
async function handleNewSession() {
  try {
    await chatStore.createNewSession();
    console.log("✅ 新对话已创建");
  } catch (error) {
    console.error("❌ 创建新对话失败:", error);
  }
}

/**
 * 选择/切换会话
 */
async function handleSelectSession(sessionId) {
  if (sessionId === currentSessionId.value) return;

  try {
    await chatStore.switchSession(sessionId);
    console.log("✅ 已切换到会话:", sessionId);
  } catch (error) {
    console.error("❌ 切换会话失败:", error);
  }
}

/**
 * 点击删除按钮 - 显示确认对话框
 */
function handleDeleteSession(sessionId) {
  sessionToDelete.value = sessionId;
  showDeleteConfirm.value = true;
}

/**
 * 确认删除 - 执行删除操作
 */
async function confirmDelete() {
  if (!sessionToDelete.value) return;

  try {
    isDeleting.value = true;
    console.log(`🗑️ 正在删除会话: ${sessionToDelete.value}`);

    const success = await chatStore.deleteSession(sessionToDelete.value);

    if (success) {
      console.log("✅ 会话已删除");
    } else {
      console.error("❌ 删除失败");
      alert("删除会话失败，请重试");
    }
  } catch (error) {
    console.error("❌ 删除会话出错:", error);
    alert("删除会话失败: " + (error.message || "未知错误"));
  } finally {
    isDeleting.value = false;
    showDeleteConfirm.value = false;
    sessionToDelete.value = null;
  }
}

/**
 * 取消删除
 */
function cancelDelete() {
  showDeleteConfirm.value = false;
  sessionToDelete.value = null;
}

/**
 * ⭐ 新增：开始重命名
 */
function startRename(sessionId, currentTitle) {
  editingSessionId.value = sessionId;
  editingTitle.value = currentTitle || "新对话";

  // 下一帧聚焦并选中文本
  nextTick(() => {
    if (titleInput.value && titleInput.value[0]) {
      const input = titleInput.value[0];
      input.focus();
      input.select();
    }
  });
}

/**
 * ⭐ 修复：确认重命名
 */
async function confirmRename(sessionId) {
  // ⭐ 1. 防止重复提交
  if (isRenaming.value) {
    console.log("⚠️ 正在重命名中，忽略重复请求");
    return;
  }

  // ⭐ 2. 验证标题
  const trimmedTitle = editingTitle.value.trim();

  if (!trimmedTitle) {
    console.warn("⚠️ 标题为空，忽略重命名");
    // 直接取消编辑，不弹窗提示
    cancelRename();
    return;
  }

  if (trimmedTitle.length > 50) {
    alert("标题长度不能超过50字符");
    return;
  }

  // ⭐ 3. 检查标题是否有变化
  const originalSession = sessions.value.find(
    (s) => s.session_id === sessionId,
  );
  if (originalSession && originalSession.title === trimmedTitle) {
    console.log("✅ 标题未改变，无需重命名");
    cancelRename();
    return;
  }

  // ⭐ 4. 执行重命名
  try {
    isRenaming.value = true; // 设置标记
    console.log(`✏️ 重命名会话: ${sessionId} -> ${trimmedTitle}`);

    const success = await chatStore.renameSession(sessionId, trimmedTitle);

    if (success) {
      console.log("✅ 重命名成功");
    } else {
      alert("重命名失败，请重试");
    }
  } catch (error) {
    console.error("❌ 重命名失败:", error);
    alert("重命名失败: " + (error.message || "未知错误"));
  } finally {
    // ⭐ 5. 退出编辑模式
    isRenaming.value = false;
    editingSessionId.value = null;
    editingTitle.value = "";
  }
}

/**
 * ⭐ 修复：取消重命名
 */
function cancelRename() {
  if (isRenaming.value) {
    console.log("⚠️ 正在重命名中，忽略取消请求");
    return;
  }

  editingSessionId.value = null;
  editingTitle.value = "";
}

/**
 * 格式化时间
 */
function formatTime(timestamp) {
  if (!timestamp) return "";

  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date;

  // 今天
  if (diff < 24 * 60 * 60 * 1000 && date.getDate() === now.getDate()) {
    return date.toLocaleTimeString("zh-CN", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  // 昨天
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  if (date.getDate() === yesterday.getDate()) {
    return "昨天";
  }

  // 本周内
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const days = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];
    return days[date.getDay()];
  }

  // 更早
  return date.toLocaleDateString("zh-CN", { month: "short", day: "numeric" });
}
</script>

<style scoped>
.session-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f8f9fa;
}

/* ========== 顶部区域 ========== */
.session-header {
  padding: 16px;
  border-bottom: 1px solid #e9ecef;
  background: white;
}

/* 新对话按钮 */
.new-session-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.new-session-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.new-session-btn:active {
  transform: translateY(0);
}

/* ========== 会话列表 ========== */
.sessions-container {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

/* 滚动条样式 */
.sessions-container::-webkit-scrollbar {
  width: 6px;
}

.sessions-container::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 3px;
}

.sessions-container::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

/* 会话项 */
.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  margin-bottom: 4px;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.session-item:hover {
  background: #f0f4ff;
  border-color: #e0e7ff;
}

.session-item.active {
  background: linear-gradient(135deg, #667eea10 0%, #764ba210 100%);
  border-color: #667eea;
  border-left: 3px solid #667eea;
}

/* 会话信息 */
.session-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.session-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f4ff;
  border-radius: 8px;
  color: #667eea;
  flex-shrink: 0;
}

.session-item.active .session-icon {
  background: #667eea;
  color: white;
}

.session-content {
  flex: 1;
  min-width: 0;
}

.session-title-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.session-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 4px;
  flex: 1;
}

.session-title-input {
  width: 100%;
  padding: 4px 8px;
  font-size: 14px;
  font-weight: 500;
  border: 2px solid #667eea;
  border-radius: 4px;
  outline: none;
  background: white;
  color: #333;
}

.session-title-input:focus {
  border-color: #764ba2;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.session-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #999;
}

.session-time::after {
  content: "•";
  margin-left: 8px;
}

.session-count {
  color: #667eea;
}

/* ========== 删除按钮 ========== */
.delete-btn {
  opacity: 0;
  padding: 8px;
  background: transparent;
  border: none;
  color: #ff4757;
  font-size: 14px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

/* 悬停会话时显示删除按钮 */
.session-item:hover .delete-btn {
  opacity: 1;
}

/* 删除按钮悬停效果 */
.delete-btn:hover {
  background: #cc0000;
  transform: scale(1.1);
}

/* ========== 空状态 ========== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: #999;
}

.empty-icon {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea20 0%, #764ba220 100%);
  border-radius: 50%;
  margin-bottom: 20px;
}

.empty-icon i {
  font-size: 36px;
  color: #667eea;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #666;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
  color: #999;
}

/* ========== 操作按钮区域 ========== */
.session-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.session-item:hover .session-actions {
  opacity: 1;
}

.action-btn {
  padding: 6px 8px;
  background: transparent;
  border: none;
  color: #999;
  font-size: 14px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.action-btn:hover {
  transform: scale(1.1);
}

.rename-btn:hover {
  background: #667eea;
  color: white;
}

.delete-btn:hover {
  background: #ff4757;
  color: white;
}
</style>
