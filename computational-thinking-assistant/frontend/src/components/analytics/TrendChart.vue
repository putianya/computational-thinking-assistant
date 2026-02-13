<!-- filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\components\analytics\TrendChart.vue -->
<template>
  <div class="trend-chart">
    <!-- 有数据时显示图表 -->
    <div v-if="chartData.length > 0" class="chart-area">
      <div class="chart-placeholder">
        <p>📊 图表渲染中...</p>
        <p class="hint">数据点: {{ chartData.length }}个</p>
        <div class="data-preview">
          <h4>数据预览：</h4>
          <ul>
            <li v-for="(item, index) in chartData.slice(0, 5)" :key="index">
              {{ item.date }}: {{ getValueForType(item) }}
            </li>
          </ul>
        </div>
      </div>
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

// 计算图表数据
const chartData = computed(() => {
  return props.data || [];
});

// 根据类型获取对应的值
function getValueForType(item) {
  switch (props.type) {
    case "duration":
      return `${item.duration || 0}小时`;
    case "questions":
      return `${item.total_count || 0}次`;
    case "code":
      return `${item.code_count || 0}次`;
    case "accuracy":
      return `${item.accuracy || 0}%`;
    default:
      return item.total_count || 0;
  }
}
</script>

<style scoped>
.trend-chart {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 400px;
}

.chart-area {
  flex: 1;
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 20px;
  background: #f9f9f9;
}

.chart-placeholder {
  text-align: center;
  color: #666;
}

.chart-placeholder p {
  font-size: 16px;
  margin: 10px 0;
}

.hint {
  font-size: 14px;
  color: #999;
}

.data-preview {
  margin-top: 20px;
  text-align: left;
  background: white;
  padding: 15px;
  border-radius: 8px;
  max-width: 400px;
  margin-left: auto;
  margin-right: auto;
}

.data-preview h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #333;
}

.data-preview ul {
  margin: 0;
  padding-left: 20px;
  font-size: 13px;
  color: #666;
}

.data-preview li {
  margin: 5px 0;
  font-family: monospace;
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
