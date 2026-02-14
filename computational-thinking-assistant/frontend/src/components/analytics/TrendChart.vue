<!-- filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\components\analytics\TrendChart.vue -->
<template>
  <div class="trend-chart">
    <!-- 有数据时显示图表 -->
    <div v-if="hasData" class="chart-area">
      <!-- 顶部统计摘要 -->
      <div class="chart-summary">
        <div
          class="summary-item"
          v-for="item in summaryItems"
          :key="item.label"
        >
          <span class="summary-value">{{ item.value }}</span>
          <span class="summary-label">{{ item.label }}</span>
        </div>
      </div>

      <BaseChart :option="chartOption" height="360px" />
    </div>

    <!-- 无数据时显示空状态 -->
    <div v-else class="empty-state">
      <div class="empty-icon">📉</div>
      <h3>暂无数据</h3>
      <p>当前时间范围内没有记录</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import BaseChart from "./BaseChart.vue";

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
  type: {
    type: String,
    required: true, // 'duration', 'questions', 'code', 'accuracy'
  },
});

const hasData = computed(() => {
  return props.data && props.data.length > 0;
});

// ========== 统计摘要 ==========
const summaryItems = computed(() => {
  if (!hasData.value) return [];

  switch (props.type) {
    case "duration":
      return getDurationSummary();
    case "questions":
      return getQuestionsSummary();
    case "code":
      return getCodeSummary();
    case "accuracy":
      return getAccuracySummary();
    default:
      return [];
  }
});

function getDurationSummary() {
  const durations = props.data.map((d) => d.duration || 0);
  const total = durations.reduce((a, b) => a + b, 0);
  const avg = durations.length > 0 ? total / durations.length : 0;
  const max = Math.max(...durations, 0);
  const activeDays = durations.filter((d) => d > 0).length;
  return [
    { label: "总时长(h)", value: total.toFixed(1) },
    { label: "日均(h)", value: avg.toFixed(1) },
    { label: "最长单日(h)", value: max.toFixed(1) },
    { label: "活跃天数", value: activeDays },
  ];
}

function getQuestionsSummary() {
  const counts = props.data.map((d) => d.total_count || d.question_count || 0);
  const total = counts.reduce((a, b) => a + b, 0);
  const avg = counts.length > 0 ? total / counts.length : 0;
  const max = Math.max(...counts, 0);
  return [
    { label: "总提问", value: total },
    { label: "日均", value: avg.toFixed(1) },
    { label: "单日最多", value: max },
  ];
}

function getCodeSummary() {
  const counts = props.data.map((d) => d.code_count || 0);
  const scores = props.data
    .filter((d) => d.avg_score !== undefined && d.avg_score !== null)
    .map((d) => d.avg_score);
  const totalSubmit = counts.reduce((a, b) => a + b, 0);
  const avgScore =
    scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
  return [
    { label: "总提交", value: totalSubmit },
    { label: "平均分", value: avgScore.toFixed(1) },
  ];
}

function getAccuracySummary() {
  const accuracies = props.data
    .filter((d) => d.accuracy !== undefined && d.accuracy !== null)
    .map((d) => d.accuracy);
  const avg =
    accuracies.length > 0
      ? accuracies.reduce((a, b) => a + b, 0) / accuracies.length
      : 0;
  const latest = accuracies.length > 0 ? accuracies[accuracies.length - 1] : 0;
  // 前半段 vs 后半段
  const mid = Math.floor(accuracies.length / 2);
  const firstHalf = accuracies.slice(0, mid);
  const secondHalf = accuracies.slice(mid);
  const firstAvg =
    firstHalf.length > 0
      ? firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length
      : 0;
  const secondAvg =
    secondHalf.length > 0
      ? secondHalf.reduce((a, b) => a + b, 0) / secondHalf.length
      : 0;
  const trend = secondAvg - firstAvg;
  return [
    { label: "平均正确率", value: avg.toFixed(1) + "%" },
    { label: "最近", value: latest.toFixed(1) + "%" },
    {
      label: "趋势",
      value:
        trend >= 0
          ? "↑" + trend.toFixed(1) + "%"
          : "↓" + Math.abs(trend).toFixed(1) + "%",
    },
  ];
}

