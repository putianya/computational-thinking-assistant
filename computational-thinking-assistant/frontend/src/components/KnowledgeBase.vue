<!-- filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\components\KnowledgeBase.vue -->
<template>
  <div class="knowledge-base">
    <!-- 顶部功能栏 -->
    <div class="header">
      <h1>📚 知识库管理</h1>
      <div class="actions">
        <input
          v-model="searchQuery"
          @input="handleSearch"
          type="text"
          placeholder="🔍 搜索文档名..."
          class="search-input"
        />

        <select v-model="sortBy" @change="handleSort" class="sort-select">
          <option value="modified_at">📅 修改时间</option>
          <option value="name">📝 文件名</option>
          <option value="size">📦 文件大小</option>
          <option value="chunks_count">🔢 知识块数</option>
        </select>

        <button
          @click="loadDocuments"
          class="action-btn refresh-btn"
          :disabled="isLoading"
        >
          <i class="fas fa-sync-alt" :class="{ 'fa-spin': isLoading }"></i>
          刷新
        </button>
        <button @click="handleUpload" class="action-btn primary-btn">
          <i class="fas fa-upload"></i>
          上传文档
        </button>
        <input
          ref="fileInput"
          type="file"
          accept=".md"
          style="display: none"
          @change="handleFileChange"
        />
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <div class="stat-card">
        <div class="stat-icon">📄</div>
        <div class="stat-content">
          <div class="stat-value">{{ filteredDocuments.length }}</div>
          <div class="stat-label">显示文档（{{ documents.length }} 总）</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📝</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.chunk_count || 0 }}</div>
          <div class="stat-label">知识块数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <div class="stat-value">{{ formatChars(stats.total_chars) }}</div>
          <div class="stat-label">总字符数</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🔍</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_retrieved || 0 }}</div>
          <div class="stat-label">总引用次数</div>
        </div>
      </div>
    </div>

    <!-- 文档列表 -->
    <div class="documents-section">
      <div v-if="isLoading" class="loading-state">
        <i class="fas fa-spinner fa-spin"></i>
        <span>加载中...</span>
      </div>

      <div v-else-if="filteredDocuments.length === 0" class="empty-state">
        <div class="empty-icon">{{ searchQuery ? "🔍" : "📭" }}</div>
        <h3>{{ searchQuery ? "未找到匹配的文档" : "暂无文档" }}</h3>
        <p>
          {{
            searchQuery ? "尝试修改搜索关键词" : '点击"上传文档"添加知识库内容'
          }}
        </p>
      </div>

      <div v-else class="documents-list">
        <div
          v-for="doc in filteredDocuments"
          :key="doc.name"
          class="document-card"
          :class="{ expanded: expandedDoc === doc.name }"
        >
          <!-- 文档头部 -->
          <div class="doc-header" @click="toggleExpand(doc.name)">
            <div class="doc-info">
              <i class="fas fa-file-alt doc-icon"></i>
              <div class="doc-details">
                <h3 class="doc-name">{{ doc.name }}</h3>
                <div class="doc-meta">
                  <span class="meta-item">
                    <i class="fas fa-puzzle-piece"></i>
                    {{ doc.chunks_count }} 个知识块
                  </span>
                  <span class="meta-item">
                    <i class="fas fa-weight"></i>
                    {{ formatSize(doc.size) }}
                  </span>
                  <span class="meta-item">
                    <i class="fas fa-clock"></i>
                    {{ formatTime(doc.modified_at) }}
                  </span>
                  <!-- ⭐⭐⭐ 新增：文档引用次数 ⭐⭐⭐ -->
                  <span
                    v-if="doc.total_retrieved > 0"
                    class="meta-item meta-retrieved"
                    :title="`该文档的知识块共被引用 ${doc.total_retrieved} 次`"
                  >
                    <i class="fas fa-quote-right"></i>
                    引用 {{ doc.total_retrieved }} 次
                  </span>
                </div>
              </div>
            </div>
            <div class="doc-actions">
              <button
                class="icon-btn danger-btn"
                @click.stop="handleDelete(doc.name)"
                title="删除文档"
              >
                <i class="fas fa-trash"></i>
              </button>
              <i
                class="fas expand-icon"
                :class="
                  expandedDoc === doc.name ? 'fa-chevron-up' : 'fa-chevron-down'
                "
              ></i>
            </div>
          </div>

          <!-- 知识块列表 -->
          <transition name="slide">
            <div v-if="expandedDoc === doc.name" class="chunks-section">
              <div v-if="loadingChunks" class="loading-chunks">
                <i class="fas fa-spinner fa-spin"></i>
                <span>加载知识块...</span>
              </div>
              <div v-else-if="docChunks.length === 0" class="no-chunks">
                暂无知识块
              </div>
              <div v-else class="chunks-list">
                <div
                  v-for="(chunk, index) in docChunks"
                  :key="chunk.id"
                  class="chunk-card"
                >
                  <div class="chunk-header">
                    <span class="chunk-badge">#{{ index + 1 }}</span>
                    <span class="chunk-title">{{ chunk.chapter }}</span>
                    <span v-if="chunk.section" class="chunk-subtitle"
                      >/ {{ chunk.section }}</span
                    >

                    <!-- ⭐⭐⭐ 引用次数标签（关键修复）⭐⭐⭐ -->
                    <span
                      v-if="chunk.retrieved_count > 0"
                      class="chunk-retrieved"
                      :title="getRetrievedTooltip(chunk)"
                    >
                      <i class="fas fa-quote-right"></i>
                      {{ chunk.retrieved_count }}
                    </span>

                    <span class="chunk-size">{{ chunk.char_count }} 字</span>
                  </div>
                  <div class="chunk-body">
                    <div class="chunk-content">{{ chunk.content }}</div>
                  </div>
                </div>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <ConfirmDialog
      v-if="showDeleteConfirm"
      title="删除文档"
      :message="`确定要删除文档「${deleteTarget}」吗？\n\n此操作将同时删除：\n• 物理文件\n• 所有知识块\n• 向量数据\n\n⚠️ 此操作不可恢复！`"
      confirmText="确认删除"
      cancelText="取消"
      :loading="isDeleting"
      @confirm="confirmDelete"
      @cancel="cancelDelete"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { knowledgeAPI } from "../api/knowledge";
