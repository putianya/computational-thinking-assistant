<template>
  <div class="session-list">
    <!-- ========== 新建会话按钮 ========== -->
    <div class="session-list-header">
      <button class="new-session-btn" @click="handleNewSession" :disabled="isCreating">
        <i class="fas fa-plus"></i>
        <span>新对话</span>
      </button>
    </div>

    <!-- ========== 加载状态 ========== -->
    <div v-if="chatStore.isLoadingSessions" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i>
      <span>加载中...</span>
    </div>

    <!-- ========== 会话列表 ========== -->
    <div v-else class="session-list-content">
      <!-- 无会话提示 -->
      <div v-if="sessions.length === 0" class="empty-state">
        <i class="fas fa-comments"></i>
        <p>暂无会话</p>
        <p class="hint">点击"新对话"开始聊天</p>
      </div>

      <!-- 会话列表 -->
      <div v-else class="sessions">
        <div
          v-for="session in sessions"
          :key="session.id"
          class="session-item"
          :class="{ active: session.is_active }"
          @click="handleSelectSession(session.session_id)"
        >
          <!-- 会话图标 -->
          <div class="session-icon">
            <i :class="session.is_active ? 'fas fa-comment-dots' : 'fas fa-comment'"></i>
          </div>

          <!-- 会话信息 -->
          <div class="session-info">
            <div class="session-title">
              {{ session.title || '新对话' }}
            </div>
            <div class="session-meta">
              <span class="session-time">{{ formatTime(session.updated_at) }}</span>
              <span v-if="session.message_count" class="session-count">
                {{ Math.floor(session.message_count / 2) }} 轮对话
              </span>
            </div>
          </div>

          <!-- 删除按钮 -->
          <button
            v-if="!session.is_active"
            class="delete-btn"
            @click.stop="handleDeleteSession(session.session_id, $event)"
            title="删除会话"
          >
            <i class="fas fa-trash-alt"></i>
          </button>

          <!-- 当前会话标记 -->
          <div v-if="session.is_active" class="active-indicator">
            <i class="fas fa-circle"></i>
          </div>
        </div>
      </div>
    </div>

    <!-- ========== 确认删除对话框 ========== -->
    <teleport to="body">
      <div v-if="showDeleteConfirm" class="modal-overlay" @click="cancelDelete">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <h3>确认删除</h3>
            <button class="modal-close" @click="cancelDelete">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="modal-body">
            <p>确定要删除这个会话吗？</p>
            <p class="warning">此操作无法撤销，所有消息将被永久删除。</p>
          </div>
          <div class="modal-footer">
            <button class="btn-cancel" @click="cancelDelete">取消</button>
            <button class="btn-confirm" @click="confirmDelete" :disabled="isDeleting">
              <i v-if="isDeleting" class="fas fa-spinner fa-spin"></i>
              <span>{{ isDeleting ? '删除中...' : '确认删除' }}</span>
            </button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import { useChatStore } from '../stores/chat';

const chatStore = useChatStore();

// ========== 数据 ==========
const sessions = computed(() => chatStore.sessions);
const currentSession = computed(() => chatStore.currentSession);

const isCreating = ref(false);
const isDeleting = ref(false);
const showDeleteConfirm = ref(false);
const sessionToDelete = ref(null);

// ========== 方法 ==========

/**
 * 创建新会话
 */
async function handleNewSession() {
  try {
    isCreating.value = true;
    console.log('📝 创建新会话...');
    
    await chatStore.createNewSession();
    
    console.log('✅ 新会话已创建');
  } catch (error) {
    console.error('❌ 创建新会话失败:', error);
    alert('创建新会话失败，请重试');
  } finally {
    isCreating.value = false;
  }
}

/**
 * 切换会话
 */
async function handleSelectSession(sessionId) {
  // 如果点击的就是当前会话，不处理
  if (currentSession.value?.session_id === sessionId) {
    console.log('⚠️ 已经是当前会话');
    return;
  }

  try {
    console.log(`🔄 切换到会话: ${sessionId}`);
    
    await chatStore.switchSession(sessionId);
    
    console.log('✅ 会话已切换');
  } catch (error) {
    console.error('❌ 切换会话失败:', error);
    alert('切换会话失败，请重试');
  }
}

/**
 * 删除会话（显示确认对话框）
 */
function handleDeleteSession(sessionId, event) {
  event.stopPropagation(); // 阻止触发会话切换
  
  sessionToDelete.value = sessionId;
  showDeleteConfirm.value = true;
}

/**
 * 确认删除
 */
