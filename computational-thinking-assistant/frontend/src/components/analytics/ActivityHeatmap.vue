<!-- filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\components\analytics\ActivityHeatmap.vue -->
<template>
  <div class="activity-calendar">
    <!-- 空状态 -->
    <div v-if="!hasStudent" class="empty-state">
      <div class="empty-icon">👈</div>
      <p>请先选择一名学生</p>
    </div>

    <template v-else>
      <!-- 汇总栏 -->
      <div class="summary-bar">
        <div class="summary-item">
          <span class="summary-value">{{ activeDays }}</span>
          <span class="summary-label">活跃天数</span>
        </div>
        <div class="summary-item">
          <span class="summary-value">{{ maxCount }}</span>
          <span class="summary-label">最高单日</span>
        </div>
        <div class="summary-item">
          <span class="summary-value">{{ totalCount }}</span>
          <span class="summary-label">累计活动</span>
        </div>
      </div>

      <!-- 月份翻页 -->
      <div class="calendar-nav">
        <button class="nav-btn" @click="prevMonth" :disabled="!canGoPrev">
          ‹
        </button>
        <span class="nav-title">{{ viewYear }} 年 {{ viewMonth + 1 }} 月</span>
        <button class="nav-btn" @click="nextMonth" :disabled="!canGoNext">
          ›
        </button>
      </div>

      <!-- 日历主体 -->
      <div class="calendar-grid">
        <!-- 星期头 -->
        <div class="week-header" v-for="w in weekDays" :key="w">{{ w }}</div>

        <!-- 空白占位（月份第一天前） -->
        <div
          v-for="n in firstDayOffset"
          :key="'empty-' + n"
          class="day-cell empty"
        ></div>

        <!-- 日期格子 -->
        <div
          v-for="day in daysInMonth"
          :key="day.date"
          class="day-cell"
          :class="[
            getLevel(day.count),
            { today: day.isToday, 'out-of-range': day.outOfRange },
          ]"
          :title="
            day.outOfRange ? day.label : `${day.label}：${day.count} 次活动`
          "
        >
          <span class="day-num">{{ day.dayNum }}</span>
          <span v-if="day.count > 0 && !day.outOfRange" class="day-count">{{
            day.count
          }}</span>
        </div>
      </div>

      <!-- 图例 -->
      <div class="legend">
        <span class="legend-label">少</span>
        <div class="legend-cell level-0"></div>
        <div class="legend-cell level-1"></div>
        <div class="legend-cell level-2"></div>
        <div class="legend-cell level-3"></div>
        <div class="legend-cell level-4"></div>
        <span class="legend-label">多</span>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

const props = defineProps({
  data: { type: Array, default: () => [] },
  days: { type: Number, default: 30 },
  hasStudent: { type: Boolean, default: false },
});

const weekDays = ["日", "一", "二", "三", "四", "五", "六"];

// 当前浏览的年月（默认当月）
const today = new Date();
const viewYear = ref(today.getFullYear());
const viewMonth = ref(today.getMonth()); // 0-based

// 数据映射 date -> count
const dataMap = computed(() => {
  const map = {};
  (props.data || []).forEach((item) => {
    map[item.date] = item.count || 0;
  });
  return map;
});

// 整个数据范围（最早日期 ~ 今天）
const rangeStart = computed(() => {
  const d = new Date(today);
  d.setDate(today.getDate() - props.days + 1);
  d.setHours(0, 0, 0, 0);
  return d;
});

// 当月第一天是星期几（0=周日）
const firstDayOffset = computed(() => {
  return new Date(viewYear.value, viewMonth.value, 1).getDay();
});

// 当月天数
const totalDays = computed(() => {
  return new Date(viewYear.value, viewMonth.value + 1, 0).getDate();
});

// 生成当月所有日期格子
const daysInMonth = computed(() => {
  const result = [];
  for (let d = 1; d <= totalDays.value; d++) {
    const date = new Date(viewYear.value, viewMonth.value, d);
    const dateStr = date.toISOString().slice(0, 10);
    const isToday =
      date.getFullYear() === today.getFullYear() &&
      date.getMonth() === today.getMonth() &&
      date.getDate() === today.getDate();
    // 超出数据范围（未来或太久前）
    const outOfRange = date > today || date < rangeStart.value;

    result.push({
      dayNum: d,
      date: dateStr,
      label: `${viewYear.value}-${String(viewMonth.value + 1).padStart(2, "0")}-${String(d).padStart(2, "0")}`,
      count: outOfRange ? 0 : dataMap.value[dateStr] || 0,
      isToday,
      outOfRange,
    });
  }
  return result;
});

