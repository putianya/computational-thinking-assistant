<!-- filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\components\KnowledgeBase.vue -->
<template>
  <div class="knowledge-base">
    <!-- 头部功能栏 -->
    <div class="header">
      <h1>📚 知识库管理</h1>
      <div class="actions">
        <input
          v-model="searchQuery"
          @input="handleSearch"
          type="text"
          placeholder="搜索知识内容..."
          class="search-input"
        />
        <button @click="handleUpload" class="upload-btn">
          <i class="fas fa-upload"></i>
          上传文档
        </button>
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
            {{ stats.hot_chunks ? stats.hot_chunks[0]?.retrieved_count : 0 }}次
          </div>
          <div class="stat-label">热门内容</div>
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
        <option
          v-for="source in sources"
          :key="source.name"
          :value="source.name"
        >
          {{ source.name }} ({{ source.count }})
        </option>
      </select>

      <select
        v-model="filterChapter"
        @change="handleFilter"
        class="filter-select"
      >
        <option value="">全部章节</option>
        <option
          v-for="chapter in chapters"
          :key="chapter.name"
          :value="chapter.name"
        >
          {{ chapter.name }} ({{ chapter.count }})
        </option>
      </select>

      <button @click="handleResetFilter" class="reset-btn">重置</button>
    </div>

    <!-- 加载中 -->
    <div v-if="isLoading" class="loading">
      <i class="fas fa-spinner fa-spin"></i>
      加载中...
    </div>

    <!-- 空状态 -->
    <div v-else-if="chunks.length === 0" class="empty-state">
      <div class="empty-icon">📭</div>
      <p>暂无知识块数据</p>
    </div>

    <!-- 知识块列表 -->
    <div v-else class="chunks-section">
      <table class="chunks-table">
        <thead>
          <tr>
            <!-- ⭐ ID 列（可排序） -->
            <th @click="handleSort('id')" class="sortable">
              ID
              <span class="sort-icon">
                <i
                  v-if="sortField === 'id' && sortOrder === 'asc'"
                  class="fas fa-caret-up"
                ></i>
                <i
                  v-else-if="sortField === 'id' && sortOrder === 'desc'"
                  class="fas fa-caret-down"
                ></i>
                <i v-else class="fas fa-sort"></i>
              </span>
            </th>

            <!-- ⭐ 来源列（可排序） -->
            <th @click="handleSort('source')" class="sortable">
              来源
              <span class="sort-icon">
                <i
                  v-if="sortField === 'source' && sortOrder === 'asc'"
                  class="fas fa-caret-up"
                ></i>
                <i
                  v-else-if="sortField === 'source' && sortOrder === 'desc'"
                  class="fas fa-caret-down"
                ></i>
                <i v-else class="fas fa-sort"></i>
              </span>
            </th>

            <!-- ⭐ 章节列（可排序） -->
            <th @click="handleSort('chapter')" class="sortable">
              章节
              <span class="sort-icon">
                <i
                  v-if="sortField === 'chapter' && sortOrder === 'asc'"
                  class="fas fa-caret-up"
                ></i>
                <i
                  v-else-if="sortField === 'chapter' && sortOrder === 'desc'"
                  class="fas fa-caret-down"
                ></i>
                <i v-else class="fas fa-sort"></i>
              </span>
            </th>

            <th>内容预览</th>
            <th>字符数</th>
            <th>热度</th>
            <th>操作</th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="chunk in chunks" :key="chunk.id">
            <td>{{ chunk.id }}</td>
            <td>
              <span class="source-tag">{{ chunk.source }}</span>
            </td>
            <td>{{ chunk.chapter || "-" }}</td>
            <td>
              <div class="content-preview">{{ chunk.content }}</div>
            </td>
            <td>{{ chunk.char_count || 0 }}</td>
            <td>
              <span class="heat-badge">{{ chunk.retrieved_count || 0 }}次</span>
            </td>
            <td class="actions-cell">
              <button
                @click="handleEdit(chunk)"
                class="action-btn edit-btn"
                title="编辑"
              >
                <i class="fas fa-edit"></i>
              </button>
              <button
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
    </div>

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
        第 {{ pagination.page }} / {{ pagination.pages }} 页
      </span>

      <button
        @click="handlePageChange(pagination.page + 1)"
        :disabled="pagination.page === pagination.pages"
        class="page-btn"
      >
        下一页
      </button>
    </div>

    <!-- 编辑对话框 -->
    <div v-if="showEditDialog" class="modal-overlay" @click="closeEditDialog">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>编辑知识块</h3>
          <button class="close-btn" @click="closeEditDialog">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <label for="edit-chapter">章节</label>
            <input
              id="edit-chapter"
              v-model="editForm.chapter"
              type="text"
              placeholder="如：指针的应用"
            />
          </div>

          <div class="form-group">
            <label for="edit-content">内容</label>
            <textarea
              id="edit-content"
              v-model="editForm.content"
              rows="8"
              placeholder="知识块内容..."
            ></textarea>
          </div>

          <div class="form-group">
            <label for="edit-keywords">关键词</label>
            <input
              id="edit-keywords"
              v-model="editForm.keywords"
              type="text"
              placeholder="用逗号分隔，如：指针,内存,变量"
            />
          </div>
        </div>

        <div class="modal-footer">
          <button @click="closeEditDialog" class="cancel-btn">取消</button>
          <button @click="confirmEdit" :disabled="isSaving" class="save-btn">
            {{ isSaving ? "保存中..." : "保存" }}
          </button>
        </div>
      </div>
    </div>

    <!-- 隐藏的文件上传输入框 -->
    <input
      ref="fileInput"
      type="file"
      accept=".md"
      style="display: none"
      @change="handleFileChange"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useAuthStore } from "../stores/user";
