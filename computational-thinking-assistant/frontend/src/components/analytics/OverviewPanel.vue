<!-- filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\components\analytics\OverviewPanel.vue -->
<template>
  <div class="overview-panel">
    <!-- 加载状态 -->
    <div v-if="analyticsStore.isLoading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i>
      <p>加载统计数据中...</p>
    </div>

    <!-- 统计卡片 -->
    <template v-else>
      <div class="stat-card">
        <div class="stat-icon">📚</div>
        <div class="stat-content">
          <div class="stat-value">
            {{ analyticsStore.overview?.total_duration_hours || 0 }}
          </div>
          <div class="stat-label">学习时长（小时）</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">💬</div>
        <div class="stat-content">
          <div class="stat-value">
            {{ analyticsStore.overview?.question_count || 0 }}
          </div>
          <div class="stat-label">提问次数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">💻</div>
        <div class="stat-content">
          <div class="stat-value">
            {{ analyticsStore.overview?.code_count || 0 }}
          </div>
          <div class="stat-label">代码提交</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-value">
            {{ analyticsStore.overview?.accuracy || 0 }}%
          </div>
          <div class="stat-label">代码正确率</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">📅</div>
        <div class="stat-content">
          <div class="stat-value">
            {{ analyticsStore.overview?.active_days || 0 }}
          </div>
          <div class="stat-label">活跃天数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">👁️</div>
        <div class="stat-content">
          <div class="stat-value">
            {{ analyticsStore.overview?.view_count || 0 }}
          </div>
          <div class="stat-label">知识点查看</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { useAnalyticsStore } from "../../stores/analytics";

const analyticsStore = useAnalyticsStore();
</script>

<style scoped>
.overview-panel {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  padding: 20px;
}

.loading-state {
  grid-column: 1 / -1;
  text-align: center;
  padding: 40px;
  color: #999;
}

.loading-state i {
  font-size: 48px;
  margin-bottom: 16px;
  color: #667eea;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stat-icon {
  font-size: 36px;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

/* 响应式 */
@media (max-width: 768px) {
  .overview-panel {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
    padding: 12px;
  }

  .stat-card {
    padding: 15px;
    gap: 10px;
  }

  .stat-icon {
    font-size: 28px;
    width: 50px;
    height: 50px;
  }

  .stat-value {
    font-size: 22px;
  }

  .stat-label {
    font-size: 12px;
  }
}
</style>
