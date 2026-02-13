import { defineStore } from "pinia";
import { ref } from "vue";
import { analyticsAPI } from "../api/analytics";

export const useAnalyticsStore = defineStore("analytics", () => {
  // ========== 状态 ==========
  const overview = ref(null);
  const learningTrend = ref([]);
  const knowledgeMastery = ref([]);
  const weaknessAnalysis = ref(null);
  const errorDistribution = ref(null);
  const codeQualityTrend = ref([]);
  const activityHeatmap = ref(null);

  const isLoading = ref(false);
  const currentPeriod = ref(30); // 当前查看的时间范围（天）

  // ========== 加载数据方法 ==========

  /**
   * 加载概览数据
   */
  async function loadOverview(days = 30) {
    try {
      isLoading.value = true;
      console.log(`📊 加载学习概览（${days}天）...`);

      const response = await analyticsAPI.getOverview(days);

      if (response.status === "success") {
        overview.value = response.data;
        console.log("✅ 概览数据加载成功:", overview.value);
      }
    } catch (error) {
      console.error("❌ 加载概览数据失败:", error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * 加载学习趋势
   */
  async function loadLearningTrend(days = 30) {
    try {
      console.log(`📈 加载学习趋势（${days}天）...`);

      const response = await analyticsAPI.getLearningTrend(days);

      if (response.status === "success") {
        learningTrend.value = response.data;
        console.log("✅ 趋势数据加载成功");
      }
    } catch (error) {
      console.error("❌ 加载趋势数据失败:", error);
      throw error;
    }
  }

  /**
   * 加载知识点掌握度
   */
  async function loadKnowledgeMastery(days = 30) {
    try {
      console.log(`🎯 加载知识点掌握度（${days}天）...`);

      const response = await analyticsAPI.getKnowledgeMastery(days);

      if (response.status === "success") {
        knowledgeMastery.value = response.data;
        console.log("✅ 知识点数据加载成功");
      }
    } catch (error) {
      console.error("❌ 加载知识点数据失败:", error);
      throw error;
    }
  }

  /**
   * 加载薄弱环节分析
   */
  async function loadWeaknessAnalysis(days = 30) {
    try {
      console.log(`⚠️ 加载薄弱环节分析（${days}天）...`);

      const response = await analyticsAPI.getWeaknessAnalysis(days);

      if (response.status === "success") {
        weaknessAnalysis.value = response.data;
        console.log("✅ 薄弱环节数据加载成功");
      }
    } catch (error) {
      console.error("❌ 加载薄弱环节数据失败:", error);
      throw error;
    }
  }

  /**
   * 加载所有数据
   */
  async function loadAllData(days = 30) {
    try {
      isLoading.value = true;
      currentPeriod.value = days;

      console.log(`🔄 开始加载所有分析数据（${days}天）...`);

      // 并行加载所有数据
      await Promise.all([
        loadOverview(days),
        loadLearningTrend(days),
        loadKnowledgeMastery(days),
        loadWeaknessAnalysis(days),
      ]);

      console.log("✅ 所有分析数据加载完成");
    } catch (error) {
      console.error("❌ 加载分析数据失败:", error);
      throw error;
    } finally {
      isLoading.value = false;
    }
  }

  /**
   * 刷新数据
   */
  async function refreshData() {
    await loadAllData(currentPeriod.value);
  }

  /**
   * 切换时间范围
   */
  async function changePeriod(days) {
    if (days === currentPeriod.value) return;
    await loadAllData(days);
  }

  /**
   * 重置 Store
   */
  function resetStore() {
    overview.value = null;
    learningTrend.value = [];
    knowledgeMastery.value = [];
    weaknessAnalysis.value = null;
    errorDistribution.value = null;
    codeQualityTrend.value = [];
    activityHeatmap.value = null;
    isLoading.value = false;
    currentPeriod.value = 30;
  }

  // ========== 导出 ==========
  return {
    // 状态
    overview,
    learningTrend,
    knowledgeMastery,
    weaknessAnalysis,
    errorDistribution,
    codeQualityTrend,
    activityHeatmap,
    isLoading,
    currentPeriod,

    // 方法
    loadOverview,
    loadLearningTrend,
    loadKnowledgeMastery,
    loadWeaknessAnalysis,
    loadAllData,
    refreshData,
    changePeriod,
    resetStore,
  };
});