import { knowledgeAPI } from "../api/knowledge";

const authStore = useAuthStore();

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

// ⭐⭐⭐ 排序状态 ⭐⭐⭐
const sortField = ref("id");
const sortOrder = ref("asc");

// 编辑
const showEditDialog = ref(false);
const editingChunk = ref(null);
const editForm = ref({
  chapter: "",
  content: "",
  keywords: "",
});

// 文件上传
const fileInput = ref(null);

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
      source: filterSource.value,
      chapter: filterChapter.value,
      search: searchQuery.value,
      sort_by: sortField.value,
      order: sortOrder.value,
    };

    const response = await knowledgeAPI.getChunks(params);

    if (response.status === "success") {
      chunks.value = response.data.chunks;
      pagination.value = response.data.pagination;
      console.log(`✅ 加载了 ${chunks.value.length} 个知识块`);
    } else {
      alert("加载失败: " + response.message);
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
    }
  } catch (error) {
    console.error("❌ 加载统计失败:", error);
  }
}

// ========== 排序方法 ==========

/**
 * 处理排序（点击表头）
 */
function handleSort(field) {
  console.log(`🔄 排序: ${field}`);

  if (sortField.value === field) {
    sortOrder.value = sortOrder.value === "asc" ? "desc" : "asc";
  } else {
    sortField.value = field;
    sortOrder.value = "asc";
  }

  pagination.value.page = 1;
  loadChunks();
}

// ========== ⭐⭐⭐ 编辑和删除方法（恢复）⭐⭐⭐ ==========

/**
 * 打开编辑对话框
 */
function handleEdit(chunk) {
  console.log("✏️ 编辑知识块:", chunk.id);

  editingChunk.value = chunk;
  editForm.value = {
    chapter: chunk.chapter || "",
    content: chunk.content || "",
    keywords: chunk.keywords ? chunk.keywords.join(", ") : "",
  };
  showEditDialog.value = true;
}

/**
 * 关闭编辑对话框
 */
function closeEditDialog() {
  showEditDialog.value = false;
  editingChunk.value = null;
  editForm.value = {
    chapter: "",
    content: "",
    keywords: "",
  };
}

/**
 * 确认编辑
 */
async function confirmEdit() {
  if (!editingChunk.value) return;

  try {
    isSaving.value = true;

    const data = {
      chapter: editForm.value.chapter,
      content: editForm.value.content,
      keywords: editForm.value.keywords,
    };

    const response = await knowledgeAPI.updateChunk(
      editingChunk.value.id,
      data,
    );

    if (response.status === "success") {
      alert("修改成功！");
      closeEditDialog();
      loadChunks(); // 重新加载列表
    } else {
      alert("修改失败: " + response.message);
    }
  } catch (error) {
    console.error("❌ 修改失败:", error);
    alert("修改失败: " + error.message);
  } finally {
    isSaving.value = false;
  }
}

/**
 * 删除知识块
 */
async function handleDelete(chunkId) {
  if (!confirm("确定要删除这个知识块吗？此操作不可恢复！")) {
    return;
  }

  try {
    console.log("🗑️ 删除知识块:", chunkId);

    const response = await knowledgeAPI.deleteChunk(chunkId);

    if (response.status === "success") {
      alert("删除成功！");
      loadChunks(); // 重新加载列表
      loadStats(); // 更新统计信息
    } else {
      alert("删除失败: " + response.message);
    }
  } catch (error) {
    console.error("❌ 删除失败:", error);
    alert("删除失败: " + error.message);
  }
}

// ========== 其他方法 ==========

/**
 * 搜索
 */
function handleSearch() {
  pagination.value.page = 1;
  loadChunks();
}

/**
 * 过滤
 */
function handleFilter() {
  pagination.value.page = 1;
  loadChunks();
}

/**
 * 重置过滤器
 */
function handleResetFilter() {
  searchQuery.value = "";
  filterSource.value = "";
  filterChapter.value = "";
  pagination.value.page = 1;
  loadChunks();
}

/**
 * 翻页
 */