// ========== ECharts 配置 ==========
const chartOption = computed(() => {
  if (!hasData.value) return {};

  switch (props.type) {
    case "duration":
      return buildDurationOption();
    case "questions":
      return buildQuestionsOption();
    case "code":
      return buildCodeOption();
    case "accuracy":
      return buildAccuracyOption();
    default:
      return {};
  }
});

function formatDates() {
  return props.data.map((d) => {
    if (!d.date) return "";
    // 只显示月-日
    const parts = d.date.split("-");
    return parts.length >= 3 ? `${parts[1]}-${parts[2]}` : d.date;
  });
}

// 📚 学习时长 - 折线图
function buildDurationOption() {
  const dates = formatDates();
  const durations = props.data.map((d) => d.duration || 0);

  return {
    tooltip: {
      trigger: "axis",
      formatter: (params) => {
        const p = params[0];
        return `${props.data[p.dataIndex]?.date || ""}<br/>学习时长: <b>${p.value}</b> 小时`;
      },
    },
    grid: { left: 50, right: 20, top: 30, bottom: 40 },
    xAxis: {
      type: "category",
      data: dates,
      axisLabel: {
        rotate: dates.length > 15 ? 45 : 0,
        fontSize: 11,
      },
    },
    yAxis: {
      type: "value",
      name: "小时",
      nameTextStyle: { fontSize: 12 },
      splitLine: { lineStyle: { type: "dashed" } },
    },
    series: [
      {
        name: "学习时长",
        type: "line",
        data: durations,
        smooth: true,
        symbol: "circle",
        symbolSize: 6,
        lineStyle: { width: 3, color: "#667eea" },
        itemStyle: { color: "#667eea" },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(102,126,234,0.3)" },
              { offset: 1, color: "rgba(102,126,234,0.02)" },
            ],
          },
        },
      },
    ],
  };
}

// 💬 提问次数 - 柱状图
function buildQuestionsOption() {
  const dates = formatDates();
  const counts = props.data.map((d) => d.total_count || d.question_count || 0);

  return {
    tooltip: {
      trigger: "axis",
      formatter: (params) => {
        const p = params[0];
        return `${props.data[p.dataIndex]?.date || ""}<br/>提问次数: <b>${p.value}</b> 次`;
      },
    },
    grid: { left: 50, right: 20, top: 30, bottom: 40 },
    xAxis: {
      type: "category",
      data: dates,
      axisLabel: {
        rotate: dates.length > 15 ? 45 : 0,
        fontSize: 11,
      },
    },
    yAxis: {
      type: "value",
      name: "次数",
      minInterval: 1,
      splitLine: { lineStyle: { type: "dashed" } },
    },
    series: [
      {
        name: "提问次数",
        type: "bar",
        data: counts,
        barMaxWidth: 30,
        itemStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "#667eea" },
              { offset: 1, color: "#764ba2" },
            ],
          },
          borderRadius: [4, 4, 0, 0],
        },
      },
    ],
  };
}