import ConfirmDialog from "./ConfirmDialog.vue";

// ========== 数据状态 ==========
const documents = ref([]);
const stats = ref({});
const isLoading = ref(false);

// 搜索和排序状态
const searchQuery = ref("");
const sortBy = ref("modified_at");

// 展开/折叠
const expandedDoc = ref(null);
const docChunks = ref([]);
const loadingChunks = ref(false);

// 删除确认
const showDeleteConfirm = ref(false);
const deleteTarget = ref("");
const isDeleting = ref(false);

// 文件上传
const fileInput = ref(null);

// ========== 计算属性 ==========
const filteredDocuments = computed(() => {
  let result = [...documents.value];

  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter((doc) => doc.name.toLowerCase().includes(query));
  }

  result.sort((a, b) => {
    switch (sortBy.value) {
      case "name":
        return a.name.localeCompare(b.name);
      case "size":
        return b.size - a.size;
      case "chunks_count":
        return b.chunks_count - a.chunks_count;
      case "modified_at":
      default:
        return new Date(b.modified_at) - new Date(a.modified_at);
    }
  });

  return result;
});

// ========== 生命周期 ==========
onMounted(() => {
  loadDocuments();
  loadStats();
});

// ========== 加载数据 ==========
async function loadDocuments() {
  try {
    isLoading.value = true;
    const response = await knowledgeAPI.getDocuments();
    if (response.status === "success") {
      documents.value = response.data.documents;

      // ⭐⭐⭐ 调试：打印文档引用统计 ⭐⭐⭐
      console.log("📚 文档列表（含引用统计）:");
      documents.value.forEach((doc) => {
        if (doc.total_retrieved > 0) {
          console.log(`  📄 ${doc.name}: ${doc.total_retrieved} 次引用`);
        }
      });
    }
  } catch (error) {
    console.error("❌ 加载文档列表失败:", error);
    alert("加载失败: " + error.message);
  } finally {
    isLoading.value = false;
  }
}

