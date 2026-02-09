<template>
  <div class="code-analyzer">
    <!-- 左侧：代码编辑区 -->
    <div class="editor-panel">
      <div class="editor-header">
        <h3>📝 C语言代码编辑器</h3>
        <div class="editor-actions">
          <!-- 分析类型选择 -->
          <select v-model="analysisType" class="analysis-type-select">
            <option value="syntax">仅语法检查</option>
            <option value="logic">仅逻辑分析</option>
            <option value="full">完整分析</option>
          </select>

          <button
            @click="handleClear"
            class="btn-clear"
            :disabled="!code.trim()"
          >
            <i class="fas fa-eraser"></i> 清空
          </button>

          <button
            @click="handleAnalyze"
            class="btn-analyze"
            :disabled="!code.trim() || isAnalyzing"
          >
            <i v-if="isAnalyzing" class="fas fa-spinner fa-spin"></i>
            <i v-else class="fas fa-search"></i>
            {{ isAnalyzing ? "分析中..." : "分析代码" }}
          </button>
        </div>
      </div>

      <!-- ⭐ 新增：草稿提示 -->
      <div v-if="hasDraft" class="draft-notice">
        <i class="fas fa-save"></i>
        草稿已自动保存
        <span class="draft-info">{{ code.length }} 字符</span>
      </div>

      <!-- 代码输入框 -->
      <textarea
        ref="codeEditor"
        v-model="code"
        @keydown="handleKeyDown"
        class="code-editor"
        placeholder='请在此输入C语言代码...

示例：
#include <stdio.h>

