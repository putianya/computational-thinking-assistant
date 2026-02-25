import { defineStore } from "pinia";
import { ref, watch } from "vue";
import { analyticsAPI } from "../api/analytics";

// ⭐ localStorage 键名
const STORAGE_KEYS = {
  SELECTED_STUDENT: "analytics_selected_student",
  SELECTED_PERIOD: "analytics_selected_period",
  SELECTED_CARD: "analytics_selected_card",
};

export const useAnalyticsStore = defineStore("analytics", () => {
  // ========== 状态 ==========
  const overview = ref(null);
  const learningTrend = ref([]);
  const knowledgeMastery = ref([]);
  const weaknessAnalysis = ref(null);
  const errorDistribution = ref(null);
  const codeQualityTrend = ref([]);
  const activityHeatmap = ref(null);
  const knowledgeChunkStats = ref(null);

  const isLoading = ref(false);

  // ⭐⭐⭐ 修改：从 localStorage 恢复状态 ⭐⭐⭐
  const currentPeriod = ref(
    parseInt(localStorage.getItem(STORAGE_KEYS.SELECTED_PERIOD)) || 30,
  );

  const students = ref([]);
  const selectedStudentId = ref(
    (() => {
      const saved = localStorage.getItem(STORAGE_KEYS.SELECTED_STUDENT);
      if (saved === "null" || saved === null) return null;
      const parsed = parseInt(saved);
      return isNaN(parsed) ? null : parsed;
    })(),
  );

  // ⭐⭐⭐ 新增：选中的卡片类型 ⭐⭐⭐
  const selectedCard = ref(
    localStorage.getItem(STORAGE_KEYS.SELECTED_CARD) || null,
  );

  // ⭐⭐⭐ 监听状态变化，自动保存到 localStorage ⭐⭐⭐
  watch(selectedStudentId, (val) => {
    if (val === null) {
      localStorage.removeItem(STORAGE_KEYS.SELECTED_STUDENT);
    } else {
      localStorage.setItem(STORAGE_KEYS.SELECTED_STUDENT, String(val));
    }
  });

  watch(currentPeriod, (val) => {
    localStorage.setItem(STORAGE_KEYS.SELECTED_PERIOD, String(val));
  });

  watch(selectedCard, (val) => {
    if (val === null) {
      localStorage.removeItem(STORAGE_KEYS.SELECTED_CARD);
    } else {
      localStorage.setItem(STORAGE_KEYS.SELECTED_CARD, val);
    }
  });

  // ========== 加载学生列表 ==========
  async function loadStudents() {
    try {
      const response = await analyticsAPI.getStudents();
      if (response.status === "success") {
        students.value = response.data;
        console.log(`✅ 加载了 ${students.value.length} 个学生`);

        // ⭐ 验证缓存的学生ID是否仍然有效
        if (
          selectedStudentId.value &&
          !students.value.find((s) => s.id === selectedStudentId.value)
        ) {
          console.log("⚠️ 缓存的学生ID已失效，重置");
          selectedStudentId.value = null;
          selectedCard.value = null;
        }
      }
    } catch (error) {
      console.error("❌ 加载学生列表失败:", error);
    }
  }

  // ========== 选择学生 ==========
  async function selectStudent(studentId) {
    selectedStudentId.value = studentId;
    // ⭐ 切换学生时清除选中的卡片
    selectedCard.value = null;
    console.log("👤 选择学生:", studentId);
    await loadAllData(currentPeriod.value);
  }

  // ⭐⭐⭐ 新增：设置选中的卡片 ⭐⭐⭐
  function setSelectedCard(cardType) {
    selectedCard.value = cardType;
  }

  // ========== 加载数据方法 ==========

  /**
   * 加载概览数据
   */
  async function loadOverview(days = 30) {
    try {
      const response = await analyticsAPI.getOverview(
        days,
        selectedStudentId.value,
      );
      if (response.status === "success") {
        overview.value = response.data;
      }
    } catch (error) {
      console.error("❌ 加载概览数据失败:", error);
    }
  }

  /**
   * 加载学习趋势
   */
  async function loadLearningTrend(days = 30) {
    try {
      if (!selectedStudentId.value) {
        learningTrend.value = [];
        return;
      }
      const response = await analyticsAPI.getLearningTrend(
        days,
        selectedStudentId.value,
      );
      if (response.status === "success") {
        learningTrend.value = response.data;
      }
    } catch (error) {
      console.error("❌ 加载趋势数据失败:", error);
    }
  }

  /**
   * 加载知识点掌握度
   */
  async function loadKnowledgeMastery(days = 30) {
    try {
      if (!selectedStudentId.value) {
        knowledgeMastery.value = [];
        return;
      }
      const response = await analyticsAPI.getKnowledgeMastery(
        days,
        selectedStudentId.value,
      );
      if (response.status === "success") {
        knowledgeMastery.value = response.data;
      }
    } catch (error) {
      console.error("❌ 加载知识点数据失败:", error);
    }
  }

  /**
   * 加载活跃热力图
   */
  async function loadActivityHeatmap(days = 30) {
    try {
      if (!selectedStudentId.value) {
        activityHeatmap.value = [];
        return;
      }
      // 热力图使用更长的天数范围（默认用 days，最少30天）
      const heatmapDays = Math.max(days, 30);
      const response = await analyticsAPI.getActivityHeatmap(
        heatmapDays,
        selectedStudentId.value,
      );
      if (response.status === "success") {
        activityHeatmap.value = response.data;
      }
    } catch (error) {
      console.error("❌ 加载热力图数据失败:", error);
    }
  }

  /**
   * 加载薄弱环节分析
   */
  async function loadWeaknessAnalysis(days = 30) {
    try {
      if (!selectedStudentId.value) {
        weaknessAnalysis.value = null;
        return;
      }
      const response = await analyticsAPI.getWeaknessAnalysis(
        days,
        selectedStudentId.value,
      );
      if (response.status === "success") {
        weaknessAnalysis.value = response.data;
      }
    } catch (error) {
      console.error("❌ 加载薄弱环节数据失败:", error);
    }
  }

  /**
   * 加载知识块引用热度
   */
  async function loadKnowledgeChunkStats(limit = 20) {
    try {
      const response = await analyticsAPI.getKnowledgeChunkStats(limit);
      if (response.status === "success") {
        knowledgeChunkStats.value = response.data;
      }
    } catch (error) {
      console.error("❌ 加载知识块热度数据失败:", error);
    }
  }

  /**
   * 加载所有数据
   */
  async function loadAllData(days = 30) {
    try {
      isLoading.value = true;
      currentPeriod.value = days;

      await Promise.all([
        loadOverview(days),
        loadLearningTrend(days),
        loadKnowledgeMastery(days),
        loadWeaknessAnalysis(days),
        loadKnowledgeChunkStats(),
        loadActivityHeatmap(days),
      ]);

      console.log("✅ 所有分析数据加载完成");
    } catch (error) {
      console.error("❌ 加载分析数据失败:", error);
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
<<<<<<<<< Temporary merge branch 1
    activityHeatmap.value = [];
=========
    activityHeatmap.value = null;
    knowledgeChunkStats.value = null;
>>>>>>>>> Temporary merge branch 2
    isLoading.value = false;
    currentPeriod.value = 30;
    students.value = [];
    selectedStudentId.value = null;
    selectedCard.value = null;

    // ⭐ 清除 localStorage
    Object.values(STORAGE_KEYS).forEach((key) => localStorage.removeItem(key));
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
    knowledgeChunkStats,
    isLoading,
    currentPeriod,
    students,
    selectedStudentId,
    selectedCard, // ⭐ 新增

    // 方法
    loadStudents,
    selectStudent,
    setSelectedCard, // ⭐ 新增
    loadOverview,
    loadLearningTrend,
    loadKnowledgeMastery,
    loadWeaknessAnalysis,
<<<<<<<<< Temporary merge branch 1
    loadActivityHeatmap,
=========
    loadKnowledgeChunkStats,
>>>>>>>>> Temporary merge branch 2
    loadAllData,
    refreshData,
    changePeriod,
    resetStore,
  };
});
