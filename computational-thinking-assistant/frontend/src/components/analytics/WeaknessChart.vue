<!-- filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\components\analytics\WeaknessChart.vue -->
<template>
  <div class="weakness-chart">
    <!-- 有数据 -->
    <div v-if="chartData.length > 0" class="chart-area">
      <div class="list-view">
        <div
          v-for="(item, index) in chartData.slice(0, 10)"
          :key="index"
          class="topic-item"
        >
          <div class="topic-info">
            <span class="rank">{{ index + 1 }}</span>
            <span class="topic-name">{{ item.topic }}</span>
          </div>
          <div class="topic-stats">
            <span class="count">{{ item.total_count || 0 }}次</span>
            <span class="mastery" :style="getMasteryColor(item.mastery)">
              {{ item.mastery || 0 }}%
            </span>
          </div>
        </div>
      </div>
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
  return props.data || [];
});

// 根据掌握度设置颜色
function getMasteryColor(mastery) {
  if (mastery >= 80) return { color: "#67C23A" };
  if (mastery >= 60) return { color: "#E6A23C" };
  return { color: "#F56C6C" };
}
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

.list-view {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.topic-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.topic-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rank {
  width: 28px;
  height: 28px;
  background: #667eea;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
}

.topic-name {
  font-size: 15px;
  color: #333;
  font-weight: 500;
}

.topic-stats {
  display: flex;
  gap: 16px;
  align-items: center;
}

.count {
  font-size: 14px;
  color: #666;
}

.mastery {
  font-size: 16px;
  font-weight: bold;
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
