<!-- filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\components\analytics\ActivityHeatmap.vue -->
<template>
  <div class="activity-heatmap">
    <div v-if="hasData" class="chart-area">
      <!-- 统计摘要 -->
      <div class="heatmap-summary">
        <div class="summary-item">
          <span class="summary-value">{{ stats.activeDays }}</span>
          <span class="summary-label">活跃天数</span>
        </div>
        <div class="summary-item">
          <span class="summary-value">{{ stats.maxStreak }}</span>
          <span class="summary-label">最长连续</span>
        </div>
        <div class="summary-item">
          <span class="summary-value">{{ stats.activeRate }}%</span>
          <span class="summary-label">活跃率</span>
        </div>
        <div class="summary-item">
          <span class="summary-value">{{ stats.busiestDay }}</span>
          <span class="summary-label">最活跃星期</span>
        </div>
      </div>

      <!-- 热力图容器 -->
      <div class="heatmap-grid">
        <!-- 星期标签 -->
        <div class="weekday-labels">
          <div class="weekday-label">一</div>
          <div class="weekday-label">二</div>
          <div class="weekday-label">三</div>
          <div class="weekday-label">四</div>
          <div class="weekday-label">五</div>
          <div class="weekday-label">六</div>
          <div class="weekday-label">日</div>
        </div>

        <!-- 日历网格 -->
        <div class="calendar-grid">
          <div
            v-for="(cell, index) in calendarCells"
            :key="index"
            :class="['day-cell', cell.levelClass]"
            :title="cell.tooltip"
          >
            <span v-if="cell.showDate" class="cell-date">{{ cell.day }}</span>
          </div>
        </div>

        <!-- 图例 -->
        <div class="heatmap-legend">
          <span class="legend-label">少</span>
          <div class="legend-cell level-0"></div>
          <div class="legend-cell level-1"></div>
          <div class="legend-cell level-2"></div>
          <div class="legend-cell level-3"></div>
          <div class="legend-cell level-4"></div>
          <span class="legend-label">多</span>
        </div>
      </div>
    </div>

    <!-- 无数据 -->
    <div v-else class="empty-state">
      <div class="empty-icon">📅</div>
      <h3>暂无活跃记录</h3>
      <p>开始学习后将显示活跃热力图</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
    // 期望格式: [{ date: '2026-02-01', count: 5, duration: 1.2 }, ...]
  },
  days: {
    type: Number,
    default: 30,
  },
});

const hasData = computed(() => {
  return props.data && props.data.length > 0;
});

// 建立日期->数据的映射
const dateMap = computed(() => {
  const map = {};
  (props.data || []).forEach((item) => {
    if (item.date) {
      map[item.date] = {
        count: item.total_count || item.count || 0,
        duration: item.duration || 0,
      };
    }
  });
  return map;
});

// 最大活跃度（用于计算颜色级别）
const maxCount = computed(() => {
  const counts = Object.values(dateMap.value).map((v) => v.count);
  return Math.max(...counts, 1);
});

// 生成日历格子
const calendarCells = computed(() => {
  const cells = [];
  const today = new Date();
  const startDate = new Date(today);
  startDate.setDate(startDate.getDate() - props.days + 1);

  // 补齐起始日到周一
  const startDay = startDate.getDay(); // 0=周日
  const offset = startDay === 0 ? 6 : startDay - 1; // 周一=0的偏移量
  const paddingStart = new Date(startDate);
  paddingStart.setDate(paddingStart.getDate() - offset);

  // 从 paddingStart 一直到 today
  const current = new Date(paddingStart);
  while (current <= today) {
    const dateStr = current.toISOString().split("T")[0];
    const data = dateMap.value[dateStr];
    const count = data ? data.count : 0;
    const duration = data ? data.duration : 0;
    const isInRange = current >= startDate;

    const level = isInRange ? getLevel(count) : -1;

    cells.push({
      date: dateStr,
      day: current.getDate(),
      count,
      duration,
      isInRange,
      levelClass: isInRange ? `level-${level}` : "out-of-range",
      showDate: current.getDate() === 1 || cells.length === 0,
      tooltip: isInRange
        ? `${dateStr}\n活动: ${count} 次\n时长: ${duration.toFixed(1)} 小时`
        : "",
    });

    current.setDate(current.getDate() + 1);
  }

  return cells;
});