async function loadStats() {
  try {
    const response = await knowledgeAPI.getStats();
    if (response.status === "success") {
      stats.value = response.data;
    }
  } catch (error) {
    console.error("❌ 加载统计信息失败:", error);
  }
}

async function toggleExpand(docName) {
  if (expandedDoc.value === docName) {
    expandedDoc.value = null;
    docChunks.value = [];
  } else {
    expandedDoc.value = docName;
    await loadDocumentChunks(docName);
  }
}

// ⭐⭐⭐ 关键修复：加载知识块数据 ⭐⭐⭐
async function loadDocumentChunks(filename) {
  try {
    loadingChunks.value = true;
    console.log(`📥 加载知识块: ${filename}`);

    const response = await knowledgeAPI.getDocumentChunks(filename);

    console.log("📦 API 响应:", response);

    if (response.status === "success") {
      // ⭐⭐⭐ 修复：确保正确提取 chunks 数组 ⭐⭐⭐
      docChunks.value = response.data.chunks || [];

      console.log(`✅ 加载了 ${docChunks.value.length} 个知识块`);

      // ⭐⭐⭐ 调试：打印每个知识块的引用次数 ⭐⭐⭐
      docChunks.value.forEach((chunk, index) => {
        console.log(`  知识块 ${index + 1}:`, {
          id: chunk.id,
          chapter: chunk.chapter,
          retrieved_count: chunk.retrieved_count,
          last_retrieved_at: chunk.last_retrieved_at,
        });
      });
    }
  } catch (error) {
    console.error("❌ 加载知识块失败:", error);
    docChunks.value = [];
  } finally {
    loadingChunks.value = false;
  }
}

// ========== 上传文档 ==========
function handleUpload() {
  fileInput.value.click();
}

async function handleFileChange(event) {
  const file = event.target.files[0];
  if (!file) return;

  if (!file.name.endsWith(".md")) {
    alert("只支持 .md 格式的文件");
    return;
  }

  try {
    isLoading.value = true;
    const response = await knowledgeAPI.uploadDocument(file);
    if (response.status === "success") {
      const msg = response.data.is_overwrite
        ? `文档已覆盖更新，共 ${response.data.chunks_count} 个知识块`
        : `上传成功，共 ${response.data.chunks_count} 个知识块`;
      alert(msg);
      await loadDocuments();
      await loadStats();
    }
  } catch (error) {
    console.error("❌ 上传失败:", error);
    alert("上传失败: " + error.message);
  } finally {
    isLoading.value = false;
    event.target.value = "";
  }
}

// ========== 删除文档 ==========
function handleDelete(docName) {
  deleteTarget.value = docName;
  showDeleteConfirm.value = true;
}

async function confirmDelete() {
  if (!deleteTarget.value) return;

  try {
    isDeleting.value = true;
    const response = await knowledgeAPI.deleteDocument(deleteTarget.value);
    if (response.status === "success") {
      alert(`文档「${deleteTarget.value}」已删除`);
      if (expandedDoc.value === deleteTarget.value) {
        expandedDoc.value = null;
        docChunks.value = [];
      }
      await loadDocuments();
      await loadStats();
    }
  } catch (error) {
    console.error("❌ 删除失败:", error);
    alert("删除失败: " + error.message);
  } finally {
    isDeleting.value = false;
    showDeleteConfirm.value = false;
    deleteTarget.value = "";
  }
}

function cancelDelete() {
  showDeleteConfirm.value = false;
  deleteTarget.value = "";
}

function handleSearch() {
  console.log("🔍 搜索:", searchQuery.value);
}

function handleSort() {
  console.log("📊 排序方式:", sortBy.value);
}

// ========== 工具函数 ==========
function formatSize(bytes) {
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  let i = 0;
  while (bytes >= 1024 && i < units.length - 1) {
    bytes /= 1024;
    i++;
  }
  return `${bytes.toFixed(1)} ${units[i]}`;
}

function formatChars(chars) {
  if (!chars) return "0";
  if (chars >= 10000) {
    return `${(chars / 10000).toFixed(1)}万`;
  }
  return chars.toString();
}

