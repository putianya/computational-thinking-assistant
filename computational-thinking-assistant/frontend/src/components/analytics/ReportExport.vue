<!-- filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\components\analytics\ReportExport.vue -->
<template>
  <div class="report-export">
    <!-- 工具栏 -->
    <div class="export-toolbar">
      <div class="toolbar-left">
        <select v-model="selectedDays" class="period-select">
          <option :value="7">最近 7 天</option>
          <option :value="30">最近 30 天</option>
          <option :value="90">最近 90 天</option>
        </select>

        <select
          v-if="isTeacherOrAdmin"
          v-model="selectedUserId"
          class="student-select"
        >
          <option :value="null">-- 选择学生 --</option>
          <option v-for="s in students" :key="s.id" :value="s.id">
            {{ s.nickname || s.username }}
          </option>
        </select>

        <button @click="loadReport" :disabled="isLoading" class="btn-refresh">
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': isLoading }"></i>
          刷新预览
        </button>
      </div>

      <div class="toolbar-right">
        <!-- ⭐ 直接下载 PDF，不再用 window.print() -->
        <button
          @click="downloadPDF"
          :disabled="isDownloading || !report"
          class="btn-download"
        >
          <i
            class="fas"
            :class="isDownloading ? 'fa-spinner fa-spin' : 'fa-file-pdf'"
          ></i>
          {{ isDownloading ? "生成中..." : "下载 PDF" }}
        </button>
      </div>
    </div>

    <!-- 加载中 -->
    <div v-if="isLoading" class="loading-state">
      <i class="fas fa-spinner fa-spin"></i>
      <p>加载报告数据中...</p>
    </div>

    <!-- 错误 -->
    <div v-else-if="error" class="error-state">
      <i class="fas fa-exclamation-circle"></i>
      <p>{{ error }}</p>
      <button @click="loadReport" class="btn-retry">重试</button>
    </div>

    <!-- 空状态 -->
    <div v-else-if="!report" class="empty-state">
      <div class="empty-icon">📋</div>
      <h3>点击"刷新预览"加载报告</h3>
      <p>加载后可预览报告内容并下载 PDF</p>
      <button @click="loadReport" class="btn-generate">
        <i class="fas fa-chart-bar"></i> 生成报告
      </button>
    </div>

    <!-- 报告预览 -->
    <div v-else class="report-content" ref="reportRef">
      <!-- 封面 -->
      <div class="report-cover">
        <div class="cover-logo">📊</div>
        <h1 class="cover-title">学情分析报告</h1>
        <p class="cover-subtitle">计算思维课程助手系统</p>
        <div class="cover-meta">
          <span
            >学生：{{
              report.user_info?.nickname ||
              report.user_info?.username ||
              report.user_info?.name ||
              "—"
            }}</span
          >
          <span
            >统计周期：最近
            {{ report.overview?.period_days || selectedDays }} 天</span
          >
          <span>生成时间：{{ formatDate(report.generated_at) }}</span>
        </div>
        <!-- 综合得分 -->
        <div v-if="report.score" class="cover-score">
          <div class="score-number">{{ Math.round(report.score.total) }}</div>
          <div class="score-grade">{{ report.score.grade }}</div>
          <div class="score-text">{{ report.score.grade_text }}</div>
        </div>
      </div>

      <!-- 一、学习概览 -->
      <div class="report-section">
        <h2 class="section-title">一、学习概览</h2>
        <div class="overview-grid">
          <div class="overview-card">
            <div class="card-icon">📚</div>
            <div class="card-value">
              {{ report.overview?.total_duration_hours?.toFixed(1) || 0 }}
            </div>
            <div class="card-label">学习时长（小时）</div>
          </div>
          <div class="overview-card">
            <div class="card-icon">💬</div>
            <div class="card-value">
              {{ report.overview?.question_count || 0 }}
            </div>
            <div class="card-label">提问次数</div>
          </div>
          <div class="overview-card">
            <div class="card-icon">💻</div>
            <div class="card-value">{{ report.overview?.code_count || 0 }}</div>
            <div class="card-label">代码提交</div>
          </div>
          <div class="overview-card">
            <div class="card-icon">✅</div>
            <div class="card-value">
              {{ report.overview?.accuracy?.toFixed(1) || 0 }}%
            </div>
            <div class="card-label">代码正确率</div>
          </div>
          <div class="overview-card">
            <div class="card-icon">📅</div>
            <div class="card-value">
              {{ report.overview?.active_days || 0 }}
            </div>
            <div class="card-label">活跃天数</div>
          </div>
          <div class="overview-card">
            <div class="card-icon">👁️</div>
            <div class="card-value">{{ report.overview?.view_count || 0 }}</div>
            <div class="card-label">知识点查看</div>
          </div>
        </div>
      </div>

      <!-- 二、综合评分 -->
      <div v-if="report.score" class="report-section">
        <h2 class="section-title">二、综合评分</h2>
        <div class="score-breakdown">
          <div v-for="(max, key) in scoreMax" :key="key" class="score-item">
            <span class="score-label">{{ scoreLabels[key] }}</span>
            <div class="score-bar-wrapper">
              <div
                class="score-bar"
                :class="`bar-${key}`"
                :style="{
                  width: (report.score.breakdown[key] / max) * 100 + '%',
                }"
              ></div>
            </div>
            <span class="score-val">
              {{ report.score.breakdown[key]?.toFixed(1) }} / {{ max }}
            </span>
          </div>
        </div>
      </div>

      <!-- 三、知识点掌握 -->
      <div v-if="report.knowledge_mastery?.length" class="report-section">
        <h2 class="section-title">三、知识点掌握情况</h2>
        <table class="report-table">
          <thead>
            <tr>
              <th>知识点</th>
              <th>查看次数</th>
              <th>掌握程度</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in report.knowledge_mastery" :key="item.topic">
              <td>{{ item.topic }}</td>
              <td>{{ item.total_count }} 次</td>
              <td>
                <div class="mastery-bar-wrapper">
                  <div
                    class="mastery-bar"
                    :class="getMasteryClass(item.mastery)"
                    :style="{ width: (item.mastery || 0) + '%' }"
                  ></div>
                </div>
              </td>
              <td>
                <span
                  class="mastery-badge"
                  :class="getMasteryClass(item.mastery)"
                >
                  {{ getMasteryText(item.mastery) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- ⭐ 新增：四、知识块引用热度 -->
      <div
        v-if="report.knowledge_chunk_stats?.items?.length > 0"
        class="report-section"
      >
        <h2 class="section-title">四、知识块引用热度</h2>
        <div
          class="overview-grid"
          style="grid-template-columns: repeat(2, 1fr); margin-bottom: 16px"
        >
          <div class="overview-card">
            <div class="card-icon">🔥</div>
            <div class="card-value">
              {{ report.knowledge_chunk_stats.total_retrieved || 0 }}
            </div>
            <div class="card-label">总引用次数</div>
          </div>
          <div class="overview-card">
            <div class="card-icon">📚</div>
            <div class="card-value">
              {{ report.knowledge_chunk_stats.total_chunks || 0 }}
            </div>
            <div class="card-label">上榜知识块数</div>
          </div>
        </div>
        <table class="report-table">
          <thead>
            <tr>
              <th style="width: 50px">排名</th>
              <th>来源</th>
              <th>章节</th>
              <th style="width: 80px">引用次数</th>
              <th style="width: 60px">占比</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(item, idx) in report.knowledge_chunk_stats.items.slice(
                0,
                10,
              )"
              :key="item.chunk_id"
            >
              <td style="text-align: center">
                {{
                  idx === 0
                    ? "🥇"
                    : idx === 1
                      ? "🥈"
                      : idx === 2
                        ? "🥉"
                        : idx + 1
                }}
              </td>
              <td>{{ item.source || "—" }}</td>
              <td>{{ item.chapter || "—" }}</td>
              <td style="text-align: center">
                <strong>{{ item.retrieved_count }}</strong> 次
              </td>
              <td style="text-align: center">{{ item.heat_rate }}%</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 五、薄弱环节 -->
      <div v-if="report.weaknesses?.weak_topics?.length" class="report-section">
        <h2 class="section-title">五、薄弱环节分析</h2>
        <h3 class="subsection-title">薄弱知识点（正确率 &lt; 60%）</h3>
        <table class="report-table">
          <thead>
            <tr>
              <th>知识点</th>
              <th>正确率</th>
              <th>练习次数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in report.weaknesses.weak_topics" :key="t.topic">
              <td>{{ t.topic }}</td>
              <td class="text-danger">{{ t.accuracy?.toFixed(1) }}%</td>
              <td>{{ t.attempts }}</td>
            </tr>
          </tbody>
        </table>

        <template v-if="report.weaknesses.frequent_errors?.length">
          <h3 class="subsection-title">高频错误模式</h3>
          <table class="report-table">
            <thead>
              <tr>
                <th>错误类型</th>
                <th>描述</th>
                <th>出现次数</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="e in report.weaknesses.frequent_errors"
                :key="e.description"
              >
                <td>
                  <span class="error-badge" :class="`error-${e.error_type}`">
                    {{ errorTypeText[e.error_type] || e.error_type }}
                  </span>
                </td>
                <td>{{ e.description }}</td>
                <td>{{ e.occurrence_count }}</td>
              </tr>
            </tbody>
          </table>
        </template>
      </div>

      <!-- 六、学习建议 -->
      <div v-if="report.recommendations?.length" class="report-section">
        <h2 class="section-title">六、个性化学习建议</h2>
        <div class="recommendations">
          <div
            v-for="(rec, i) in report.recommendations"
            :key="i"
            class="rec-item"
            :class="`priority-${rec.priority}`"
          >
            <div class="rec-icon">
              {{
                rec.priority === "high"
                  ? "🔴"
                  : rec.priority === "medium"
                    ? "🟡"
                    : "🟢"
              }}
            </div>
            <div class="rec-body">
              <div class="rec-title">
                <span class="rec-priority" :class="`priority-${rec.priority}`">
                  {{ priorityText[rec.priority] }}
                </span>
              </div>
              <div class="rec-content">{{ rec.content }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 报告页脚 -->
      <div class="report-footer">
        <p>
          本报告由计算思维课程助手系统自动生成 ·
          {{ formatDate(report.generated_at) }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { analyticsAPI } from "../../api/analytics";
import { useAuthStore } from "../../stores/user";
import { useAnalyticsStore } from "../../stores/analytics";

const authStore = useAuthStore();
const analyticsStore = useAnalyticsStore();

const report = ref(null);
const isLoading = ref(false);
const isDownloading = ref(false); // ⭐ 新增：下载状态
const error = ref("");
const selectedDays = ref(30);
const selectedUserId = ref(null);

const isTeacherOrAdmin = computed(() =>
  authStore.hasAnyRole(["teacher", "admin"]),
);
const students = computed(() => analyticsStore.students);

const scoreLabels = {
  time: "学习时长",
  activity: "活跃程度",
  code: "代码质量",
  knowledge: "学习广度",
};
const scoreMax = { time: 25, activity: 25, code: 30, knowledge: 20 };
const priorityText = { high: "重点关注", medium: "建议改进", low: "持续保持" };
const errorTypeText = {
  syntax: "语法错误",
  logic: "逻辑错误",
  concept: "概念错误",
};

onMounted(async () => {
  if (isTeacherOrAdmin.value) {
    await analyticsStore.loadStudents();
  } else {
    await loadReport();
  }
});

async function loadReport() {
  isLoading.value = true;
  error.value = "";
  report.value = null;
  try {
    const userId = isTeacherOrAdmin.value ? selectedUserId.value : null;
    const res = await analyticsAPI.getReport(selectedDays.value, userId);
    if (res.status === "success") {
      report.value = res.data;
    } else {
      error.value = res.message || "加载失败";
    }
  } catch (e) {
    error.value = e.message || "网络错误";
  } finally {
    isLoading.value = false;
  }
}

// ⭐ 核心：直接下载 PDF
async function downloadPDF() {
  isDownloading.value = true;
  try {
    const userId = isTeacherOrAdmin.value ? selectedUserId.value : null;
    await analyticsAPI.downloadReportPDF(selectedDays.value, userId);
  } catch (e) {
    alert("PDF 下载失败：" + (e.message || "未知错误"));
  } finally {
    isDownloading.value = false;
  }
}

function formatDate(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("zh-CN");
  } catch {
    return iso;
  }
}

function getMasteryClass(m) {
  if (!m) return "mastery-none";
  if (m >= 80) return "mastery-high";
  if (m >= 60) return "mastery-medium";
  return "mastery-low";
}

function getMasteryText(m) {
  if (!m) return "未学习";
  if (m >= 80) return "已掌握";
  if (m >= 60) return "基本掌握";
  return "需加强";
}
</script>

<style scoped>
.report-export {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
  overflow: hidden;
}

/* ===== 工具栏 ===== */
.export-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0;
  gap: 12px;
  flex-wrap: wrap;
}
.toolbar-left,
.toolbar-right {
  display: flex;
  gap: 10px;
  align-items: center;
}

.period-select,
.student-select {
  padding: 7px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 13px;
  outline: none;
  cursor: pointer;
}

.btn-refresh,
.btn-download,
.btn-generate,
.btn-retry {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}
.btn-refresh {
  background: #f0f4ff;
  color: #667eea;
  border: 1px solid #667eea;
}
.btn-refresh:hover:not(:disabled) {
  background: #667eea;
  color: white;
}

/* ⭐ 下载按钮 - 突出显示 */
.btn-download {
  background: linear-gradient(135deg, #e53e3e 0%, #c53030 100%);
  color: white;
  font-size: 14px;
  padding: 9px 20px;
}
.btn-download:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(229, 62, 62, 0.4);
}
.btn-download:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-generate {
  background: #667eea;
  color: white;
}
.btn-generate:hover {
  background: #5568d3;
}
.btn-retry {
  background: #f0f4ff;
  color: #667eea;
  border: 1px solid #667eea;
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed !important;
}

/* ===== 状态页 ===== */
.loading-state,
.error-state,
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
  text-align: center;
  gap: 12px;
}
.loading-state i,
.error-state i {
  font-size: 48px;
  color: #667eea;
}
.empty-icon {
  font-size: 64px;
  opacity: 0.5;
}
.empty-state h3 {
  margin: 0;
  font-size: 18px;
  color: #555;
}
.empty-state p {
  margin: 0;
  font-size: 14px;
}
.error-state i {
  color: #e53e3e;
}

/* ===== 报告容器 ===== */
.report-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.report-content::-webkit-scrollbar {
  width: 6px;
}
.report-content::-webkit-scrollbar-thumb {
  background: #cbd5e0;
  border-radius: 3px;
}

/* ===== 封面 ===== */
.report-cover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 16px;
  padding: 40px;
  text-align: center;
}
.cover-logo {
  font-size: 56px;
  margin-bottom: 12px;
}
.cover-title {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px 0;
}
.cover-subtitle {
  font-size: 14px;
  opacity: 0.85;
  margin: 0 0 16px 0;
}
.cover-meta {
  display: flex;
  gap: 24px;
  justify-content: center;
  flex-wrap: wrap;
  font-size: 13px;
  opacity: 0.9;
  margin-bottom: 20px;
}
.cover-score {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 20px 40px;
  display: inline-block;
}
.score-number {
  font-size: 56px;
  font-weight: 900;
  line-height: 1;
}
.score-grade {
  font-size: 28px;
  font-weight: 700;
}
.score-text {
  font-size: 14px;
  opacity: 0.9;
  margin-top: 4px;
}

