# Markdown 预处理工具使用说明

## 简介

本目录包含两个 Markdown 预处理脚本，用于在将原始知识素材导入知识库之前，将格式混乱的 Markdown 文件整理为 `import_knowledge.py` 可以高质量解析的标准格式。

| 脚本 | 用途 |
|------|------|
| `preprocess_md.py` | 处理单个 Markdown 文件 |
| `batch_preprocess_md.py` | 批量处理整个目录下的 Markdown 文件 |

---

## 工作流程

```
原始 Markdown 素材
       │
       ▼
┌──────────────────────────────────────────┐
│  preprocess_md.py / batch_preprocess_md.py│
│                                          │
│  1. 解析章节结构 (parse_md_structure)     │
│  2. 重新排版内容 (reformat_section)       │
│  3. 生成标准 MD  (format_chapter_as_md)  │
│  4. 按章节分文件输出到 data/knowledge/    │
└──────────────────────────────────────────┘
       │
       ▼
data/knowledge/
  ├── 01_章节A.md
  ├── 02_章节B.md
  └── ...
       │
       ▼
┌──────────────────────────────────────────┐
│         import_knowledge.py              │
│                                          │
│  1. load_markdown_files()                │
│  2. split_by_headers()                   │
│  3. 写入 ChromaDB 向量数据库             │
│  4. 写入 SQLite KnowledgeChunk 数据表    │
└──────────────────────────────────────────┘
       │
       ▼
  知识库就绪，可供 RAG 检索使用
```

---

## 安装依赖

本工具仅依赖 Python 标准库（`re`、`pathlib`、`argparse`、`math`），无需额外安装任何包。

---

## 使用示例

### 单文件处理

```bash
# 基本用法（输出到默认目录 ../data/knowledge/）
python preprocess_md.py 原始素材.md

# 指定输出目录
python preprocess_md.py 原始素材.md --output-dir /path/to/knowledge/

# 添加文件名前缀（方便区分来源）
python preprocess_md.py 原始素材.md --prefix "cpp_"

# 强制覆盖已有文件，不询问
python preprocess_md.py 原始素材.md --overwrite
```

**输出示例：**

```
========================================
📄 输入文件: /path/to/原始素材.md
📂 输出目录: /path/to/data/knowledge/
========================================
✅ 解析到 5 个章节
   01_前言.md  (预估 1 个知识块)
   02_什么是指针.md  (预估 3 个知识块)
   03_指针运算.md  (预估 2 个知识块)
   04_指针与数组.md  (预估 4 个知识块)
   05_常见错误.md  (预估 2 个知识块)
========================================
✅ 输出文件:
   01_前言.md
   02_什么是指针.md
   ...
========================================
🎉 处理完成！共输出 5 个文件
   可直接运行 import_knowledge.py 导入知识库
========================================
```

### 批量处理

```bash
# 批量处理整个目录（输出到默认目录）
python batch_preprocess_md.py /path/to/raw_materials/

# 以原文件名作为前缀，避免章节名冲突
python batch_preprocess_md.py /path/to/raw_materials/ --prefix-by-file

# 指定输出目录 + 强制覆盖
python batch_preprocess_md.py /path/to/raw_materials/ --output-dir /path/to/knowledge/ --overwrite
```

**输出示例：**

```
========================================
📂 批量处理目录: /path/to/raw_materials/
📂 输出目录: /path/to/data/knowledge/
========================================

📄 [1/3] 处理: 文件A.md
✅ 解析到 4 个章节
   文件A_01_章节一.md  (预估 2 个知识块)
   ...
   -> 输出 4 个文件

📄 [2/3] 处理: 文件B.md
   ...
   -> 输出 3 个文件

📄 [3/3] 处理: 文件C.md
   ...
   -> 输出 5 个文件

========================================
🎉 批量处理完成！共处理 3 个文件，输出 12 个知识库文件
========================================
```

### 完整工作流（预处理 + 导入）

