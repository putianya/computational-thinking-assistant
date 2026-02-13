<!-- filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\components\analytics\LearningAnalytics.vue -->
<template>
  <div class="learning-analytics">
    <!-- 顶部工具栏 -->
    <div class="analytics-header">
      <h2>📊 学习数据分析</h2>
      <div class="header-actions">
        <select
          v-model="selectedPeriod"
          @change="handlePeriodChange"
          class="period-select"
        >
          <option value="7">最近7天</option>
          <option value="30">最近30天</option>
          <option value="90">最近90天</option>
        </select>

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

    <!-- ⭐⭐⭐ 主内容区：左侧卡片 + 右侧图表 ⭐⭐⭐ -->
    <div class="analytics-content">
      <!-- 左侧：统计卡片（垂直堆叠 + 可滚动） -->
      <div class="left-panel">
        <OverviewPanel @card-click="handleCardClick" />
      </div>

      <!-- 右侧：图表展示区 -->
      <div class="right-panel">
        <!-- 空状态（未选择卡片） -->
        <div v-if="!selectedCard" class="empty-chart">
          <div class="empty-icon">📈</div>
          <h3>选择左侧卡片查看详细图表</h3>
          <p>点击任意统计卡片，右侧将展示对应的数据可视化图表</p>
        </div>

        <!-- 学习时长趋势图 -->
        <div v-else-if="selectedCard === 'duration'" class="chart-container">
          <h3>📚 学习时长趋势</h3>
          <TrendChart :data="analyticsStore.learningTrend" type="duration" />
        </div>

        <!-- 提问次数趋势图 -->
        <div v-else-if="selectedCard === 'questions'" class="chart-container">
          <h3>💬 提问次数趋势</h3>
          <TrendChart :data="analyticsStore.learningTrend" type="questions" />
        </div>

        <!-- 代码提交趋势图 -->
        <div v-else-if="selectedCard === 'code'" class="chart-container">
          <h3>💻 代码提交趋势</h3>
          <TrendChart :data="analyticsStore.learningTrend" type="code" />
        </div>

        <!-- 正确率趋势图 -->
        <div v-else-if="selectedCard === 'accuracy'" class="chart-container">
          <h3>✅ 代码正确率趋势</h3>
          <TrendChart :data="analyticsStore.learningTrend" type="accuracy" />
        </div>

        <!-- 活跃天数日历热力图 -->
        <div v-else-if="selectedCard === 'active_days'" class="chart-container">
          <h3>📅 活跃天数分布</h3>
          <div class="heatmap-placeholder">
            <p>🔧 日历热力图开发中...</p>
          </div>
        </div>

        <!-- 知识点查看统计 -->
        <div v-else-if="selectedCard === 'views'" class="chart-container">
          <h3>👁️ 知识点查看分布</h3>
          <WeaknessChart :data="analyticsStore.knowledgeMastery" type="views" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useAnalyticsStore } from "../../stores/analytics";
import OverviewPanel from "./OverviewPanel.vue";
import TrendChart from "./TrendChart.vue";
import WeaknessChart from "./WeaknessChart.vue";

const analyticsStore = useAnalyticsStore();
const selectedPeriod = ref(30);
const selectedCard = ref(null); // ⭐ 当前选中的卡片

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

// ⭐⭐⭐ 处理卡片点击 ⭐⭐⭐
function handleCardClick(cardType) {
  console.log("🖱️ 点击卡片:", cardType);
  selectedCard.value = cardType; // ⭐ 关键：更新选中状态
}
</script>

<style scoped>
/* ========== 整体布局 ========== */
.learning-analytics {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  overflow: hidden; /* ⭐ 关键：防止整体滚动 */
}

/* ========== 顶部工具栏 ========== */
.analytics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0; /* ⭐ 防止被压缩 */
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

/* ========== ⭐⭐⭐ 主内容区布局（修复版）⭐⭐⭐ ========== */
.analytics-content {
  flex: 1;
  display: flex;
  gap: 20px;
  padding: 20px;
  overflow: hidden; /* ⭐ 关键：子元素自己处理滚动 */
}

/* ========== 左侧面板（垂直堆叠 + 可滚动）========== */
.left-panel {
  width: 350px; /* ⭐ 固定宽度 */
  flex-shrink: 0; /* ⭐ 防止被压缩 */
  overflow-y: auto; /* ⭐ 关键：左侧可滚动 */
  overflow-x: hidden;
  padding-right: 10px; /* ⭐ 为滚动条留出空间 */
}

/* ⭐⭐⭐ 美化滚动条 ⭐⭐⭐ */
.left-panel::-webkit-scrollbar {
  width: 6px;
}

.left-panel::-webkit-scrollbar-track {
  background: transparent;
}

.left-panel::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 3px;
}

.left-panel::-webkit-scrollbar-thumb:hover {
  background: #a0aec0;
}

/* ========== 右侧面板（图表区域）========== */
.right-panel {
  flex: 1; /* ⭐ 占据剩余空间 */
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow-y: auto; /* ⭐ 图表区域可滚动 */
  display: flex;
  flex-direction: column;
}

/* ========== 空状态 ========== */
.empty-chart {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #999;
}

.empty-icon {
  font-size: 80px;
  margin-bottom: 20px;
  opacity: 0.5;
}

.empty-chart h3 {
  margin: 0 0 12px 0;
  font-size: 20px;
  color: #666;
}

.empty-chart p {
  margin: 0;
  font-size: 14px;
}

/* ========== 图表容器 ========== */
.chart-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0; /* ⭐ 允许子元素缩小 */
}

.chart-container h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: #333;
  border-bottom: 2px solid #667eea;
  padding-bottom: 10px;
  flex-shrink: 0; /* ⭐ 标题不缩小 */
}

/* ========== 占位图表 ========== */
.heatmap-placeholder {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px dashed #ddd;
  border-radius: 8px;
  color: #999;
  background: #f9f9f9;
}

/* ========== 响应式 ========== */
@media (max-width: 1200px) {
  .analytics-content {
    flex-direction: column; /* ⭐ 小屏幕改为上下排列 */
  }

  .left-panel {
    width: 100%; /* ⭐ 左侧占满宽度 */
    max-height: 300px; /* ⭐ 限制高度 */
    overflow-y: auto;
  }

  .right-panel {
    min-height: 400px; /* ⭐ 确保图表区域有足够高度 */
  }
}

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

  .left-panel {
    max-height: 250px;
  }
}
</style>