int main() {
    printf("Hello, World!");
    return 0;
}'
        spellcheck="false"
      ></textarea>

      <!-- 编辑器底部信息 -->
      <div class="editor-footer">
        <span class="info-item">
          <i class="fas fa-file-code"></i>
          {{ code.split("\n").length }} 行
        </span>
        <span class="info-item">
          <i class="fas fa-keyboard"></i>
          {{ code.length }} 字符
        </span>
        <span class="info-item" title="按 Tab 插入 4 个空格">
          <i class="fas fa-info-circle"></i>
          支持 Tab 缩进
        </span>
      </div>
    </div>

    <!-- 右侧：分析结果 -->
    <div class="result-panel">
      <!-- 空状态 -->
      <div v-if="!analysisResult" class="empty-state">
        <div class="empty-icon">🔍</div>
        <h3>等待分析</h3>
        <p>在左侧输入代码后点击"分析代码"按钮</p>
      </div>

      <!-- 分析结果 -->
      <div v-else class="analysis-result">
        <!-- 评分卡片 -->
        <div class="score-card" :class="`level-${analysisResult.level || 'F'}`">
          <div class="score-value">{{ analysisResult.score || 0 }}</div>
          <div class="score-label">
            <span class="score-level">{{
              getLevelText(analysisResult.level)
            }}</span>
            <span class="score-desc">综合评分</span>
          </div>
        </div>

        <!-- 代码特征 -->
        <div class="section" v-if="analysisResult.features">
          <h4><i class="fas fa-info-circle"></i> 代码特征</h4>
          <div class="feature-grid">
            <div class="feature-item">
              <span class="feature-label">代码行数</span>
              <span class="feature-value">{{
                analysisResult.features.lines
              }}</span>
            </div>
            <div class="feature-item">
              <span class="feature-label">字符数</span>
              <span class="feature-value">{{
                analysisResult.features.chars
              }}</span>
            </div>
            <div class="feature-item">
              <span class="feature-label">复杂度</span>
              <span
                class="feature-value complexity"
                :class="analysisResult.features.complexity"
              >
                {{ getComplexityText(analysisResult.features.complexity) }}
              </span>
            </div>
            <div class="feature-item">
              <span class="feature-label">包含main函数</span>
              <span class="feature-value">
                {{ analysisResult.features.has_main ? "✅ 是" : "❌ 否" }}
              </span>
            </div>
          </div>

          <!-- 详细特征 -->
          <div class="feature-details">
            <div
              v-if="
                analysisResult.features.includes &&
                analysisResult.features.includes.length > 0
              "
            >
              <strong>头文件：</strong>
              <code>{{ analysisResult.features.includes.join(", ") }}</code>
            </div>
            <div
              v-if="
                analysisResult.features.functions &&
                analysisResult.features.functions.length > 0
              "
            >
              <strong>函数：</strong>
              <code>{{ analysisResult.features.functions.join(", ") }}</code>
            </div>
            <div v-if="analysisResult.features.keywords">
              <strong>控制结构：</strong>
              if({{ analysisResult.features.keywords.if }}) for({{
                analysisResult.features.keywords.for
              }}) while({{ analysisResult.features.keywords.while }}) switch({{
                analysisResult.features.keywords.switch
              }})
            </div>
          </div>
        </div>

        <!-- 语法检查结果 -->
        <div class="section" v-if="analysisResult.syntax_check">
          <h4>
            <i
              class="fas fa-check-circle"
              v-if="analysisResult.syntax_check.valid"
            ></i>
            <i class="fas fa-times-circle" v-else></i>
            语法检查
          </h4>
          <div v-if="analysisResult.syntax_check.valid" class="success-message">
            ✅ 语法正确，无错误
          </div>
          <div v-else class="error-list">
            <div
              v-for="(error, index) in analysisResult.syntax_check.errors"
              :key="index"
              class="error-item"
            >
              <strong>第 {{ error.line }} 行：</strong> {{ error.message }}
            </div>
          </div>
        </div>

        <!-- AI分析结果 -->
        <div
          class="section"
          v-if="
            analysisResult.ai_analysis && analysisResult.ai_analysis.success
          "
        >
          <h4><i class="fas fa-brain"></i> AI 深度分析</h4>

          <!-- 问题列表 -->
          <div
            v-if="
              analysisResult.ai_analysis.problems &&
              analysisResult.ai_analysis.problems.length > 0
            "
            class="problems-list"
          >
            <h5>🔴 发现的问题</h5>
            <div
              v-for="(problem, index) in analysisResult.ai_analysis.problems"
              :key="index"
              class="problem-item"
              :class="problem.severity"
            >
              <span class="problem-badge">{{
                problem.severity === "error" ? "严重" : "警告"
              }}</span>
              <span class="problem-text">{{ problem.description }}</span>
            </div>
          </div>

          <!-- 改进建议 -->
          <div
            v-if="
              analysisResult.ai_analysis.suggestions &&
              analysisResult.ai_analysis.suggestions.length > 0
            "
            class="suggestions-list"
          >
            <h5>💡 改进建议</h5>
            <ul>
              <li
                v-for="(suggestion, index) in analysisResult.ai_analysis
                  .suggestions"
                :key="index"
              >
                {{ suggestion }}
              </li>
            </ul>
          </div>

          <!-- 总结 -->
          <div v-if="analysisResult.ai_analysis.summary" class="summary">
            <h5>📋 总结</h5>
            <p>{{ analysisResult.ai_analysis.summary }}</p>
          </div>

          <!-- 使用的知识库 -->
          <div
            v-if="
              analysisResult.ai_analysis.knowledge_used &&
              analysisResult.ai_analysis.knowledge_used.length > 0
            "
            class="knowledge-sources"
          >
            <h5>📚 参考资料</h5>
            <div class="source-tags">
              <span
                v-for="(source, index) in analysisResult.ai_analysis
                  .knowledge_used"
                :key="index"
                class="source-tag"
              >
                {{ source }}
              </span>
            </div>
          </div>
        </div>

        <!-- 综合建议 -->
        <div
          class="section"
          v-if="
            analysisResult.suggestions && analysisResult.suggestions.length > 0
          "
        >
          <h4><i class="fas fa-lightbulb"></i> 综合建议</h4>
          <ul class="suggestions-list">
            <li
              v-for="(suggestion, index) in analysisResult.suggestions"
              :key="index"
            >
              {{ suggestion }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from "vue";
import { analyzeCode } from "../api/code";

// ========== 数据状态 ==========
const code = ref("");
const analysisResult = ref(null);
const isAnalyzing = ref(false);
const analysisType = ref("full");
const codeEditor = ref(null);

// ⭐ localStorage 键名
const CODE_DRAFT_KEY = "code_analyzer_draft";
const ANALYSIS_TYPE_KEY = "code_analysis_type";

// ⭐ 计算属性：是否有草稿
const hasDraft = computed(() => {
  return code.value.trim().length > 0;
});

// ⭐ 组件挂载时恢复草稿
onMounted(() => {
  // 恢复代码草稿
  const savedCode = localStorage.getItem(CODE_DRAFT_KEY);
  if (savedCode) {
    code.value = savedCode;
    console.log("✅ 恢复代码草稿:", savedCode.length, "字符");
  }

  // 恢复分析类型
  const savedType = localStorage.getItem(ANALYSIS_TYPE_KEY);
  if (savedType) {
    analysisType.value = savedType;
    console.log("✅ 恢复分析类型:", savedType);
  }
});

// ⭐ 监听代码变化，自动保存草稿（防抖优化）
let saveTimer = null;
watch(code, (newValue) => {
  if (saveTimer) {
    clearTimeout(saveTimer);
  }

  saveTimer = setTimeout(() => {
    if (newValue.trim()) {
      localStorage.setItem(CODE_DRAFT_KEY, newValue);
      console.log("💾 保存代码草稿:", newValue.length, "字符");
    } else {
      localStorage.removeItem(CODE_DRAFT_KEY);
      console.log("🗑️ 清除代码草稿");
    }
  }, 1000); // ⭐ 代码较长，延迟 1 秒保存
});

// ⭐ 监听分析类型变化，自动保存
watch(analysisType, (newValue) => {
  localStorage.setItem(ANALYSIS_TYPE_KEY, newValue);
  console.log("💾 保存分析类型:", newValue);
});

// ========== 方法 ==========

/**
 * 分析代码
 */
async function handleAnalyze() {
  if (!code.value.trim()) {
    alert("请先输入代码");
    return;
  }

  isAnalyzing.value = true;
  analysisResult.value = null;

  try {
    const result = await analyzeCode(code.value, analysisType.value);

    if (result.status === "success") {
      analysisResult.value = result.data;
      console.log("✅ 分析完成，评分:", result.data.score);
    } else {
      alert("分析失败: " + (result.message || "未知错误"));
    }
  } catch (error) {
    console.error("❌ 分析请求失败:", error);
    alert("分析失败: " + error.message);
  } finally {
    isAnalyzing.value = false;
  }
}

/**
 * ⭐ 修改：清空编辑器（同时清除草稿）
 */
function handleClear() {
  if (confirm("确定要清空代码吗？")) {
    code.value = "";
    analysisResult.value = null;

    // ⭐ 清除草稿
    localStorage.removeItem(CODE_DRAFT_KEY);
    console.log("🗑️ 清空代码和草稿");
  }
}

/**
 * 处理键盘事件（Tab、自动缩进、括号匹配）
 */
function handleKeyDown(event) {
  const textarea = event.target;

  // ========== 1. Tab 键插入空格 ==========
  if (event.key === "Tab") {
    event.preventDefault();

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;
    const spaces = "    ";

    code.value =
      code.value.substring(0, start) + spaces + code.value.substring(end);

    setTimeout(() => {
      textarea.selectionStart = textarea.selectionEnd = start + spaces.length;
    }, 0);
  }

  // ========== 2. Enter 键自动缩进 ==========
  else if (event.key === "Enter") {
    event.preventDefault();

    const start = textarea.selectionStart;
    const lines = code.value.substring(0, start).split("\n");
    const currentLine = lines[lines.length - 1];

    const indent = currentLine.match(/^\s*/)[0];
    const needExtraIndent = currentLine.trim().endsWith("{");
    const newIndent = needExtraIndent ? indent + "    " : indent;

    const newText = "\n" + newIndent;
    code.value =
      code.value.substring(0, start) + newText + code.value.substring(start);

    setTimeout(() => {
      textarea.selectionStart = textarea.selectionEnd = start + newText.length;
    }, 0);
  }

  // ========== 3. 括号自动匹配 ==========
  else if (["(", "{", "[", '"', "'"].includes(event.key)) {
    const pairs = {
      "(": ")",
      "{": "}",
      "[": "]",
      '"': '"',
      "'": "'",
    };

    const start = textarea.selectionStart;
    const end = textarea.selectionEnd;

    if (start !== end) {
      event.preventDefault();
      const selectedText = code.value.substring(start, end);
      const newText = event.key + selectedText + pairs[event.key];

      code.value =
        code.value.substring(0, start) + newText + code.value.substring(end);

      setTimeout(() => {
        textarea.selectionStart = start + 1;
        textarea.selectionEnd = start + 1 + selectedText.length;
      }, 0);
    } else {
      event.preventDefault();
      const newText = event.key + pairs[event.key];

      code.value =
        code.value.substring(0, start) + newText + code.value.substring(start);

      setTimeout(() => {
        textarea.selectionStart = textarea.selectionEnd = start + 1;
      }, 0);
    }
  }
}

/**
 * 获取等级文本
 */
function getLevelText(level) {
  const levelMap = {
    A: "优秀",
    B: "良好",
    C: "中等",
    D: "及格",
    F: "不及格",
  };
  return levelMap[level] || "未评级";
}

/**
 * 获取复杂度文本
 */
function getComplexityText(complexity) {
  const complexityMap = {
    low: "低",
    medium: "中",
    high: "高",
  };
  return complexityMap[complexity] || "未知";
}
</script>

<style scoped>
/* ========== 整体布局 ========== */
.code-analyzer {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  height: 100%;
  padding: 20px;
  background: #f0f2f5;
  overflow: hidden;
}

/* ========== 编辑器面板 ========== */
.editor-panel {
  display: flex;
  flex-direction: column;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.editor-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.editor-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.analysis-type-select {
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  font-size: 14px;
  cursor: pointer;
  outline: none;
}

.analysis-type-select option {
  color: #333;
}

.btn-clear,
.btn-analyze {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-clear {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.btn-clear:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.3);
}

.btn-analyze {
  background: white;
  color: #667eea;
}

.btn-analyze:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.btn-clear:disabled,
.btn-analyze:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ========== 代码编辑器 ========== */
.code-editor {
  flex: 1;
  padding: 20px;
  border: none;
  font-family: "Consolas", "Monaco", "Courier New", monospace; /* ⭐ 等宽字体 */
  font-size: 14px;
  line-height: 1.6;
  resize: none;
  outline: none;
  background: #f8f9fa;
  tab-size: 4; /* ⭐ Tab 显示为 4 个空格宽度 */
}

.code-editor::placeholder {
  color: #999;
  font-family:
    "Consolas", "Monaco", "Courier New", monospace; /* ⭐ placeholder 也用等宽字体 */
}

.editor-footer {
  display: flex;
  gap: 20px;
  padding: 12px 20px;
  background: #f8f9fa;
  border-top: 1px solid #e0e0e0;
  font-size: 13px;
  color: #666;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.info-item i {
  color: #667eea;
}

/* ========== 结果面板（保持原样）========== */
.result-panel {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
  padding: 20px;
}

/* 其他样式保持不变... */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
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

/* ========== 分析结果 ========== */
.analysis-result {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* 评分卡片 */
.score-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.score-card.level-A {
  background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.score-card.level-B {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.score-card.level-C {
  background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.score-card.level-D {
  background: linear-gradient(135deg, #fbc2eb 0%, #a6c1ee 100%);
}

.score-card.level-F {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.score-value {
  font-size: 48px;
  font-weight: 700;
}

.score-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.score-level {
  font-size: 24px;
  font-weight: 600;
}

.score-desc {
  font-size: 14px;
  opacity: 0.9;
}

/* 区块样式 */
.section {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #667eea;
}

.section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section h5 {
  margin: 12px 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #555;
}

/* 代码特征 */
.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.feature-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: white;
  border-radius: 6px;
}

.feature-label {
  font-size: 13px;
  color: #666;
}

.feature-value {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.feature-value.complexity {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.feature-value.complexity.low {
  background: #e8f5e9;
  color: #2e7d32;
}

.feature-value.complexity.medium {
  background: #fff3e0;
  color: #f57c00;
}

.feature-value.complexity.high {
  background: #ffebee;
  color: #c62828;
}

.feature-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  color: #555;
}

.feature-details code {
  padding: 2px 6px;
  background: white;
  border-radius: 4px;
  font-family: "Consolas", monospace;
  color: #e83e8c;
}

/* 成功消息 */
.success-message {
  padding: 12px;
  background: #e8f5e9;
  border-radius: 6px;
  color: #2e7d32;
  font-weight: 500;
}

/* 错误列表 */
.error-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.error-item {
  padding: 10px;
  background: #ffebee;
  border-radius: 6px;
  color: #c62828;
  font-size: 13px;
}

/* 问题列表 */
.problems-list {
  margin-bottom: 16px;
}

.problem-item {
  display: flex;
  gap: 10px;
  padding: 10px;
  margin-bottom: 8px;
  background: white;
  border-radius: 6px;
  border-left: 3px solid #ff9800;
}

.problem-item.error {
  border-left-color: #f44336;
}

.problem-badge {
  flex-shrink: 0;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  background: #ff9800;
  color: white;
}

.problem-item.error .problem-badge {
  background: #f44336;
}

.problem-text {
  flex: 1;
  font-size: 13px;
  color: #333;
}

/* 建议列表 */
.suggestions-list ul {
  margin: 0;
  padding-left: 20px;
}

.suggestions-list li {
  margin: 8px 0;
  font-size: 13px;
  color: #555;
  line-height: 1.6;
}

/* 总结 */
.summary p {
  margin: 0;
  font-size: 13px;
  color: #555;
  line-height: 1.6;
}

/* 知识来源 */
.knowledge-sources {
  margin-top: 16px;
}

.source-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.source-tag {
  padding: 4px 12px;
  background: white;
  border-radius: 16px;
  font-size: 12px;
  color: #667eea;
  border: 1px solid #667eea;
}

/* 滚动条 */
.result-panel::-webkit-scrollbar {
  width: 8px;
}

.result-panel::-webkit-scrollbar-track {
  background: transparent;
}

.result-panel::-webkit-scrollbar-thumb {
  background: #d0d0d0;
  border-radius: 4px;
}

.result-panel::-webkit-scrollbar-thumb:hover {
  background: #b0b0b0;
}

/* 响应式 */
@media (max-width: 1200px) {
  .code-analyzer {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr 1fr;
  }
}
</style>

/* ⭐ 新增：草稿提示样式 */ .draft-notice { display: flex; align-items: center;
gap: 10px; padding: 8px 16px; background: #e3f2fd; border-bottom: 1px solid
#90caf9; font-size: 12px; color: #1976d2; } .draft-notice i { color: #2196f3; }
.draft-info { margin-left: auto; padding: 2px 8px; background: rgba(33, 150,
243, 0.1); border-radius: 12px; font-size: 11px; }
