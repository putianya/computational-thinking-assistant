<!-- filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\components\analytics\OverviewPanel.vue -->
<template>
  <div class="overview-panel">
    <!-- 加载状态 -->
    <div v-if="analyticsStore.isLoading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i>
      <p>加载统计数据中...</p>
    </div>

    <!-- 统计卡片（垂直堆叠）-->
    <template v-else>
      <!-- ⭐ 学习时长 -->
      <div class="stat-card" @click="handleCardClick('duration')">
        <div class="stat-icon">📚</div>
        <div class="stat-content">
          <div class="stat-value">
            {{ analyticsStore.overview?.total_duration_hours || 0 }}
          </div>
          <div class="stat-label">学习时长（小时）</div>
        </div>
        <i class="arrow-icon fas fa-chevron-right"></i>
      </div>

      <!-- ⭐ 提问次数 -->
      <div class="stat-card" @click="handleCardClick('questions')">
        <div class="stat-icon">💬</div>
        <div class="stat-content">
          <div class="stat-value">
            {{ analyticsStore.overview?.question_count || 0 }}
          </div>
          <div class="stat-label">提问次数</div>
        </div>
        <i class="arrow-icon fas fa-chevron-right"></i>
      </div>

      <!-- ⭐ 代码提交 -->
      <div class="stat-card" @click="handleCardClick('code')">
        <div class="stat-icon">💻</div>
        <div class="stat-content">
          <div class="stat-value">
            {{ analyticsStore.overview?.code_count || 0 }}
          </div>
          <div class="stat-label">代码提交</div>
        </div>
        <i class="arrow-icon fas fa-chevron-right"></i>
      </div>

      <!-- ⭐ 代码正确率 -->
      <div class="stat-card" @click="handleCardClick('accuracy')">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-value">
            {{ analyticsStore.overview?.accuracy || 0 }}%
          </div>
          <div class="stat-label">代码正确率</div>
        </div>
        <i class="arrow-icon fas fa-chevron-right"></i>
      </div>

      <!-- ⭐ 活跃天数 -->
      <div class="stat-card" @click="handleCardClick('active_days')">
        <div class="stat-icon">📅</div>
        <div class="stat-content">
          <div class="stat-value">
            {{ analyticsStore.overview?.active_days || 0 }}
          </div>
          <div class="stat-label">活跃天数</div>
        </div>
        <i class="arrow-icon fas fa-chevron-right"></i>
      </div>

      <!-- ⭐ 知识点查看 -->
      <div class="stat-card" @click="handleCardClick('views')">
        <div class="stat-icon">👁️</div>
        <div class="stat-content">
          <div class="stat-value">
            {{ analyticsStore.overview?.view_count || 0 }}
          </div>
          <div class="stat-label">知识点查看</div>
        </div>
        <i class="arrow-icon fas fa-chevron-right"></i>
      </div>
    </template>
  </div>
</template>

<script setup>
import { useAnalyticsStore } from "../../stores/analytics";

const analyticsStore = useAnalyticsStore();

// ⭐⭐⭐ 定义 emit ⭐⭐⭐
const emit = defineEmits(["card-click"]);

// ⭐⭐⭐ 处理卡片点击 ⭐⭐⭐
function handleCardClick(cardType) {
  console.log("📌 OverviewPanel: 卡片点击 ->", cardType);
  emit("card-click", cardType); // ⭐ 触发事件
}
</script>

<style scoped>
/* ========== ⭐⭐⭐ 垂直堆叠布局 ⭐⭐⭐ ========== */
.overview-panel {
  display: flex;
  flex-direction: column; /* ⭐ 垂直排列 */
  gap: 12px; /* ⭐ 卡片间距 */
}

/* ========== 加载状态 ========== */
.loading-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.loading-state i {
  font-size: 48px;
  margin-bottom: 16px;
  color: #667eea;
}

/* ========== ⭐⭐⭐ 卡片样式优化 ⭐⭐⭐ ========== */
.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

/* ⭐ 悬停效果 */
.stat-card:hover {
  transform: translateY(-2px) scale(1.01);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
  border-left: 4px solid #667eea; /* ⭐ 左侧高亮边框 */
}

/* ⭐ 点击效果 */
.stat-card:active {
  transform: translateY(0) scale(0.99);
}

/* ========== 图标 ========== */
.stat-icon {
  font-size: 32px;
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  flex-shrink: 0;
}

/* ========== 内容区域 ========== */
.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 13px;
  color: #666;
  margin-top: 4px;
}

/* ========== ⭐⭐⭐ 右侧箭头图标 ⭐⭐⭐ ========== */
.arrow-icon {
  color: #ccc;
  font-size: 14px;
  transition: all 0.2s;
  flex-shrink: 0;
}

.stat-card:hover .arrow-icon {
  color: #667eea;
  transform: translateX(4px); /* ⭐ 悬停时向右移动 */
}

/* ========== 响应式 ========== */
@media (max-width: 768px) {
  .overview-panel {
    gap: 10px;
  }

  .stat-card {
    padding: 14px;
  }

  .stat-icon {
    font-size: 28px;
    width: 45px;
    height: 45px;
  }

  .stat-value {
    font-size: 20px;
  }

  .stat-label {
    font-size: 12px;
  }
}
</style>