function formatTime(isoString) {
  if (!isoString) return "";
  const date = new Date(isoString);
  return date.toLocaleDateString("zh-CN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ⭐⭐⭐ 格式化引用时间 ⭐⭐⭐
function formatRetrievedTime(isoString) {
  if (!isoString) return "";
  const date = new Date(isoString);
  const now = new Date();
  const diff = now - date;

  // 1小时内
  if (diff < 60 * 60 * 1000) {
    const minutes = Math.floor(diff / (60 * 1000));
    return `${minutes}分钟前`;
  }

  // 24小时内
  if (diff < 24 * 60 * 60 * 1000) {
    const hours = Math.floor(diff / (60 * 60 * 1000));
    return `${hours}小时前`;
  }

  // 超过24小时
  return date.toLocaleDateString("zh-CN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ⭐⭐⭐ 获取引用提示文本 ⭐⭐⭐
function getRetrievedTooltip(chunk) {
  console.log("📌 生成提示:", chunk); // ⭐ 调试

  let tooltip = `被引用 ${chunk.retrieved_count} 次`;
  if (chunk.last_retrieved_at) {
    tooltip += `\n最后引用: ${formatRetrievedTime(chunk.last_retrieved_at)}`;
  }
  return tooltip;
}
</script>

<style scoped>
/* ========== 整体布局 ========== */
.knowledge-base {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 24px;
  background: #f0f2f5;
  gap: 20px;
  overflow: hidden;
}

/* ========== 顶部功能栏 ========== */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 20px 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  flex-shrink: 0;
}

.header h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #333;
}

.actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  padding: 10px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: all 0.2s;
  width: 200px;
  background: #f8f9fa;
}

.search-input:focus {
  border-color: #667eea;
  background: white;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.sort-select {
  padding: 10px 16px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  background: #f8f9fa;
  cursor: pointer;
  transition: all 0.2s;
}

.sort-select:hover {
  border-color: #667eea;
}

/* ========== 通用按钮样式 ========== */
.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn {
  background: #f0f0f0;
  color: #666;
}

.refresh-btn:hover:not(:disabled) {
  background: #e4e4e4;
}

.refresh-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.primary-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.primary-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.icon-btn {
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.danger-btn {
  background: #fff1f0;
  color: #ff4d4f;
}

.danger-btn:hover {
  background: #ffccc7;
  transform: scale(1.05);
}

/* ========== 统计卡片 ========== */
.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  flex-shrink: 0;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: all 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  font-size: 32px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #333;
  line-height: 1;
}

.stat-label {
  font-size: 13px;
  color: #999;
  margin-top: 4px;
}

/* ========== 文档列表 ========== */
.documents-section {
  flex: 1;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.documents-list {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* ========== 加载和空状态 ========== */
.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  color: #999;
  gap: 12px;
}

.loading-state i {
  font-size: 32px;
  color: #667eea;
}

.empty-icon {
  font-size: 64px;
  opacity: 0.5;
}

.empty-state h3 {
  margin: 0;
  font-size: 16px;
  color: #666;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}

/* ========== 文档卡片 ========== */
.document-card {
  background: #fafbfc;
  border: 1px solid #e8eaed;
  border-radius: 10px;
  margin-bottom: 12px;
  overflow: hidden;
  transition: all 0.2s;
}

.document-card:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
}

.document-card:last-child {
  margin-bottom: 0;
}

.doc-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  cursor: pointer;
  background: white;
  transition: background 0.2s;
}

.doc-header:hover {
  background: #f8f9fa;
}

.doc-info {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.doc-icon {
  font-size: 24px;
  color: #667eea;
}

.doc-name {
  margin: 0 0 6px;
  font-size: 15px;
  font-weight: 600;
  color: #333;
}

.doc-meta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #999;
  transition: all 0.2s;
}

.meta-item i {
  font-size: 11px;
}

.doc-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.expand-icon {
  color: #999;
  transition: transform 0.3s;
}

.document-card.expanded .expand-icon {
  transform: rotate(180deg);
  color: #667eea;
}

/* ========== 知识块区域 ========== */
.chunks-section {
  background: #f5f7fa;
  border-top: 1px solid #e8eaed;
  padding: 16px 20px;
  max-height: 500px;
  overflow-y: auto;
}

.loading-chunks,
.no-chunks {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  color: #999;
  font-size: 14px;
}

.chunks-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ========== 知识块卡片 ========== */
.chunk-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s;
}

.chunk-card:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.12);
}

