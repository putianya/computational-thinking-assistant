<!-- filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\components\KnowledgeBase.vue -->
<template>
  <div class="knowledge-base">
    <!-- 顶部功能栏 -->
    <div class="header">
      <h1>📚 知识库管理</h1>

      <div class="actions">
        <!-- 搜索框 -->
        <input
          v-model="searchQuery"
          type="text"
          placeholder="🔍 搜索知识块..."
          class="search-input"
          @input="handleSearch"
        />

        <!-- ⭐⭐⭐ 上传按钮（权限控制）⭐⭐⭐ -->
        <label v-if="authStore.hasPermission('upload_doc')" class="upload-btn">
          <i class="fas fa-upload"></i>
          上传文档
          <input type="file" accept=".md" @change="handleFileSelect" hidden />
        </label>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <div class="stat-card">
        <div class="stat-icon">📦</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_chunks || 0 }}</div>
          <div class="stat-label">知识块总数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">🧠</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_vectors || 0 }}</div>
          <div class="stat-label">向量总数</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">🔥</div>
        <div class="stat-content">
          <div class="stat-value">
            {{ stats.hot_chunks?.[0]?.chapter || "暂无" }}
          </div>
          <div class="stat-label">
            热门内容 ({{ stats.hot_chunks?.[0]?.retrieved_count || 0 }}次)
          </div>
        </div>
      </div>
    </div>

    <!-- 过滤器 -->
    <div class="filters">
      <select
        v-model="filterSource"
        @change="handleFilter"
        class="filter-select"
      >
        <option value="">全部来源</option>
        <option v-for="src in sources" :key="src.name" :value="src.name">
          {{ src.name }} ({{ src.count }})
        </option>
      </select>

      <select
        v-model="filterChapter"
        @change="handleFilter"
        class="filter-select"
      >
        <option value="">全部章节</option>
        <option v-for="ch in chapters" :key="ch.name" :value="ch.name">
          {{ ch.name }} ({{ ch.count }})
        </option>
      </select>

      <button @click="resetFilters" class="reset-btn">重置</button>
    </div>

    <!-- 知识块列表 -->
    <div class="chunks-section">
      <!-- 加载中 -->
      <div v-if="isLoading" class="loading">
        <i class="fas fa-spinner fa-spin"></i>
        加载中...
      </div>

      <!-- 空状态 -->
      <div v-else-if="chunks.length === 0" class="empty-state">
        <div class="empty-icon">📭</div>
        <p>暂无知识块</p>
        <!-- ⭐ 只有有权限的用户才能看到上传提示 -->
        <button
          v-if="authStore.hasPermission('upload_doc')"
          @click="handleUploadClick"
          class="empty-action"
        >
          上传第一个文档
        </button>
      </div>

      <!-- 知识块表格 -->
      <table v-else class="chunks-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>来源</th>
            <th>章节</th>
            <th>内容预览</th>
            <th>字符数</th>
            <th>热度</th>
            <!-- ⭐⭐⭐ 操作列（权限控制）⭐⭐⭐ -->
            <th
              v-if="
                authStore.hasPermission('edit_knowledge') ||
                authStore.hasPermission('delete_knowledge')
              "
            >
              操作
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="chunk in chunks" :key="chunk.id">
            <td>{{ chunk.id }}</td>
            <td>
              <span class="source-tag">{{ chunk.source }}</span>
            </td>
            <td>{{ chunk.chapter || "未分类" }}</td>
            <td class="content-preview">
              {{ chunk.content.substring(0, 50) }}...
            </td>
            <td>{{ chunk.char_count }}</td>
            <td>
              <span class="heat-badge"> ⭐ {{ chunk.retrieved_count }} </span>
            </td>
            <!-- ⭐⭐⭐ 操作按钮（权限控制）⭐⭐⭐ -->
            <td
              v-if="
                authStore.hasPermission('edit_knowledge') ||
                authStore.hasPermission('delete_knowledge')
              "
              class="actions-cell"
            >
              <!-- 编辑按钮 -->
              <button
                v-if="authStore.hasPermission('edit_knowledge')"
                @click="handleEdit(chunk)"
                class="action-btn edit-btn"
                title="编辑"
              >
                <i class="fas fa-edit"></i>
              </button>
              <!-- 删除按钮 -->
              <button
                v-if="authStore.hasPermission('delete_knowledge')"
                @click="handleDelete(chunk.id)"
                class="action-btn delete-btn"
                title="删除"
              >
                <i class="fas fa-trash"></i>
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 分页 -->
      <div v-if="pagination.pages > 1" class="pagination">
        <button
          @click="handlePageChange(pagination.page - 1)"
          :disabled="pagination.page === 1"
          class="page-btn"
        >
          上一页
        </button>

        <span class="page-info">
          第 {{ pagination.page }} / {{ pagination.pages }} 页 （共
          {{ pagination.total }} 条）
        </span>

        <button
          @click="handlePageChange(pagination.page + 1)"
          :disabled="pagination.page === pagination.pages"
          class="page-btn"
        >
          下一页
        </button>
      </div>
    </div>

    <!-- 编辑对话框 -->
    <div v-if="showEditDialog" class="modal-overlay" @click="closeEditDialog">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>✏️ 编辑知识块</h3>
          <button @click="closeEditDialog" class="close-btn">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label>章节</label>
            <input v-model="editForm.chapter" type="text" />
          </div>

          <div class="form-group">
            <label>内容</label>
            <textarea v-model="editForm.content" rows="10"></textarea>
          </div>

          <div class="form-group">
            <label>关键词（用逗号分隔）</label>
            <input v-model="editForm.keywords" type="text" />
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeEditDialog" class="cancel-btn">取消</button>
          <button @click="handleSaveEdit" class="save-btn" :disabled="isSaving">
            {{ isSaving ? "保存中..." : "保存" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useAuthStore } from "../stores/user"; // ⭐ 导入
import { knowledgeAPI } from "../api/knowledge";

const authStore = useAuthStore(); // ⭐ 获取实例

// ========== 数据状态 ==========
const chunks = ref([]);
const stats = ref({});
const isLoading = ref(false);
const isSaving = ref(false);

// 分页
const pagination = ref({
  page: 1,
  per_page: 20,
  total: 0,
  pages: 0,
});

// 过滤和搜索
const searchQuery = ref("");
const filterSource = ref("");
const filterChapter = ref("");

// 编辑
const showEditDialog = ref(false);
const editingChunk = ref(null);
const editForm = ref({
  chapter: "",
  content: "",
  keywords: "",
});

// 来源和章节选项
const sources = computed(() => stats.value.sources || []);
const chapters = computed(() => stats.value.chapters || []);

// ========== 生命周期 ==========
onMounted(() => {
  loadChunks();
  loadStats();
});

// ========== 加载数据方法 ==========

/**
 * 加载知识块列表
 */
async function loadChunks() {
  try {
    isLoading.value = true;

    const params = {
      page: pagination.value.page,
      per_page: pagination.value.per_page,
    };

    if (searchQuery.value) params.search = searchQuery.value;
    if (filterSource.value) params.source = filterSource.value;
    if (filterChapter.value) params.chapter = filterChapter.value;

    const response = await knowledgeAPI.getChunks(params);

    if (response.status === "success") {
      chunks.value = response.data.chunks;
      pagination.value = response.data.pagination;
      console.log("✅ 加载知识块成功:", chunks.value.length);
    }
  } catch (error) {
    console.error("❌ 加载知识块失败:", error);
    alert("加载失败: " + error.message);
  } finally {
    isLoading.value = false;
  }
}

/**
 * 加载统计信息
 */
async function loadStats() {
  try {
    const response = await knowledgeAPI.getStats();

    if (response.status === "success") {
      stats.value = response.data;
      console.log("✅ 加载统计成功:", stats.value);
    }
  } catch (error) {
    console.error("❌ 加载统计失败:", error);
  }
}

// ========== 上传文件 ==========

/**
 * 文件选择
 */
function handleFileSelect(event) {
  const file = event.target.files[0];
  if (file) {
    handleUpload(file);
  }
}

/**
 * 点击上传按钮
 */
function handleUploadClick() {
  document.querySelector('input[type="file"]').click();
}

/**
 * 上传文件
 */
async function handleUpload(file) {
  // 验证文件类型
  if (!file.name.endsWith(".md")) {
    alert("只支持 Markdown 文件（.md）");
    return;
  }

  // 验证文件大小（5MB）
  if (file.size > 5 * 1024 * 1024) {
    alert("文件过大，最大支持 5MB");
    return;
  }

  try {
    console.log("📤 上传文件:", file.name);

    const response = await knowledgeAPI.uploadDocument(file);

    if (response.status === "success") {
      alert(
        `上传成功！\n文件: ${response.data.file_name}\n知识块: ${response.data.chunks_count}`,
      );

      // 重新加载数据
      loadChunks();
      loadStats();
    }
  } catch (error) {
    console.error("❌ 上传失败:", error);
    alert("上传失败: " + error.message);
  }
}

// ========== 删除知识块 ==========

/**
 * 删除知识块
 */
async function handleDelete(chunkId) {
  if (!confirm("确定要删除这个知识块吗？此操作不可恢复。")) {
    return;
  }

  try {
    console.log("🗑️ 删除知识块:", chunkId);

    const response = await knowledgeAPI.deleteChunk(chunkId);

    if (response.status === "success") {
      alert("删除成功");

      // 重新加载数据
      loadChunks();
      loadStats();
    }
  } catch (error) {
    console.error("❌ 删除失败:", error);
    alert("删除失败: " + error.message);
  }
}

// ========== 编辑知识块 ==========

/**
 * 打开编辑对话框
 */
function handleEdit(chunk) {
  editingChunk.value = chunk;
  editForm.value = {
    chapter: chunk.chapter || "",
    content: chunk.content || "",
    keywords: chunk.keywords?.join(", ") || "",
  };
  showEditDialog.value = true;
}

/**
 * 关闭编辑对话框
 */
function closeEditDialog() {
  showEditDialog.value = false;
  editingChunk.value = null;
  editForm.value = { chapter: "", content: "", keywords: "" };
}

/**
 * 保存编辑
 */
async function handleSaveEdit() {
  if (!editForm.value.content.trim()) {
    alert("内容不能为空");
    return;
  }

  try {
    isSaving.value = true;

    const data = {
      chapter: editForm.value.chapter,
      content: editForm.value.content,
      keywords: editForm.value.keywords
        .split(",")
        .map((k) => k.trim())
        .filter((k) => k),
    };

    const response = await knowledgeAPI.updateChunk(
      editingChunk.value.id,
      data,
    );

    if (response.status === "success") {
      alert("保存成功");
      closeEditDialog();
      loadChunks();
    }
  } catch (error) {
    console.error("❌ 保存失败:", error);
    alert("保存失败: " + error.message);
  } finally {
    isSaving.value = false;
  }
}

// ========== 搜索和过滤 ==========

/**
 * 搜索
 */
let searchTimeout = null;
function handleSearch() {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    pagination.value.page = 1;
    loadChunks();
  }, 500);
}

