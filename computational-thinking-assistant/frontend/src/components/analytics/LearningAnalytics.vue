<!-- filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\components\analytics\LearningAnalytics.vue -->
<template>
  <div class="learning-analytics">
    <!-- 顶部工具栏 -->
    <div class="analytics-header">
      <h2>📊 学习数据分析</h2>
      <div class="header-actions">
        <select
          v-model="selectedStudent"
          @change="handleStudentChange"
          class="student-select"
        >
          <option :value="null">-- 全部学生汇总 --</option>
          <option
            v-for="s in analyticsStore.students"
            :key="s.id"
            :value="s.id"
          >
            {{ s.nickname || s.username }}
          </option>
        </select>

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

    <!-- 主内容区 -->
    <div class="analytics-content">
      <!-- 左侧：统计卡片 -->
      <div class="left-panel">
        <!-- 未选择学生时显示汇总 -->
        <div
          v-if="
            !selectedStudent &&
            analyticsStore.overview?.student_count !== undefined
          "
          class="summary-info"
        >
          <p>
            📚 共
            <strong>{{ analyticsStore.overview.student_count }}</strong> 名学生
          </p>
          <p>
            ⏱️ 总学习
            <strong>{{
              analyticsStore.overview.summary?.total_duration_hours || 0
            }}</strong>
            小时
          </p>
          <p>
            💬 总提问
            <strong>{{
              analyticsStore.overview.summary?.total_questions || 0
            }}</strong>
            次
          </p>
        </div>

        <!-- 选择了学生显示详情 -->
        <OverviewPanel v-if="selectedStudent" @card-click="handleCardClick" />

        <!-- 汇总模式下的学生排行 -->
        <div
          v-if="!selectedStudent && analyticsStore.overview?.students"
          class="student-ranking"
        >
          <h4>📋 学习时长排行</h4>
          <div
            v-for="(s, index) in analyticsStore.overview.students"
            :key="s.user_id"
            class="rank-item"
            @click="quickSelectStudent(s.user_id)"
          >
            <span class="rank-num" :class="getRankClass(index)">{{
              index + 1
            }}</span>
            <span class="rank-name">{{ s.nickname || s.username }}</span>
            <span class="rank-value">{{ s.total_duration_hours }}h</span>
          </div>
        </div>
      </div>

      <!-- 右侧：图表展示区 -->
      <div class="right-panel">
        <!-- 空状态：未选择学生 -->
        <div
          v-if="!analyticsStore.selectedCard && !selectedStudent"
          class="empty-chart"
        >
          <div class="empty-icon">📈</div>
          <h3>选择学生查看详细分析</h3>
          <p>从顶部下拉框选择学生，或点击左侧排行中的学生</p>
        </div>

        <!-- 空状态：已选择学生但未选择卡片 -->
        <div
          v-else-if="!analyticsStore.selectedCard && selectedStudent"
          class="empty-chart"
        >
          <div class="empty-icon">📈</div>
          <h3>点击左侧卡片查看详细图表</h3>
          <p>选中学生：{{ currentStudentName }}</p>
        </div>

        <!-- 📚 学习时长趋势（折线图） -->
        <div
          v-else-if="analyticsStore.selectedCard === 'duration'"
          class="chart-container"
        >
          <h3>📚 {{ currentStudentName }} - 学习时长趋势</h3>
          <TrendChart :data="analyticsStore.learningTrend" type="duration" />
        </div>

        <!-- 💬 提问次数趋势（柱状图） -->
        <div
          v-else-if="analyticsStore.selectedCard === 'questions'"
          class="chart-container"
        >
          <h3>💬 {{ currentStudentName }} - 提问次数趋势</h3>
          <TrendChart :data="analyticsStore.learningTrend" type="questions" />
        </div>

        <!-- 💻 代码提交（双轴折线图） -->
        <div
          v-else-if="analyticsStore.selectedCard === 'code'"
          class="chart-container"
        >
          <h3>💻 {{ currentStudentName }} - 代码提交趋势</h3>
          <TrendChart :data="analyticsStore.learningTrend" type="code" />
        </div>

        <!-- ✅ 代码正确率（仪表盘+趋势线） -->
        <div
          v-else-if="analyticsStore.selectedCard === 'accuracy'"
          class="chart-container"
        >
          <h3>✅ {{ currentStudentName }} - 代码正确率</h3>
          <TrendChart :data="analyticsStore.learningTrend" type="accuracy" />
        </div>

        <!-- 📅 活跃天数（日历热力图） -->
        <div
          v-else-if="analyticsStore.selectedCard === 'active_days'"
          class="chart-container"
        >
          <h3>📅 {{ currentStudentName }} - 活跃天数分布</h3>
          <ActivityHeatmap
            :data="analyticsStore.learningTrend"
            :days="Number(selectedPeriod)"
          />
        </div>

        <!-- 👁️ 知识点查看（横向柱状图） -->
        <div
          v-else-if="analyticsStore.selectedCard === 'views'"
          class="chart-container"
        >
          <h3>👁️ {{ currentStudentName }} - 知识点查看分布</h3>
          <WeaknessChart :data="analyticsStore.knowledgeMastery" type="views" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useAnalyticsStore } from "../../stores/analytics";
