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
import UserManagement from "./UserManagement.vue";

const authStore = useAuthStore();
const currentTab = ref("chat");

// ⭐⭐⭐ 根据用户角色动态显示标签 ⭐⭐⭐
const availableTabs = computed(() => {
  const tabs = [
    {
      id: "chat",
      label: "对话",
      icon: "fas fa-comments",
      component: ChatView,
    },
  ];

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

// ⭐⭐⭐ 当前显示的组件 ⭐⭐⭐
const currentComponent = computed(() => {
  return availableTabs.value.find((tab) => tab.id === currentTab.value)
    ?.component;
});

// ⭐⭐⭐ 标签切换处理 ⭐⭐⭐
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
  overflow: hidden; /* ⭐ 关键：防止整体滚动 */
}

.content-area {
  flex: 1;
  overflow: hidden; /* ⭐ 关键：让子组件自己处理滚动 */
}

/* ⭐⭐⭐ 确保 Font Awesome 图标可用 ⭐⭐⭐ */
/* 如果图标不显示，在 index.html 中添加：
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
*/
</style>