// 汇总（跨所有数据，不限当月）
const allCells = computed(() => {
  const result = [];
  const d = new Date(rangeStart.value);
  while (d <= today) {
    const dateStr = d.toISOString().slice(0, 10);
    result.push({ count: dataMap.value[dateStr] || 0 });
    d.setDate(d.getDate() + 1);
  }
  return result;
});

const activeDays = computed(
  () => allCells.value.filter((c) => c.count > 0).length,
);
const maxCount = computed(() =>
  Math.max(...allCells.value.map((c) => c.count), 0),
);
const totalCount = computed(() =>
  allCells.value.reduce((s, c) => s + c.count, 0),
);

// 翻月限制
const minMonth = computed(() => {
  const d = new Date(rangeStart.value);
  return { year: d.getFullYear(), month: d.getMonth() };
});
const canGoPrev = computed(
  () =>
    viewYear.value > minMonth.value.year ||
    (viewYear.value === minMonth.value.year &&
      viewMonth.value > minMonth.value.month),
);
const canGoNext = computed(
  () =>
    viewYear.value < today.getFullYear() ||
    (viewYear.value === today.getFullYear() &&
      viewMonth.value < today.getMonth()),
);

function prevMonth() {
  if (!canGoPrev.value) return;
  if (viewMonth.value === 0) {
    viewMonth.value = 11;
    viewYear.value--;
  } else viewMonth.value--;
}
function nextMonth() {
  if (!canGoNext.value) return;
  if (viewMonth.value === 11) {
    viewMonth.value = 0;
    viewYear.value++;
  } else viewMonth.value++;
}

function getLevel(count) {
  if (count === 0) return "level-0";
  if (maxCount.value === 0) return "level-0";
  const r = count / maxCount.value;
  if (r <= 0.25) return "level-1";
  if (r <= 0.5) return "level-2";
  if (r <= 0.75) return "level-3";
  return "level-4";
}
</script>

<style scoped>
.activity-calendar {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: #999;
  text-align: center;
  background: #fafafa;
  border-radius: 10px;
  border: 1px dashed #ddd;
}
.empty-icon {
  font-size: 36px;
  margin-bottom: 8px;
  opacity: 0.5;
}

/* 汇总栏 */
.summary-bar {
  display: flex;
  gap: 16px;
}
.summary-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  min-width: 72px;
}
.summary-value {
  font-size: 18px;
  font-weight: bold;
  color: #667eea;
}
.summary-label {
  font-size: 11px;
  color: #999;
  margin-top: 2px;
}

/* 翻月导航 */
.calendar-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}
.nav-btn {
  background: none;
  border: 1px solid #ddd;
  border-radius: 6px;
  width: 28px;
  height: 28px;
  cursor: pointer;
  font-size: 16px;
  color: #555;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}
.nav-btn:hover:not(:disabled) {
  background: #f0f0f0;
}
.nav-btn:disabled {
  color: #ccc;
  cursor: not-allowed;
}
.nav-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  min-width: 110px;
  text-align: center;
}

/* 日历网格 */
.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

/* 星期头 */
.week-header {
  text-align: center;
  font-size: 12px;
  color: #999;
  font-weight: 600;
  padding: 4px 0;
}

/* 日期格子 */
.day-cell {
  position: relative;
  aspect-ratio: 1;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: default;
  transition: transform 0.1s;
  border: 1px solid transparent;
}
.day-cell:not(.empty):hover {
  transform: scale(1.12);
  z-index: 1;
}
.day-cell.empty {
  background: transparent;
  border: none;
}

.day-num {
  font-size: 13px;
  font-weight: 500;
  line-height: 1;
}
.day-count {
  font-size: 9px;
  margin-top: 2px;
  opacity: 0.8;
  line-height: 1;
}

/* 今天高亮 */
.day-cell.today {
  border-color: #667eea !important;
  box-shadow: 0 0 0 1.5px #667eea44;
}
.day-cell.today .day-num {
  color: #667eea;
  font-weight: 700;
}

/* 超出范围（未来/太久前） */
.day-cell.out-of-range {
  background: #f8f8f8 !important;
  opacity: 0.4;
}

/* 颜色等级 */
.level-0 {
  background: #ebedf0;
  color: #aaa;
}
.level-1 {
  background: #c6e48b;
  color: #555;
}
.level-2 {
  background: #7bc96f;
  color: #fff;
}
.level-3 {
  background: #239a3b;
  color: #fff;
}
.level-4 {
  background: #196127;
  color: #fff;
}

/* 图例 */
.legend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #999;
}
.legend-label {
  font-size: 11px;
}
.legend-cell {
  width: 14px;
  height: 14px;
  border-radius: 3px;
}
</style>
