<!-- filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\components\analytics\LearningAnalytics.vue -->
<template>
  <div class="learning-analytics">
    <!-- 顶部 Header -->
    <div class="analytics-header">
      <h2>📊 学习分析</h2>
      <div class="header-actions">
        <!-- 教师/管理员才显示学生选择 -->
        <select
          v-if="isTeacherOrAdmin"
          v-model="selectedStudent"
          @change="handleStudentChange"
          class="student-select"
        >
          <option :value="null">-- 选择学生 --</option>
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
          <option :value="7">最近 7 天</option>
          <option :value="30">最近 30 天</option>
          <option :value="90">最近 90 天</option>
        </select>

        <button
          @click="handleRefresh"
          :disabled="analyticsStore.isLoading"
          class="refresh-btn"
        >
          <i
            class="fas fa-sync-alt"
            :class="{ 'fa-spin': analyticsStore.isLoading }"
          ></i>
          刷新
        </button>
      </div>
    </div>

    <!-- Tab 切换 -->
    <div class="analytics-tabs">
      <button
        :class="['tab-btn', { active: activeTab === 'dashboard' }]"
        @click="activeTab = 'dashboard'"
      >
        <i class="fas fa-chart-bar"></i> 数据看板
      </button>
      <button
        :class="['tab-btn', { active: activeTab === 'report' }]"
        @click="activeTab = 'report'"
      >
        <i class="fas fa-file-alt"></i> 学情报告
      </button>
    </div>

    <!-- 数据看板 -->
    <div v-show="activeTab === 'dashboard'" class="analytics-content">
      <!-- 左侧：概览卡片 -->
      <div class="left-panel">
        <!-- 当前查看的学生信息 -->
        <div class="summary-info" v-if="isTeacherOrAdmin">
          <p>
            当前查看：<strong>{{ currentStudentName }}</strong>
          </p>
          <p>
            统计周期：<strong
              >最近 {{ analyticsStore.currentPeriod }} 天</strong
            >
          </p>
        </div>

        <!-- 概览卡片 -->
        <OverviewPanel @card-click="handleCardClick" />

        <!-- 学生排行榜（教师/管理员可见） -->
        <div
          class="student-ranking"
          v-if="isTeacherOrAdmin && analyticsStore.students.length > 0"
        >
          <h4>🏆 学生活跃排行</h4>
          <div
            v-for="(s, index) in analyticsStore.students.slice(0, 5)"
            :key="s.id"
            class="rank-item"
            @click="quickSelectStudent(s.id)"
          >
            <div class="rank-num" :class="getRankClass(index)">
              {{ index + 1 }}
            </div>
            <div class="rank-name">{{ s.nickname || s.username }}</div>
            <div class="rank-value">{{ s.active_days || 0 }}天</div>
          </div>
        </div>
      </div>

      <!-- 右侧：图表区域 -->
      <div class="right-panel">
        <!-- 未选择学生提示（教师/管理员） -->
        <div v-if="isTeacherOrAdmin && !selectedStudent" class="empty-chart">
          <div class="empty-icon">👈</div>
          <h3>请选择学生</h3>
          <p>在左侧选择学生后查看详细分析数据</p>
        </div>

        <!-- 未选择卡片提示 -->
        <div v-else-if="!analyticsStore.selectedCard" class="empty-chart">
          <div class="empty-icon">📊</div>
          <h3>点击左侧卡片</h3>
          <p>选择一个统计指标查看详细趋势图</p>
        </div>

        <!-- 图表内容 -->
        <div v-else class="chart-container">
          <!-- 学习时长趋势 -->
          <div v-if="analyticsStore.selectedCard === 'duration'">
            <h3>📚 学习时长趋势</h3>
            <TrendChart :data="analyticsStore.learningTrend" type="duration" />
          </div>

          <!-- 提问次数趋势 -->
          <div v-else-if="analyticsStore.selectedCard === 'questions'">
            <h3>💬 提问次数趋势</h3>
            <TrendChart :data="analyticsStore.learningTrend" type="questions" />
          </div>

          <!-- 代码提交趋势 -->
          <div v-else-if="analyticsStore.selectedCard === 'code'">
            <h3>💻 代码提交趋势</h3>
            <TrendChart :data="analyticsStore.learningTrend" type="code" />
          </div>

          <!-- 代码正确率 -->
          <div v-else-if="analyticsStore.selectedCard === 'accuracy'">
            <h3>✅ 代码正确率趋势</h3>
            <TrendChart :data="analyticsStore.learningTrend" type="accuracy" />
          </div>

          <!-- 活跃天数 / 热力图 -->
          <div v-else-if="analyticsStore.selectedCard === 'active_days'">
            <h3>📅 学习活跃热力图</h3>
            <ActivityHeatmap
              :data="analyticsStore.activityHeatmap || []"
              :days="analyticsStore.currentPeriod"
            />
          </div>

          <!-- 知识点分布 -->
          <div v-else-if="analyticsStore.selectedCard === 'views'">
            <h3>👁️ 知识点查看分布</h3>
            <WeaknessChart
              :data="analyticsStore.knowledgeMastery"
              type="views"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 学情报告 -->
    <div v-show="activeTab === 'report'" class="report-area">
      <ReportExport />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import { useAuthStore } from "../../stores/user";