function getLevel(count) {
  if (count === 0) return 0;
  const ratio = count / maxCount.value;
  if (ratio <= 0.25) return 1;
  if (ratio <= 0.5) return 2;
  if (ratio <= 0.75) return 3;
  return 4;
}

// 统计数据
const stats = computed(() => {
  const dates = Object.keys(dateMap.value);
  const activeDays = dates.filter((d) => dateMap.value[d].count > 0).length;

  // 最长连续天数
  let maxStreak = 0;
  let currentStreak = 0;
  const today = new Date();
  for (let i = 0; i < props.days; i++) {
    const d = new Date(today);
    d.setDate(d.getDate() - (props.days - 1 - i));
    const dateStr = d.toISOString().split("T")[0];
    if (dateMap.value[dateStr] && dateMap.value[dateStr].count > 0) {
      currentStreak++;
      maxStreak = Math.max(maxStreak, currentStreak);
    } else {
      currentStreak = 0;
    }
  }

  // 活跃率
  const activeRate =
    props.days > 0 ? Math.round((activeDays / props.days) * 100) : 0;

  // 最活跃的星期几
  const weekdayCounts = [0, 0, 0, 0, 0, 0, 0]; // 周一到周日
  Object.keys(dateMap.value).forEach((dateStr) => {
    const d = new Date(dateStr);
    const day = d.getDay(); // 0=周日
    const idx = day === 0 ? 6 : day - 1; // 转为 0=周一
    weekdayCounts[idx] += dateMap.value[dateStr].count;
  });
  const weekdays = ["一", "二", "三", "四", "五", "六", "日"];
  const busiestIdx = weekdayCounts.indexOf(Math.max(...weekdayCounts));
  const busiestDay = weekdays[busiestIdx] || "-";

  return { activeDays, maxStreak, activeRate, busiestDay };
});
</script>

<style scoped>
.activity-heatmap {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chart-area {
  flex: 1;
}

.heatmap-summary {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 18px;
  background: #f5f7fa;
  border-radius: 8px;
  min-width: 80px;
}

.summary-value {
  font-size: 22px;
  font-weight: bold;
  color: #667eea;
}

.summary-label {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.heatmap-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.weekday-labels {
  display: flex;
  gap: 0;
  margin-left: 0;
}

.weekday-label {
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: #999;
  margin-right: 3px;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 18px);
  grid-auto-rows: 18px;
  gap: 3px;
}

.day-cell {
  width: 18px;
  height: 18px;
  border-radius: 3px;
  cursor: default;
  position: relative;
}

.day-cell.out-of-range {
  background: transparent;
}

.day-cell.level-0 {
  background: #ebedf0;
}
.day-cell.level-1 {
  background: #c6dbef;
}
.day-cell.level-2 {
  background: #84b1e0;
}
.day-cell.level-3 {
  background: #4a89d0;
}
.day-cell.level-4 {
  background: #2154a8;
}

.day-cell:hover {
  outline: 2px solid #333;
  outline-offset: -1px;
}

.cell-date {
  display: none;
}

.heatmap-legend {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 12px;
}

.legend-label {
  font-size: 11px;
  color: #999;
}

.legend-cell {
  width: 14px;
  height: 14px;
  border-radius: 2px;
}

.legend-cell.level-0 {
  background: #ebedf0;
}
.legend-cell.level-1 {
  background: #c6dbef;
}
.legend-cell.level-2 {
  background: #84b1e0;
}
.legend-cell.level-3 {
  background: #4a89d0;
}
.legend-cell.level-4 {
  background: #2154a8;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  color: #666;
}
</style>