import OverviewPanel from "./OverviewPanel.vue";
import TrendChart from "./TrendChart.vue";
import WeaknessChart from "./WeaknessChart.vue";
import ActivityHeatmap from "./ActivityHeatmap.vue";

const analyticsStore = useAnalyticsStore();

const selectedPeriod = ref(analyticsStore.currentPeriod);
const selectedStudent = ref(analyticsStore.selectedStudentId);

watch(
  () => analyticsStore.selectedStudentId,
  (val) => {
    selectedStudent.value = val;
  },
);

watch(
  () => analyticsStore.currentPeriod,
  (val) => {
    selectedPeriod.value = val;
  },
);

const currentStudentName = computed(() => {
  if (!selectedStudent.value) return "全部学生";
  const s = analyticsStore.students.find((s) => s.id === selectedStudent.value);
  return s ? s.nickname || s.username : "未知学生";
});

function getRankClass(index) {
  if (index === 0) return "gold";
  if (index === 1) return "silver";
  if (index === 2) return "bronze";
  return "";
}

onMounted(async () => {
  console.log("📊 学习分析组件挂载");
  await analyticsStore.loadStudents();
  if (!analyticsStore.overview) {
    await analyticsStore.loadAllData(selectedPeriod.value);
  }
});

async function handlePeriodChange() {
  await analyticsStore.changePeriod(Number(selectedPeriod.value));
}

async function handleRefresh() {
  await analyticsStore.refreshData();
}

async function handleStudentChange() {
  analyticsStore.setSelectedCard(null);
  await analyticsStore.selectStudent(selectedStudent.value);
}

function quickSelectStudent(userId) {
  selectedStudent.value = userId;
  handleStudentChange();
}

function handleCardClick(cardType) {
  analyticsStore.setSelectedCard(cardType);
}
</script>

<style scoped>
.learning-analytics {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  overflow: hidden;
}

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

.student-select {
  padding: 8px 12px;
  border: 2px solid #667eea;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  cursor: pointer;
  background: #f0f4ff;
  color: #333;
  min-width: 160px;
}

.student-select:focus {
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

.period-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  cursor: pointer;
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
}

.analytics-content {
  flex: 1;
  display: flex;
  gap: 20px;
  padding: 20px;
  overflow: hidden;
}

.left-panel {
  width: 350px;
  flex-shrink: 0;
  overflow-y: auto;
  padding-right: 10px;
}

.left-panel::-webkit-scrollbar {
  width: 6px;
}
.left-panel::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 3px;
}

.right-panel {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.summary-info {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.summary-info p {
  margin: 8px 0;
  font-size: 15px;
  color: #555;
}
.summary-info strong {
  color: #667eea;
  font-size: 18px;
}

.student-ranking {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.student-ranking h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #333;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
}

.rank-item:hover {
  background: #f0f4ff;
  transform: translateX(4px);
}

.rank-num {
  width: 24px;
  height: 24px;
  background: #667eea;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: bold;
  flex-shrink: 0;
}

.rank-num.gold {
  background: #ffd700;
  color: #333;
}
.rank-num.silver {
  background: #c0c0c0;
  color: #333;
}
.rank-num.bronze {
  background: #cd7f32;
  color: white;
}

.rank-name {
  flex: 1;
  font-size: 14px;
  color: #333;
}
.rank-value {
  font-size: 14px;
  font-weight: bold;
  color: #667eea;
}

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

.chart-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chart-container h3 {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: #333;
  border-bottom: 2px solid #667eea;
  padding-bottom: 10px;
  flex-shrink: 0;
}

@media (max-width: 1200px) {
  .analytics-content {
    flex-direction: column;
  }
  .left-panel {
    width: 100%;
    max-height: 300px;
  }
  .right-panel {
    min-height: 400px;
  }
}
</style>