import { useAnalyticsStore } from "../../stores/analytics";
import OverviewPanel from "./OverviewPanel.vue";
import TrendChart from "./TrendChart.vue";
import WeaknessChart from "./WeaknessChart.vue";
import ActivityHeatmap from "./ActivityHeatmap.vue";
import ReportExport from "./ReportExport.vue";

const authStore = useAuthStore();
const analyticsStore = useAnalyticsStore();

// ========== 响应式状态 ==========
const activeTab = ref("dashboard");
const selectedPeriod = ref(analyticsStore.currentPeriod);
const selectedStudent = ref(analyticsStore.selectedStudentId);

// ========== 计算属性 ==========
const isTeacherOrAdmin = computed(() =>
  authStore.hasAnyRole(["teacher", "admin"]),
);

const currentStudentName = computed(() => {
  if (!selectedStudent.value) return "全部学生";
  const s = analyticsStore.students.find((s) => s.id === selectedStudent.value);
  return s ? s.nickname || s.username : "未知学生";
});

// ========== 同步 store 状态变化 ==========
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

// ========== 生命周期 ==========
onMounted(async () => {
  console.log("📊 学习分析组件挂载");
  await analyticsStore.loadStudents();
  if (!analyticsStore.overview) {
    await analyticsStore.loadAllData(analyticsStore.currentPeriod);
  }
});

// ========== 事件处理 ==========
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

async function quickSelectStudent(userId) {
  selectedStudent.value = userId;
  await handleStudentChange();
}

function handleCardClick(cardType) {
  analyticsStore.setSelectedCard(cardType);
}

function getRankClass(index) {
  if (index === 0) return "gold";
  if (index === 1) return "silver";
  if (index === 2) return "bronze";
  return "";
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

/* ========== Header ========== */
.analytics-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.analytics-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.student-select,
.period-select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  outline: none;
  cursor: pointer;
  min-width: 140px;
}

.student-select {
  border-color: #667eea;
  background: #f0f4ff;
  color: #333;
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
.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ========== Tabs ========== */
.analytics-tabs {
  display: flex;
  gap: 8px;
  padding: 10px 16px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
}

.tab-btn {
  padding: 8px 20px;
  border: 1px solid #ddd;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.tab-btn:hover {
  border-color: #667eea;
  color: #667eea;
}
.tab-btn.active {
  background: #667eea;
  border-color: #667eea;
  color: white;
}

/* ========== Content ========== */
.analytics-content {
  flex: 1;
  display: flex;
  gap: 20px;
  padding: 20px;
  overflow: hidden;
}

/* ========== Left Panel ========== */
.left-panel {
  width: 280px;
  flex-shrink: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.left-panel::-webkit-scrollbar {
  width: 6px;
}
.left-panel::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 3px;
}

.summary-info {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.summary-info p {
  margin: 6px 0;
  font-size: 14px;
  color: #555;
}
.summary-info strong {
  color: #667eea;
}

.student-ranking {
  background: white;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.student-ranking h4 {
  margin: 0 0 12px 0;
  font-size: 15px;
  color: #333;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
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

/* ========== Right Panel ========== */
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

.empty-chart {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-chart h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
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
  margin: 0 0 16px 0;
  font-size: 17px;
  color: #333;
}

/* ========== Report Area ========== */
.report-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ========== 响应式 ========== */
@media (max-width: 1200px) {
  .left-panel {
    width: 240px;
  }
}

@media (max-width: 900px) {
  .analytics-content {
    flex-direction: column;
    overflow-y: auto;
  }
  .left-panel {
    width: 100%;
    overflow: visible;
  }
  .right-panel {
    min-height: 400px;
  }
}
</style>
