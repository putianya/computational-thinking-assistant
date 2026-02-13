<!-- filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\components\analytics\LearningAnalytics.vue -->
<template>
  <div class="learning-analytics">
    <!-- 顶部工具栏 -->
    <div class="analytics-header">
      <h2>📊 学习数据分析</h2>
      <div class="header-actions">
        <!-- 时间范围选择 -->
        <select
          v-model="selectedPeriod"
          @change="handlePeriodChange"
          class="period-select"
        >
          <option value="7">最近7天</option>
          <option value="30">最近30天</option>
          <option value="90">最近90天</option>
        </select>

        <!-- 刷新按钮 -->
        <button
          @click="handleRefresh"
          :disabled="analyticsStore.isLoading"
          class="refresh-btn"
        >
          <i
            :class="[
              'fas fa-sync-alt',
              { 'fa-spin': analyticsStore.isLoading },
            ]"
          ></i>
          刷新
        </button>
      </div>
    </div>

    <!-- 概览面板 -->
    <OverviewPanel />

    <!-- 学习趋势图（TODO: 后续实现） -->
    <!-- <TrendChart /> -->

    <!-- 薄弱环节分析（TODO: 后续实现） -->
    <!-- <WeaknessChart /> -->

    <!-- 空状态提示 -->
    <div
      v-if="!analyticsStore.isLoading && !analyticsStore.overview"
      class="empty-state"
    >
      <div class="empty-icon">📈</div>
      <h3>暂无学习数据</h3>
      <p>开始学习后，这里将展示您的学习分析数据</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useAnalyticsStore } from "../../stores/analytics";
import OverviewPanel from "./OverviewPanel.vue";
// import TrendChart from "./TrendChart.vue";
// import WeaknessChart from "./WeaknessChart.vue";

const analyticsStore = useAnalyticsStore();
const selectedPeriod = ref(30);

onMounted(async () => {
  console.log("📊 学习分析组件挂载");
  await analyticsStore.loadAllData(selectedPeriod.value);
});

async function handlePeriodChange() {
  console.log("📅 切换时间范围:", selectedPeriod.value);
  await analyticsStore.changePeriod(selectedPeriod.value);
}

async function handleRefresh() {
  console.log("🔄 刷新数据");
  await analyticsStore.refreshData();
}
</script>

<style scoped>
.learning-analytics {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  overflow-y: auto;
}

/* 顶部工具栏 */
.analytics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.analytics-header h2 {
  margin: 0;
  font-size: 22px;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.period-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  cursor: pointer;
  transition: border-color 0.2s;
}

.period-select:hover {
  border-color: #667eea;
}

.period-select:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.refresh-btn {
  padding: 8px 16px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: #5568d3;
  transform: translateY(-2px);
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 空状态 */
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  font-size: 80px;
  margin-bottom: 20px;
  opacity: 0.5;
}

.empty-state h3 {
  margin: 0 0 12px 0;
  font-size: 20px;
  color: #666;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
  color: #999;
}

/* 响应式 */
@media (max-width: 768px) {
  .analytics-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
}
</style>