.chunk-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: #fafbfc;
  border-bottom: 1px solid #f0f0f0;
  flex-wrap: wrap;
}

.chunk-badge {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.chunk-title {
  font-weight: 600;
  font-size: 14px;
  color: #333;
}

.chunk-subtitle {
  font-size: 13px;
  color: #666;
}

/* ⭐⭐⭐ 文档引用次数样式 ⭐⭐⭐ */
.meta-retrieved {
  color: #10b981 !important;
  font-weight: 600;
  background: linear-gradient(
    135deg,
    rgba(16, 185, 129, 0.1) 0%,
    rgba(5, 150, 105, 0.15) 100%
  );
  padding: 4px 10px;
  border-radius: 12px;
  cursor: help;
}

.meta-retrieved:hover {
  background: linear-gradient(
    135deg,
    rgba(16, 185, 129, 0.15) 0%,
    rgba(5, 150, 105, 0.2) 100%
  );
  transform: scale(1.05);
}

.meta-retrieved i {
  color: #10b981;
  margin-right: 2px;
}

/* ========== 知识块引用次数标签 ========== */
.chunk-retrieved {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(16, 185, 129, 0.3);
  cursor: help;
  transition: all 0.2s;
  flex-shrink: 0;
}

.chunk-retrieved:hover {
  transform: scale(1.05);
  box-shadow: 0 3px 8px rgba(16, 185, 129, 0.4);
}

.chunk-retrieved i {
  font-size: 10px;
}

.chunk-size {
  margin-left: auto;
  font-size: 12px;
  color: #999;
  background: #f0f0f0;
  padding: 2px 8px;
  border-radius: 4px;
  flex-shrink: 0;
}

/* ========== 知识块内容滚动 ========== */
.chunk-body {
  padding: 12px 16px;
  max-height: 200px;
  overflow-y: auto;
}

.chunk-content {
  font-size: 13px;
  line-height: 1.7;
  color: #555;
  white-space: pre-wrap;
  word-break: break-word;
}

/* ========== 滚动条美化 ========== */
.documents-list::-webkit-scrollbar,
.chunks-section::-webkit-scrollbar,
.chunk-body::-webkit-scrollbar {
  width: 6px;
}

.documents-list::-webkit-scrollbar-track,
.chunks-section::-webkit-scrollbar-track,
.chunk-body::-webkit-scrollbar-track {
  background: #f5f5f5;
  border-radius: 3px;
}

.documents-list::-webkit-scrollbar-thumb,
.chunks-section::-webkit-scrollbar-thumb,
.chunk-body::-webkit-scrollbar-thumb {
  background: #d0d0d0;
  border-radius: 3px;
}

.documents-list::-webkit-scrollbar-thumb:hover,
.chunks-section::-webkit-scrollbar-thumb:hover,
.chunk-body::-webkit-scrollbar-thumb:hover {
  background: #b0b0b0;
}

/* ========== 展开动画 ========== */
.slide-enter-active,
.slide-leave-active {
  transition: all 0.3s ease;
  max-height: 500px;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
  max-height: 0;
}

/* ========== 响应式 ========== */
@media (max-width: 768px) {
  .knowledge-base {
    padding: 16px;
  }

  .header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .actions {
    flex-wrap: wrap;
  }

  .search-input {
    flex: 1;
    min-width: 150px;
  }

  .stats-section {
    grid-template-columns: repeat(2, 1fr);
  }

  .stat-card {
    padding: 16px;
  }

  .stat-icon {
    font-size: 24px;
  }

  .stat-value {
    font-size: 20px;
  }

  .doc-meta {
    flex-direction: column;
    gap: 4px;
  }

  .chunk-body {
    max-height: 150px;
  }

  .chunk-retrieved {
    font-size: 11px;
    padding: 3px 8px;
  }
}
</style>