/* ===== 章节 ===== */
.report-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}
.section-title {
  font-size: 18px;
  font-weight: 700;
  color: #667eea;
  margin: 0 0 16px 0;
  padding-bottom: 10px;
  border-bottom: 2px solid #e8ecff;
}
.subsection-title {
  font-size: 14px;
  font-weight: 600;
  color: #444;
  margin: 16px 0 8px 0;
}

/* ===== 概览网格 ===== */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.overview-card {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 16px;
  text-align: center;
  border: 1px solid #e8ecff;
}
.card-icon {
  font-size: 28px;
  margin-bottom: 8px;
}
.card-value {
  font-size: 28px;
  font-weight: 700;
  color: #667eea;
}
.card-label {
  font-size: 12px;
  color: #888;
  margin-top: 4px;
}

/* ===== 评分 ===== */
.score-breakdown {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.score-item {
  display: flex;
  align-items: center;
  gap: 12px;
}
.score-label {
  width: 80px;
  font-size: 13px;
  color: #555;
  flex-shrink: 0;
}
.score-bar-wrapper {
  flex: 1;
  height: 12px;
  background: #eee;
  border-radius: 6px;
  overflow: hidden;
}
.score-bar {
  height: 100%;
  border-radius: 6px;
  transition: width 0.3s;
}
.bar-time {
  background: linear-gradient(90deg, #667eea, #764ba2);
}
.bar-activity {
  background: linear-gradient(90deg, #56ccf2, #2f80ed);
}
.bar-code {
  background: linear-gradient(90deg, #6fcf97, #27ae60);
}
.bar-knowledge {
  background: linear-gradient(90deg, #f2994a, #f2c94c);
}
.score-val {
  width: 60px;
  font-size: 12px;
  color: #777;
  text-align: right;
  flex-shrink: 0;
}

/* ===== 表格 ===== */
.report-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.report-table th {
  background: #667eea;
  color: white;
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
}
.report-table td {
  padding: 9px 12px;
  border-bottom: 1px solid #f0f0f0;
  color: #444;
}
.report-table tr:last-child td {
  border-bottom: none;
}
.report-table tr:hover td {
  background: #f8f9ff;
}

/* 掌握度 */
.mastery-bar-wrapper {
  height: 8px;
  background: #eee;
  border-radius: 4px;
  overflow: hidden;
  width: 100px;
}
.mastery-bar {
  height: 100%;
  border-radius: 4px;
}
.mastery-high {
  background: #28a745;
}
.mastery-medium {
  background: #ffc107;
}
.mastery-low {
  background: #dc3545;
}
.mastery-none {
  background: #ddd;
}
.mastery-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}
.mastery-badge.mastery-high {
  background: #d4edda;
  color: #155724;
}
.mastery-badge.mastery-medium {
  background: #fff3cd;
  color: #856404;
}
.mastery-badge.mastery-low {
  background: #f8d7da;
  color: #721c24;
}
.mastery-badge.mastery-none {
  background: #f5f5f5;
  color: #888;
}

/* 错误徽章 */
.error-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
}
.error-syntax {
  background: #f8d7da;
  color: #721c24;
}
.error-logic {
  background: #fff3cd;
  color: #856404;
}
.error-concept {
  background: #cce5ff;
  color: #004085;
}

.text-danger {
  color: #dc3545;
  font-weight: 600;
}

/* 建议 */
.recommendations {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.rec-item {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px 16px;
  border-radius: 8px;
  border-left: 4px solid transparent;
}
.rec-item.priority-high {
  background: #fff5f5;
  border-left-color: #e53e3e;
}
.rec-item.priority-medium {
  background: #fffbf0;
  border-left-color: #ffc107;
}
.rec-item.priority-low {
  background: #f0fff4;
  border-left-color: #28a745;
}

.rec-icon {
  font-size: 18px;
  flex-shrink: 0;
  margin-top: 2px;
}
.rec-body {
  flex: 1;
}
.rec-title {
  margin-bottom: 4px;
}
.rec-content {
  font-size: 13px;
  color: #444;
  line-height: 1.6;
}
.rec-priority {
  display: inline-block;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}
.priority-high {
  background: #fed7d7;
  color: #c53030;
}
.priority-medium {
  background: #fef3c7;
  color: #92400e;
}
.priority-low {
  background: #c6f6d5;
  color: #276749;
}

/* 页脚 */
.report-footer {
  text-align: center;
  color: #aaa;
  font-size: 12px;
  padding: 16px 0;
}

/* 响应式 */
@media (max-width: 768px) {
  .overview-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