```bash
# 步骤 1：预处理原始素材
python scripts/preprocess_md.py raw/my_notes.md --overwrite

# 步骤 2：导入知识库
python scripts/import_knowledge.py
```

---

## 输入文件格式要求

### 支持的标题格式

| 格式 | 说明 |
|------|------|
| `# 文档标题` | 一级标题，识别为文档标题，不输出到分块 |
| `## 章节名` | 二级标题，每个对应一个独立输出文件 |
| `### 小节名` | 三级标题，在文件内作为子标题 |
| `#### 子段落` | 四级及更深标题，作为普通正文行处理 |

### 兼容的"杂乱"情况

- 标题行前有多余空格（`   ## 标题`）
- 标题行前有全角空格（`　## 标题`）
- 文件头部有 UTF-8 BOM（`\ufeff`）
- 连续多个空行
- 列表缩进不统一

### 不支持的情况

- 使用 `===` 或 `---` 下划线式标题（Setext 格式）
- 完全没有任何 `##` 标题的文档（会作为一个「前言」章节整体处理）

---

## 输出文件命名规则

文件名格式：`{prefix}{chapter_index:02d}_{safe_title}.md`

| 部分 | 说明 |
|------|------|
| `{prefix}` | 可选前缀，通过 `--prefix` 指定 |
| `{chapter_index:02d}` | 章节序号，两位数字（01、02、...） |
| `{safe_title}` | 章节标题转义后的文件名（去除非法字符，空格替换为 `_`，最长 50 字符） |

**示例：**

| 章节标题 | 生成文件名 |
|----------|------------|
| `什么是指针` | `01_什么是指针.md` |
| `指针 & 引用` | `02_指针__引用.md` |
| `C++/内存管理` | `03_C内存管理.md` |
| （空标题） | `04_chapter_4.md` |

---

## 常见错误排查

### 问题：输出文件中没有 `##` 标题，`import_knowledge.py` 跳过了所有块

**原因：** `split_by_headers()` 的正则为 `r'^(###+)\s+(.+)$'`，不识别一级标题 `#`。

**解决：** 确保输出文件中第一行是 `## 章节名`。`preprocess_md.py` 已自动处理，但如果手动编辑输出文件时不要将 `##` 改成 `#`。

---

### 问题：知识块内容少于 20 字符，被 `split_by_headers()` 过滤

**原因：** 某个小节内容太短（可能是空节或只有几个字）。

**解决：** 在原始文件中补充相关内容，或删除该空节。

---

### 问题：文件读取失败，提示编码错误

**原因：** 文件编码不是 UTF-8 也不是 GBK。

**解决：** 用文本编辑器将文件另存为 UTF-8 编码后重新处理。

---

### 问题：`batch_preprocess_md.py` 找不到 `preprocess_md` 模块

**原因：** 两个脚本必须放在同一目录下。

**解决：** 确认 `batch_preprocess_md.py` 和 `preprocess_md.py` 在同一目录（`backend/scripts/`）。

---

### 问题：中文文件名在 Windows 系统上显示乱码

**解决：** 所有输出文件均使用 UTF-8 编码，Windows 终端可通过 `chcp 65001` 切换到 UTF-8 代码页。

---

## API 参考

### `preprocess_md.py` 公开函数

| 函数 | 说明 |
|------|------|
| `parse_md_structure(raw_text)` | 解析原始 MD 文本，返回章节树列表 |
| `reformat_section(section)` | 对单个小节内容重新排版，返回字符串 |
| `format_chapter_as_md(chapter, source_filename)` | 将章节合并为完整 MD 字符串 |
| `sanitize_filename(title, index)` | 将标题转换为合法文件名 |
| `split_md_to_files(input_path, output_dir, prefix, overwrite)` | 主函数：读取并分割输出 |

也可在其他 Python 脚本中导入使用：

```python
from scripts.preprocess_md import split_md_to_files

output_files = split_md_to_files(
    input_path='raw/my_notes.md',
    output_dir='backend/data/knowledge/',
    prefix='notes_',
    overwrite=True,
)
print(f"输出了 {len(output_files)} 个文件")
```
