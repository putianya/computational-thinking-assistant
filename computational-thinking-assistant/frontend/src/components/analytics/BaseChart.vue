<!-- filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\components\analytics\BaseChart.vue -->
<template>
  <div ref="chartRef" class="base-chart" :style="{ height: height }"></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from "vue";
import * as echarts from "echarts";

const props = defineProps({
  option: {
    type: Object,
    required: true,
  },
  height: {
    type: String,
    default: "400px",
  },
});

const chartRef = ref(null);
let chartInstance = null;

onMounted(() => {
  initChart();
  window.addEventListener("resize", handleResize);
});

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  if (chartInstance) {
    chartInstance.dispose();
    chartInstance = null;
  }
});

watch(
  () => props.option,
  (newOption) => {
    if (chartInstance && newOption) {
      chartInstance.setOption(newOption, true);
    }
  },
  { deep: true },
);

function initChart() {
  if (!chartRef.value) return;
  chartInstance = echarts.init(chartRef.value);
  if (props.option) {
    chartInstance.setOption(props.option);
  }
}

function handleResize() {
  if (chartInstance) {
    chartInstance.resize();
  }
}

defineExpose({ chartInstance, handleResize });
</script>

<style scoped>
.base-chart {
  width: 100%;
  min-height: 300px;
}
</style>