async function confirmDelete() {
  if (!sessionToDelete.value) return;

  try {
    isDeleting.value = true;
    console.log(`🗑️ 删除会话: ${sessionToDelete.value}`);
    
    await chatStore.deleteSession(sessionToDelete.value);
    
    console.log('✅ 会话已删除');
    
    // 关闭对话框
    showDeleteConfirm.value = false;
    sessionToDelete.value = null;
  } catch (error) {
    console.error('❌ 删除会话失败:', error);
    alert('删除会话失败，请重试');
  } finally {
    isDeleting.value = false;
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
 * 格式化时间
 */
function formatTime(timeString) {
  if (!timeString) return '';

  const date = new Date(timeString);
  const now = new Date();
  const diff = now - date;

  // 今天
  if (diff < 24 * 60 * 60 * 1000 && now.getDate() === date.getDate()) {
    return `今天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
  }

  // 昨天
  const yesterday = new Date(now);
  yesterday.setDate(yesterday.getDate() - 1);
  if (date.getDate() === yesterday.getDate()) {
    return `昨天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
  }

  // 一周内
  if (diff < 7 * 24 * 60 * 60 * 1000) {
    const days = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    return `${days[date.getDay()]} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
  }

  // 更早
  return `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')}`;
}
</script>

<style scoped>
.session-list {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f8f9fa;
}

/* ========== 头部：新建会话按钮 ========== */
.session-list-header {
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
}

.new-session-btn {
  width: 100%;
  padding: 12px 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;
}

.new-session-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.new-session-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ========== 加载状态 ========== */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
  color: #999;
  gap: 8px;
}

.loading-state i {
  font-size: 24px;
}

/* ========== 空状态 ========== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 16px;
  color: #999;
  text-align: center;
}

.empty-state i {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state p {
  margin: 4px 0;
  font-size: 14px;
}

.empty-state .hint {
  font-size: 12px;
  color: #bbb;
}

/* ========== 会话列表 ========== */
.session-list-content {
  flex: 1;
  overflow-y: auto;
}

.sessions {
  padding: 8px;
}

/* ========== 会话项 ========== */
.session-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  margin-bottom: 4px;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  border-left: 3px solid transparent;
}

.session-item:hover {
  background: #f5f7ff;
  transform: translateX(2px);
}

/* ⭐ 当前活跃会话高亮 */
.session-item.active {
  background: rgba(102, 126, 234, 0.1);
  border-left-color: #667eea;
}

.session-item.active:hover {
  background: rgba(102, 126, 234, 0.15);
}

/* 会话图标 */
.session-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
  flex-shrink: 0;
}

.session-item.active .session-icon {
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.4);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(102, 126, 234, 0);
  }
}

/* 会话信息 */
.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-item.active .session-title {
  color: #667eea;
}

.session-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #999;
}

.session-time {
  flex-shrink: 0;
}

.session-count {
  flex-shrink: 0;
  padding: 2px 6px;
  background: #f0f0f0;
  border-radius: 10px;
  font-size: 11px;
}

.session-item.active .session-count {
  background: rgba(102, 126, 234, 0.2);
  color: #667eea;
}

/* 删除按钮 */
.delete-btn {
  opacity: 0;
  padding: 6px;
  background: transparent;
  border: none;
  color: #ff4757;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.session-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: #ffe5e8;
  transform: scale(1.1);
}

/* 当前会话标记 */
.active-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #667eea;
  flex-shrink: 0;
  animation: blink 1.5s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* ========== 确认删除对话框 ========== */
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
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  color: #333;
}

.modal-close {
  background: transparent;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 20px;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close:hover {
  color: #333;
}

.modal-body {
  padding: 24px;
}

.modal-body p {
  margin: 0 0 12px;
  color: #333;
  font-size: 14px;
}

.modal-body .warning {
  color: #ff4757;
  font-size: 13px;
}

.modal-footer {
  display: flex;
  gap: 12px;
  padding: 16px 24px 20px;
  border-top: 1px solid #e0e0e0;
}

.btn-cancel,
.btn-confirm {
  flex: 1;
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.btn-cancel {
  background: #f0f0f0;
  color: #666;
}

.btn-cancel:hover {
  background: #e0e0e0;
}

.btn-confirm {
  background: #ff4757;
  color: white;
}

.btn-confirm:hover:not(:disabled) {
  background: #ff3344;
  transform: translateY(-1px);
}

.btn-confirm:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ========== 滚动条样式 ========== */
.session-list-content::-webkit-scrollbar {
  width: 6px;
}

.session-list-content::-webkit-scrollbar-track {
  background: transparent;
}

.session-list-content::-webkit-scrollbar-thumb {
  background: #d0d0d0;
  border-radius: 3px;
}

.session-list-content::-webkit-scrollbar-thumb:hover {
  background: #b0b0b0;
}
</style>