<template>
  <div class="app-container">
    <!-- ⭐⭐⭐ 顶部标签栏 ⭐⭐⭐ -->
    <TabBar
      :tabs="availableTabs"
      :activeTab="currentTab"
      @switch="handleTabSwitch"
    />

    <!-- ⭐⭐⭐ 动态内容区域 ⭐⭐⭐ -->
    <div class="content-area">
      <component :is="currentComponent" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useAuthStore } from "../stores/user";
import TabBar from "./TabBar.vue";
import ChatView from "./ChatView.vue";
import KnowledgeBase from "./KnowledgeBase.vue";
import CodeAnalyzer from "./CodeAnalyzer.vue";
import UserManagement from "./UserManagement.vue";
import LearningAnalytics from "./analytics/LearningAnalytics.vue";

const authStore = useAuthStore();
const currentTab = ref("chat");

// ⭐⭐⭐ 修复：根据用户角色动态显示标签 ⭐⭐⭐
const availableTabs = computed(() => {
  const tabs = [
    {
      id: "chat",
      label: "对话",
      icon: "fas fa-comments",
      component: ChatView,
    },
    {
      id: "code",
      label: "代码分析",
      icon: "fas fa-code",
      component: CodeAnalyzer,
    },
  ];

  // ⭐⭐⭐ 修改：学习分析只对教师和管理员可见 ⭐⭐⭐
  if (authStore.hasAnyRole(["teacher", "admin"])) {
    tabs.push({
      id: "analytics",
      label: "学习分析",
      icon: "fas fa-chart-line",
      component: LearningAnalytics,
    });
  }

  // 教师和管理员可以看到知识库管理
  if (authStore.hasPermission("manage_knowledge")) {
    tabs.push({
      id: "knowledge",
      label: "知识库管理",
      icon: "fas fa-book",
      component: KnowledgeBase,
    });
  }

  // 只有管理员可以看到用户管理
  if (authStore.hasPermission("manage_users")) {
    tabs.push({
      id: "admin",
      label: "用户管理",
      icon: "fas fa-users",
      component: UserManagement,
    });
  }

  return tabs;
});

const currentComponent = computed(() => {
  return availableTabs.value.find((tab) => tab.id === currentTab.value)
    ?.component;
});

function handleTabSwitch(tabId) {
  console.log("📑 切换标签:", currentTab.value, "→", tabId);
  currentTab.value = tabId;
}
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
  overflow: hidden;
}

.content-area {
  flex: 1;
  overflow: hidden;
}
</style>
