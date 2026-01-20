<template>
  <teleport to="body">
    <div class="modal-overlay" @click="handleCancel">
      <div class="modal-content" @click.stop>
        <!-- 头部 -->
        <div class="modal-header">
          <h3>{{ title }}</h3>
          <button class="modal-close" @click="handleCancel">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <!-- 内容 -->
        <div class="modal-body">
          <div class="warning-icon">
            <i class="fas fa-exclamation-triangle"></i>
          </div>
          <p class="message">{{ message }}</p>
        </div>

        <!-- 底部按钮 -->
        <div class="modal-footer">
          <button class="btn-cancel" @click="handleCancel" :disabled="loading">
            {{ cancelText }}
          </button>
          <button
            class="btn-confirm"
            @click="handleConfirm"
            :disabled="loading"
          >
            <i v-if="loading" class="fas fa-spinner fa-spin"></i>
            <span>{{ loading ? "处理中..." : confirmText }}</span>
          </button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
const props = defineProps({
  title: {
    type: String,
    default: "确认操作",
  },
  message: {
    type: String,
    default: "确定要执行此操作吗？",
  },
  confirmText: {
    type: String,
    default: "确认",
  },
  cancelText: {
    type: String,
    default: "取消",
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["confirm", "cancel"]);

function handleConfirm() {
  emit("confirm");
}

function handleCancel() {
  if (!props.loading) {
    emit("cancel");
  }
}
</script>

<style scoped>
/* 遮罩层 */
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
  z-index: 9999;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* 对话框内容 */
.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 400px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
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

/* 头部 */
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.modal-close {
  background: none;
  border: none;
  font-size: 18px;
  color: #999;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s;
}

.modal-close:hover {
  background: #f5f5f5;
  color: #333;
}

/* 内容 */
.modal-body {
  padding: 24px 20px;
  text-align: center;
}

.warning-icon {
  width: 60px;
  height: 60px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff3cd;
  border-radius: 50%;
  color: #ffc107;
  font-size: 28px;
}

.message {
  margin: 0;
  font-size: 15px;
  color: #555;
  line-height: 1.6;
}

/* 底部按钮 */
.modal-footer {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #eee;
}

.modal-footer button {
  flex: 1;
  padding: 12px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.btn-cancel {
  background: #f5f5f5;
  border: 1px solid #ddd;
  color: #666;
}

.btn-cancel:hover:not(:disabled) {
  background: #eee;
}

.btn-confirm {
  background: #ff4757;
  border: none;
  color: white;
}

.btn-confirm:hover:not(:disabled) {
  background: #ff3344;
}

.btn-confirm:disabled,
.btn-cancel:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>