/**
 * 过滤
 */
function handleFilter() {
  pagination.value.page = 1;
  loadChunks();
}

/**
 * 重置过滤
 */
function resetFilters() {
  searchQuery.value = "";
  filterSource.value = "";
  filterChapter.value = "";
  pagination.value.page = 1;
  loadChunks();
}

// ========== 分页 ==========

/**
 * 页码变化
 */
function handlePageChange(page) {
  pagination.value.page = page;
  loadChunks();
}
</script>

<style scoped>
/* ========== 整体布局 ========== */
.knowledge-base {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
}

/* ========== 顶部功能栏 ========== */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.actions {
  display: flex;
  gap: 12px;
}

.search-input {
  padding: 10px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 14px;
  width: 300px;
  transition: all 0.3s;
}

.search-input:focus {
  outline: none;
  border-color: #667eea;
}

.upload-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;
}

.upload-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* ========== 统计卡片 ========== */
.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 48px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: #333;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

/* ========== 过滤器 ========== */
.filters {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  background: white;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.filter-select {
  padding: 8px 12px;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
}

.reset-btn {
  padding: 8px 16px;
  background: #f5f5f5;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.reset-btn:hover {
  background: #e0e0e0;
}

/* ========== 知识块列表 ========== */
.chunks-section {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.loading {
  text-align: center;
  padding: 40px;
  color: #999;
  font-size: 16px;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.empty-action {
  padding: 10px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  margin-top: 16px;
}

.chunks-table {
  width: 100%;
  border-collapse: collapse;
}

.chunks-table th {
  background: #f5f5f5;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  color: #666;
  border-bottom: 2px solid #e0e0e0;
}

.chunks-table td {
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.source-tag {
  display: inline-block;
  padding: 4px 8px;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 4px;
  font-size: 12px;
}

.content-preview {
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #666;
}

.heat-badge {
  display: inline-block;
  padding: 4px 8px;
  background: #fff3e0;
  color: #f57c00;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.actions-cell {
  display: flex;
  gap: 8px;
}

.action-btn {
  padding: 6px 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.edit-btn {
  background: #e3f2fd;
  color: #1976d2;
}

.edit-btn:hover {
  background: #1976d2;
  color: white;
}

.delete-btn {
  background: #ffebee;
  color: #d32f2f;
}

.delete-btn:hover {
  background: #d32f2f;
  color: white;
}

/* ========== 分页 ========== */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
}

.page-btn {
  padding: 8px 16px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.page-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.page-info {
  color: #666;
  font-size: 14px;
}

/* ========== 编辑对话框 ========== */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h3 {
  margin: 0;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #999;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group textarea {
  width: 100%;
  padding: 10px;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 14px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #e0e0e0;
}

.cancel-btn {
  padding: 10px 20px;
  background: #f5f5f5;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.save-btn {
  padding: 10px 20px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

.save-btn:disabled {
  background: #ccc;
  cursor: not-allowed;
}
</style>