function handlePageChange(newPage) {
  if (newPage < 1 || newPage > pagination.value.pages) return;
  pagination.value.page = newPage;
  loadChunks();
}

/**
 * 上传文档
 */
function handleUpload() {
  fileInput.value.click();
}

/**
 * 文件选择后上传
 */
async function handleFileChange(event) {
  const file = event.target.files[0];
  if (!file) return;

  if (!file.name.endsWith(".md")) {
    alert("只支持 Markdown 文件（.md）");
    return;
  }

  try {
    console.log("📤 上传文件:", file.name);

    const response = await knowledgeAPI.uploadDocument(file);

    if (response.status === "success") {
      alert(`上传成功！已导入 ${response.data.chunks_count} 个知识块`);
      loadChunks();
      loadStats();
    } else {
      alert("上传失败: " + response.message);
    }
  } catch (error) {
    console.error("❌ 上传失败:", error);
    alert("上传失败: " + error.message);
  } finally {
    // 重置文件输入框
    event.target.value = "";
  }
}
</script>

<style scoped>
/* ========== 整体布局 ========== */
.knowledge-base {
  padding: 16px;
  background: #f5f5f5;
  min-height: 100vh;
}

/* ========== 顶部功能栏 ========== */
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  background: white;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.header h1 {
  margin: 0;
  font-size: 22px;
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
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}

.stat-card {
  background: white;
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  display: flex;
  align-items: center;
  gap: 10px;
}

.stat-icon {
  font-size: 32px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 22px;
  font-weight: 600;
  color: #333;
}

.stat-label {
  font-size: 12px;
  color: #666;
  margin-top: 2px;
}

/* ========== 过滤器 ========== */
.filters {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
  background: white;
  padding: 12px;
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
  padding: 0;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  max-height: 600px;
  overflow-y: auto;
  overflow-x: hidden;
}

.chunks-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.chunks-table thead {
  position: sticky;
  top: 0;
  background: #fafafa;
  z-index: 10;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.chunks-table th {
  background: #fafafa;
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  font-size: 13px;
  color: #666;
  border-bottom: 1px solid #e0e0e0;
}

.chunks-table th:first-child {
  padding-left: 16px;
  border-top-left-radius: 12px;
}

.chunks-table th:last-child {
  padding-right: 16px;
  border-top-right-radius: 12px;
}

.chunks-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #f5f5f5;
  overflow: hidden;
  text-overflow: ellipsis;
  font-size: 14px;
}

.chunks-table td:first-child {
  padding-left: 16px;
}

.chunks-table td:last-child {
  padding-right: 16px;
}

.chunks-table tbody tr:hover {
  background: #f9fafb;
}

/* 可排序的表头 */
.sortable {
  cursor: pointer;
  user-select: none;
  position: relative;
  transition: background 0.2s;
}

.sortable:hover {
  background: #e8e8e8;
}

.sort-icon {
  margin-left: 6px;
  font-size: 12px;
  color: #999;
  transition: color 0.2s;
}

.sortable:hover .sort-icon {
  color: #667eea;
}

.sortable .sort-icon i.fa-caret-up,
.sortable .sort-icon i.fa-caret-down {
  color: #667eea;
  font-weight: bold;
}

/* 来源标签 */
.source-tag {
  display: inline-block;
  padding: 4px 10px;
  background: #e3f2fd;
  color: #1976d2;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

/* 内容预览 */
.content-preview {
  max-width: 400px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: #555;
  font-size: 13px;
}

/* 热度徽章 */
.heat-badge {
  display: inline-block;
  padding: 4px 10px;
  background: #fff3e0;
  color: #f57c00;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

/* 操作按钮 */
.actions-cell {
  display: flex;
  gap: 6px;
}

.action-btn {
  padding: 5px 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.edit-btn {
  background: #e3f2fd;
  color: #1976d2;
}

.edit-btn:hover {
  background: #bbdefb;
}

.delete-btn {
  background: #ffebee;
  color: #c62828;
}

.delete-btn:hover {
  background: #ffcdd2;
}

/* 滚动条样式美化 */
.chunks-section::-webkit-scrollbar {
  width: 6px;
}

.chunks-section::-webkit-scrollbar-track {
  background: #f5f5f5;
  border-radius: 3px;
}

.chunks-section::-webkit-scrollbar-thumb {
  background: #d0d0d0;
  border-radius: 3px;
  transition: background 0.2s;
}

.chunks-section::-webkit-scrollbar-thumb:hover {
  background: #aaa;
}

/* 加载/空状态 */
.loading,
.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #999;
}

.loading {
  font-size: 16px;
}

.empty-state {
  font-size: 15px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 12px;
  opacity: 0.5;
}

/* 编辑对话框 */
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
}

/* 分页组件 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-top: 16px;
  padding: 16px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.page-btn {
  padding: 8px 12px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.page-btn:hover:not(:disabled) {
  background: #f0f4ff;
  border-color: #667eea;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: #666;
}
</style>
