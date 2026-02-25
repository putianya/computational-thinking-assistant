<!-- filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\components\analytics\WeaknessChart.vue -->
<template>
  <div class="weakness-chart">
    <!-- 有数据 -->
    <div v-if="chartData.length > 0" class="chart-area">
      <BaseChart :option="chartOption" :height="chartHeight" />
    </div>

    <!-- 无数据 -->
    <div v-else class="empty-state">
      <div class="empty-icon">📊</div>
      <h3>暂无数据</h3>
      <p>开始学习后将显示知识点统计</p>
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
    default: "views",
  },
});

const chartData = computed(() => {
  return (props.data || []).slice(0, 15); // 最多显示15个
});

// 动态高度：每个知识点40px，最小300px
const chartHeight = computed(() => {
  const count = chartData.value.length;
  return Math.max(300, count * 45 + 80) + "px";
});

const chartOption = computed(() => {
  if (chartData.value.length === 0) return {};

  // 排序：按查看次数降序
  const sorted = [...chartData.value].sort(
    (a, b) => (b.total_count || 0) - (a.total_count || 0),
  );

  // ⭐ 不要在这里 reverse，保持原顺序
  const topics = sorted.map((d) => d.topic || "未知");
  const counts = sorted.map((d) => d.total_count || 0);

  return {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params) => {
        const idx = params[0]?.dataIndex;
        if (idx === undefined) return "";
        // ⭐ yAxis 是 reverse 后的，所以 dataIndex 对应 reversed 数组
        const item = sorted[sorted.length - 1 - idx]; // ⭐ 修正索引
        return `<b>${item.topic}</b><br/>查看次数: ${item.total_count || 0} 次<br/>掌握度: ${item.mastery || 0}%`;
      },
    },
    legend: {
      data: ["查看次数"],
      top: 0,
    },
    grid: {
      left: 120,
      right: 50,
      top: 35,
      bottom: 10,
      containLabel: false,
    },
    xAxis: [
      {
        type: "value",
        name: "次数",
        position: "top",
        splitLine: { lineStyle: { type: "dashed" } },
      },
    ],
    yAxis: {
      type: "category",
      data: [...topics].reverse(), // ⭐ 只在 yAxis 这里 reverse，让最高的排在最上面
      axisLabel: {
        fontSize: 13,
        width: 110,
        overflow: "truncate",
        ellipsis: "...",
      },
      inverse: false,
    },
    series: [
      {
        name: "查看次数",
        type: "bar",
        data: [...counts].reverse(), // ⭐ series 数据也同步 reverse
        barMaxWidth: 20,
        itemStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 1,
            y2: 0,
            colorStops: [
              { offset: 0, color: "#667eea" },
              { offset: 1, color: "#764ba2" },
            ],
          },
          borderRadius: [0, 4, 4, 0],
        },
        label: {
          show: true,
          position: "right",
          fontSize: 12,
          color: "#666",
          formatter: "{c}次",
        },
      },
    ],
  };
});
</script>

<style scoped>
.weakness-chart {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chart-area {
  flex: 1;
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