// 💻 代码提交 - 双轴折线图（提交次数 + 平均分）
function buildCodeOption() {
  const dates = formatDates();
  const counts = props.data.map((d) => d.code_count || 0);
  const scores = props.data.map((d) => d.avg_score ?? null);

  return {
    tooltip: {
      trigger: "axis",
      formatter: (params) => {
        let result = `${props.data[params[0]?.dataIndex]?.date || ""}<br/>`;
        params.forEach((p) => {
          if (p.value !== null && p.value !== undefined) {
            result += `${p.marker}${p.seriesName}: <b>${p.value}</b>${p.seriesName === "平均分" ? "分" : "次"}<br/>`;
          }
        });
        return result;
      },
    },
    legend: {
      data: ["提交次数", "平均分"],
      top: 0,
    },
    grid: { left: 50, right: 50, top: 40, bottom: 40 },
    xAxis: {
      type: "category",
      data: dates,
      axisLabel: {
        rotate: dates.length > 15 ? 45 : 0,
        fontSize: 11,
      },
    },
    yAxis: [
      {
        type: "value",
        name: "次数",
        position: "left",
        minInterval: 1,
        splitLine: { lineStyle: { type: "dashed" } },
      },
      {
        type: "value",
        name: "分数",
        position: "right",
        max: 100,
        min: 0,
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: "提交次数",
        type: "line",
        data: counts,
        smooth: true,
        symbol: "circle",
        symbolSize: 6,
        lineStyle: { width: 2, color: "#409EFF" },
        itemStyle: { color: "#409EFF" },
      },
      {
        name: "平均分",
        type: "line",
        yAxisIndex: 1,
        data: scores,
        smooth: true,
        symbol: "diamond",
        symbolSize: 6,
        lineStyle: { width: 2, color: "#67C23A" },
        itemStyle: { color: "#67C23A" },
        connectNulls: true,
      },
    ],
  };
}

// ✅ 代码正确率 - 仪表盘 + 趋势线
function buildAccuracyOption() {
  const dates = formatDates();
  const accuracies = props.data.map((d) => d.accuracy ?? 0);
  const avg =
    accuracies.length > 0
      ? accuracies.reduce((a, b) => a + b, 0) / accuracies.length
      : 0;

  // 颜色：绿>80, 黄60-80, 红<60
  const gaugeColor = avg >= 80 ? "#67C23A" : avg >= 60 ? "#E6A23C" : "#F56C6C";

  return {
    tooltip: {
      trigger: "axis",
      formatter: (params) => {
        // 过滤掉仪表盘的tooltip
        const lineParams = params.filter((p) => p.seriesType === "line");
        if (lineParams.length === 0) return "";
        const p = lineParams[0];
        return `${props.data[p.dataIndex]?.date || ""}<br/>正确率: <b>${p.value}%</b>`;
      },
    },
    grid: { left: 50, right: 20, top: 180, bottom: 40 },
    // 仪表盘
    series: [
      {
        name: "总正确率",
        type: "gauge",
        center: ["50%", "100px"],
        radius: "70px",
        startAngle: 200,
        endAngle: -20,
        min: 0,
        max: 100,
        progress: {
          show: true,
          width: 10,
          itemStyle: { color: gaugeColor },
        },
        pointer: { show: false },
        axisLine: {
          lineStyle: { width: 10, color: [[1, "#E0E0E0"]] },
        },
        axisTick: { show: false },
        splitLine: { show: false },
        axisLabel: { show: false },
        title: {
          offsetCenter: [0, "20%"],
          fontSize: 12,
          color: "#999",
        },
        detail: {
          offsetCenter: [0, "-10%"],
          fontSize: 28,
          fontWeight: "bold",
          color: gaugeColor,
          formatter: "{value}%",
        },
        data: [{ value: Math.round(avg * 10) / 10, name: "平均正确率" }],
      },
      // 趋势折线图
      {
        name: "正确率趋势",
        type: "line",
        data: accuracies,
        smooth: true,
        symbol: "circle",
        symbolSize: 6,
        lineStyle: { width: 2, color: gaugeColor },
        itemStyle: { color: gaugeColor },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: gaugeColor + "40" },
              { offset: 1, color: gaugeColor + "05" },
            ],
          },
        },
        xAxisIndex: 0,
        yAxisIndex: 0,
      },
    ],
    xAxis: {
      type: "category",
      data: dates,
      axisLabel: {
        rotate: dates.length > 15 ? 45 : 0,
        fontSize: 11,
      },
    },
    yAxis: {
      type: "value",
      name: "%",
      max: 100,
      min: 0,
      splitLine: { lineStyle: { type: "dashed" } },
    },
  };
}
</script>

<style scoped>
.trend-chart {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chart-area {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chart-summary {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
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
  font-size: 20px;
  font-weight: bold;
  color: #667eea;
}

.summary-label {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
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

.empty-state p {
  margin: 0;
  font-size: 14px;
}
</style>
