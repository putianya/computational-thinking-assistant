# -*- coding: utf-8 -*-
"""
Markdown 预处理工具

功能：
1. 解析杂乱 Markdown 文件中的章节结构
2. 重新排版每个章节内容，使其符合 split_by_headers() 期望的格式规范
3. 按章节分割成多个独立 .md 文件（每个文件对应一个 ## 标题）
4. 输出到 data/knowledge/ 目录（可直接被 import_knowledge.py 读取导入）

用法：
    python preprocess_md.py <input.md> [--output-dir <dir>] [--prefix <prefix>] [--overwrite]

作者: 计算思维助手团队
日期: 2026-03-06
"""
import re
import os
import sys
import math
import argparse
from pathlib import Path


# ========== 0. OCR 文本预处理（无 Markdown 标题 → 自动生成标题） ==========

def _collapse_cjk_spaces(text: str) -> str:
    """折叠 CJK 字符/数字之间的多余空格（OCR 常见问题）。"""
    text = re.sub(r' {2,}', ' ', text)
    for _ in range(5):
        prev = text
        text = re.sub(
            r'([\u4e00-\u9fff\uff00-\uffef]) ([\u4e00-\u9fff\uff00-\uffef\d])',
            r'\1\2', text,
        )
        text = re.sub(
            r'([\u4e00-\u9fff\uff00-\uffef\d]) ([\u4e00-\u9fff\uff00-\uffef])',
            r'\1\2', text,
        )
        if text == prev:
            break
    return text


def normalize_raw_text(raw_text: str) -> str:
    """
    将无 Markdown 标题的原始文本（OCR/PDF 导出）预处理为带标准 Markdown 标题的格式。

    规则（按优先级）：
    1. 代码块内容原样保留
    2. 已有 Markdown 标题（# 开头）直接保留
    3. 目录行（含 3+ 连续点号且末尾为页码）→ 整行跳过
    4. "第 N 章 标题" → "## 第N章 标题"
    5. "N.N.N 标题"   → "### N.N.N 标题"
    6. "N.N 标题"     → "### N.N 标题"
    7. 普通行：清理 OCR 多余空格
    """
    toc_re     = re.compile(r'[·\.]{3,}\s*\d+\s*$')
    chapter_re = re.compile(r'^[\s　]*(第)\s*(\d{1,2})\s*(章)\s+(.+?)\s*$')
    subsec_re  = re.compile(r'^[\s　]*(\d{1,2})\.(\d{1,2})\.(\d{1,2})\s+([^\d·\s].+?)\s*$')
    sec_re     = re.compile(r'^[\s　]*(\d{1,2})\.(\d{1,2})\s+([^\d·\s].+?)\s*$')

    lines = raw_text.splitlines()
    result = []
    in_code_block = False

    for line in lines:
        stripped = line.strip()

        if stripped.startswith('```'):
            in_code_block = not in_code_block
            result.append(line)
            continue
        if in_code_block:
            result.append(line)
            continue

        # 已有 Markdown 标题，保留原样
        if re.match(r'^#{1,6}\s', stripped):
            result.append(stripped)
            continue

        # 目录行：跳过
        if toc_re.search(stripped):
            continue

        # 第N章
        m = chapter_re.match(stripped)
        if m:
            num   = m.group(2)
            title = _collapse_cjk_spaces(m.group(4).strip())
            result.append(f'## 第{num}章 {title}')
            continue

        # N.N.N 节
        m = subsec_re.match(stripped)
        if m:
            sec_num = f'{m.group(1)}.{m.group(2)}.{m.group(3)}'
            title   = _collapse_cjk_spaces(m.group(4).strip())
            result.append(f'### {sec_num} {title}')
            continue

        # N.N 节
        m = sec_re.match(stripped)
        if m:
            sec_num = f'{m.group(1)}.{m.group(2)}'
            title   = _collapse_cjk_spaces(m.group(3).strip())
            result.append(f'### {sec_num} {title}')
            continue

        # 普通行：清理 OCR 多余空格
        result.append(_collapse_cjk_spaces(line))

    return '\n'.join(result)


# ========== 1. 解析章节结构 ==========

def parse_md_structure(raw_text: str) -> list:
    """
    解析原始 Markdown 文本，提取章节树结构。

    规则：
    - 识别 #、##、###、#### 标题行（兼容标题前有多余空格/BOM头/全角空格）
    - # 一级标题识别为文档标题，不作为独立分块
    - ## 二级标题识别为顶层章节（每个章节将输出为一个独立文件）
    - ### 三级标题识别为章节内的小节
    - #### 及更深的标题识别为子段落，保留在所属小节内
    - 文档开头在第一个 ## 之前的内容作为「前言」章节处理

    Args:
        raw_text: 原始 Markdown 文本字符串

    Returns:
        list[dict]: 章节列表，每项结构为：
            {
                'chapter_title': str,
                'chapter_index': int,
                'sections': [
                    {
                        'section_title': str,  # ### 后的文本，若无则为 ''
                        'level': int,          # 2 或 3
                        'content_lines': list[str],
                    },
                    ...
                ]
            }
    """
    # 去除 BOM 头
    raw_text = raw_text.lstrip('\ufeff')

    lines = raw_text.splitlines()

    # 匹配标题行：兼容前导空格、全角空格、BOM
    # 全角空格 U+3000
    header_re = re.compile(r'^[\s\u3000]*(#{1,6})\s+(.*?)\s*$')

    chapters = []
    chapter_index = 0

    # 当前正在构建的章节和小节
    current_chapter = None
    current_section = None  # {'section_title': str, 'level': int, 'content_lines': list}

    def _flush_section():
        """将当前小节添加到当前章节中。"""
        if current_chapter is not None and current_section is not None:
            current_chapter['sections'].append(current_section)

    def _new_chapter(title: str) -> dict:
        """创建新章节结构。"""
        nonlocal chapter_index
        chapter_index += 1
        return {
            'chapter_title': title,
            'chapter_index': chapter_index,
            'sections': [],
        }

    def _new_section(title: str, level: int) -> dict:
        """创建新小节结构。"""
        return {
            'section_title': title,
            'level': level,
            'content_lines': [],
        }

    # 处理文档开头（第一个 ## 之前的内容）
    # 先扫描一遍，找到第一个 ## 的位置
    first_chapter_line = None
    for idx, line in enumerate(lines):
        m = header_re.match(line)
        if m and len(m.group(1)) == 2:
            first_chapter_line = idx
            break

    # 如果第一个 ## 之前有内容，创建「前言」章节
    preface_lines = []
    if first_chapter_line is None:
        # 没有 ## 标题，整个文档作为前言
        preface_lines = lines
    else:
        preface_lines = lines[:first_chapter_line]

    # 过滤：前言行去除一级标题行，只保留正文和小节
    preface_content_lines = []
    for line in preface_lines:
        m = header_re.match(line)
        if m:
            level = len(m.group(1))
            if level == 1:
                # 一级标题作为文档标题，跳过
                continue
            else:
                preface_content_lines.append(line)
        else:
            preface_content_lines.append(line)

    if any(l.strip() for l in preface_content_lines):
        # 前言有实质内容，创建前言章节
        chapter_index += 1
        preface_chapter = {
            'chapter_title': '前言',
            'chapter_index': chapter_index,
            'sections': [],
        }
        preface_section = _new_section('', 2)
        for line in preface_content_lines:
            m = header_re.match(line)
            if m:
                level = len(m.group(1))
                title_text = m.group(2).strip()
                if level == 3:
                    # 有 ### 小节，先保存当前 section
                    if preface_section['content_lines'] or preface_section['section_title']:
                        preface_chapter['sections'].append(preface_section)
                    preface_section = _new_section(title_text, 3)
                else:
                    # #### 及更深，当作普通正文行加入当前小节
                    preface_section['content_lines'].append(line)
            else:
                preface_section['content_lines'].append(line)
        if preface_section['content_lines'] or preface_section['section_title']:
            preface_chapter['sections'].append(preface_section)
        if preface_chapter['sections']:
            chapters.append(preface_chapter)

    if first_chapter_line is None:
        # 没有 ## 标题，直接返回前言
        return chapters

    # 逐行处理剩余内容
    current_chapter = None
    current_section = None

    for line in lines[first_chapter_line:]:
        m = header_re.match(line)
        if m:
            level = len(m.group(1))
            title_text = m.group(2).strip()

            if level == 1:
                # 一级标题：文档标题，忽略
                continue
            elif level == 2:
                # ## 新章节开始
                # 先保存当前小节和章节
                _flush_section()
                if current_chapter is not None:
                    chapters.append(current_chapter)

                current_chapter = _new_chapter(title_text)
                # 为本章节创建默认小节（level=2，section_title=''）
                current_section = _new_section('', 2)
            elif level == 3:
                # ### 新小节
                _flush_section()
                if current_chapter is None:
                    # 没有上级 ## 章节，创建一个匿名章节
                    current_chapter = _new_chapter('未分类')
                current_section = _new_section(title_text, 3)
            else:
                # #### 及更深：作为普通正文行，保留原始标题语法
                if current_section is None:
                    if current_chapter is None:
                        current_chapter = _new_chapter('未分类')
                    current_section = _new_section('', 2)
                current_section['content_lines'].append(line)
        else:
            # 普通行
            if current_section is None:
                if current_chapter is None:
                    # 出现在任何 ## 之前但 first_chapter_line 之后（不应发生）
                    current_chapter = _new_chapter('未分类')
                current_section = _new_section('', 2)
            current_section['content_lines'].append(line)

    # 保存最后的小节和章节
    _flush_section()
    if current_chapter is not None:
        chapters.append(current_chapter)

    return chapters


# ========== 2. 小节内容重新排版 ==========

def reformat_section(section: dict) -> str:
    """
    对单个小节内容重新排版。

    规则：
    - 去除多余连续空行（超过 2 个连续空行压缩为 1 个）
    - 去除行首/行尾多余空格（代码块内容除外）
    - 代码块（```...```）原样保留，不做任何处理
    - 表格行原样保留
    - 列表项（-、*、1.）统一缩进为 2 空格（保持相对层级）
    - 段落之间有且仅有一个空行
    - 小节标题行（###）保留在内容的开头

    Args:
        section: 小节字典，含 'section_title'、'level'、'content_lines' 字段

    Returns:
        str: 重新排版后的小节完整字符串
    """
    lines = section.get('content_lines', [])
    section_title = section.get('section_title', '')
    level = section.get('level', 2)

    result_lines = []

    # 小节标题行
    if section_title and level == 3:
        result_lines.append(f'### {section_title}')

    # 处理正文行（代码块内保持原样）
    in_code_block = False
    processed = []

    for line in lines:
        # 检测代码块边界（``` 开头）
        stripped = line.strip()
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            processed.append(line)  # 代码块标记行原样保留
            continue

        if in_code_block:
            # 代码块内原样保留
            processed.append(line)
            continue

        # 表格行原样保留（以 | 开头或是分隔行）
        if stripped.startswith('|') or re.match(r'^\|?[\s\-:|]+\|', stripped):
            processed.append(line)
            continue

        # 列表项统一缩进为 2 空格（保持相对层级）
        list_match = re.match(r'^(\s*)([-*]|\d+\.)\s+(.*)', line)
        if list_match:
            indent_str = list_match.group(1)
            marker = list_match.group(2)
            content = list_match.group(3)
            # 每 2 个空格或 1 个 tab 算一级缩进
            indent_level = len(indent_str.expandtabs(2)) // 2
            new_indent = '  ' * indent_level
            processed.append(f'{new_indent}{marker} {content}')
            continue

        # 普通行：去除行首/行尾多余空格
        processed.append(stripped)

    # 若代码块未关闭（异常情况），强制关闭
    if in_code_block:
        processed.append('```')

    # 压缩连续空行（超过 2 个连续空行压缩为 1 个）
    compressed = []
    blank_count = 0
    for line in processed:
        if line.strip() == '':
            blank_count += 1
            if blank_count <= 1:
                compressed.append('')
        else:
            blank_count = 0
            compressed.append(line)

    # 去除开头和结尾的空行
    while compressed and compressed[0] == '':
        compressed.pop(0)
    while compressed and compressed[-1] == '':
        compressed.pop()

    result_lines.extend(compressed)

    return '\n'.join(result_lines)


# ========== 3. 章节合并为 MD 字符串 ==========

def format_chapter_as_md(chapter: dict, source_filename: str) -> str:
    """
    将一个章节的所有小节合并为一个完整的 Markdown 字符串。

    格式：
    - 文件头部写入 ## {chapter_title} 作为顶层章节标题
    - 依次追加各小节（### 小节标题 + 正文）
    - 章节与章节之间保留一个空行
    - 文件末尾加一个换行

    满足 split_by_headers() 的要求：
    - 必须有 ## 或 ### 标题
    - 每块去除代码后正文至少 20 字符
    - 单个标题到下个标题之间内容不超过 1000 字符

    Args:
        chapter: 章节字典，含 'chapter_title'、'chapter_index'、'sections' 字段
        source_filename: 原始文件名（用于注释/溯源）

    Returns:
        str: 该章节对应的完整 Markdown 文件内容
    """
    parts = []

    # 章节标题（##）
    parts.append(f"## {chapter['chapter_title']}")

    for section in chapter.get('sections', []):
        formatted = reformat_section(section)
        if formatted.strip():
            parts.append('')  # 空行分隔
            parts.append(formatted)

    # 确保文件末尾有换行
    content = '\n'.join(parts) + '\n'
    return content


# ========== 4. 文件名安全化 ==========

def sanitize_filename(title: str, index: int = 0) -> str:
    """
    将章节标题转换为合法的文件名。

    规则：
    - 去除或替换不能用于文件名的字符：/ \\ : * ? " < > |
    - 将空格替换为 _
    - 长度限制 50 个字符
    - 若结果为空，返回 chapter_{index}

    Args:
        title: 章节标题字符串
        index: 章节序号（结果为空时作为后备文件名）

    Returns:
        str: 合法的文件名（不含扩展名）
    """
    # 替换非法字符
    illegal_chars = r'[/\\:*?"<>|]'
    safe = re.sub(illegal_chars, '', title)

    # 将空格替换为下划线
    safe = safe.replace(' ', '_')

    # 去除连续下划线
    safe = re.sub(r'_+', '_', safe)

    # 去除首尾下划线
    safe = safe.strip('_')

    # 长度限制 50
    safe = safe[:50]

    if not safe:
        safe = f'chapter_{index}'

    return safe


# ========== 5. 主函数：读取原始 MD，按章节输出多个文件 ==========

def split_md_to_files(
    input_path: str,
    output_dir: str,
    prefix: str = '',
    overwrite: bool = False,
) -> list:
    """
    主函数：读取一个杂乱的原始 Markdown 文件，输出多个按章节分割的标准 Markdown 文件。

    流程：
    1. 读取 input_path 文件（utf-8 编码，出错时尝试 gbk）
    2. 调用 parse_md_structure() 解析章节结构
    3. 对每个章节调用 format_chapter_as_md() 生成内容
    4. 文件名格式：{prefix}{chapter_index:02d}_{sanitize_filename(chapter_title)}.md
    5. 如果 output_dir 不存在则自动创建
    6. 同名文件已存在时询问用户或根据 overwrite 参数决定是否覆盖

    Args:
        input_path: 原始 Markdown 文件路径
        output_dir: 输出目录路径
        prefix: 文件名前缀（默认为空）
        overwrite: 若为 True，同名文件直接覆盖；否则询问用户

    Returns:
        list[str]: 已输出的文件路径列表
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    # 读取文件（优先 utf-8，失败则尝试 gbk）
    raw_text = None
    for encoding in ('utf-8', 'gbk'):
        try:
            with open(input_path, 'r', encoding=encoding) as f:
                raw_text = f.read()
            break
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            print(f"❌ 文件不存在: {input_path}")
            return []

    if raw_text is None:
        print(f"❌ 无法读取文件（尝试 utf-8 和 gbk 均失败）: {input_path}")
        return []

    # 预处理：识别中文章节结构、清理 OCR 多余空格
    raw_text = normalize_raw_text(raw_text)

    # 解析章节结构
    chapters = parse_md_structure(raw_text)

    if not chapters:
        print(f"⚠️  未解析到任何章节: {input_path.name}")
        return []

    print(f"✅ 解析到 {len(chapters)} 个章节")

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    source_filename = input_path.name
    output_files = []

    for chapter in chapters:
        chapter_index = chapter['chapter_index']
        chapter_title = chapter['chapter_title']
        safe_name = sanitize_filename(chapter_title, chapter_index)
        filename = f"{prefix}{chapter_index:02d}_{safe_name}.md"
        output_path = output_dir / filename

        # 检查是否覆盖
        if output_path.exists() and not overwrite:
            answer = input(f"⚠️  文件已存在: {filename}，是否覆盖？[y/N] ").strip().lower()
            if answer != 'y':
                print(f"   ⏭️  跳过: {filename}")
                continue

        # 生成章节内容
        content = format_chapter_as_md(chapter, source_filename)

        # 预估分块数量（总字符数 / 800，向上取整）
        estimated_chunks = max(1, math.ceil(len(content) / 800))

        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"   {filename}  (预估 {estimated_chunks} 个知识块)")
        output_files.append(str(output_path))

    return output_files


# ========== 6. 命令行入口 ==========

def main():
    """
    命令行入口，支持：
        python preprocess_md.py <input.md> [--output-dir <dir>] [--prefix <prefix>] [--overwrite]
    """
    parser = argparse.ArgumentParser(
        description='Markdown 预处理工具：将杂乱 MD 文件按章节分割为标准格式，供 import_knowledge.py 导入使用',
    )
    parser.add_argument('input', help='原始 Markdown 文件路径')
    parser.add_argument(
        '--output-dir',
        default=None,
        help='输出目录（默认为脚本所在目录的 ../data/knowledge/）',
    )
    parser.add_argument('--prefix', default='', help='输出文件名前缀（默认为空）')
    parser.add_argument(
        '--overwrite',
        action='store_true',
        help='若输出文件已存在则直接覆盖，不询问',
    )
    args = parser.parse_args()

    # 确定输出目录
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        # 默认：脚本所在目录的 ../data/knowledge/
        script_dir = Path(__file__).parent
        output_dir = script_dir / '..' / 'data' / 'knowledge'
        output_dir = output_dir.resolve()

    input_path = Path(args.input).resolve()

    print('=' * 40)
    print(f'📄 输入文件: {input_path}')
    print(f'📂 输出目录: {output_dir}')
    print('=' * 40)

    output_files = split_md_to_files(
        input_path=str(input_path),
        output_dir=str(output_dir),
        prefix=args.prefix,
        overwrite=args.overwrite,
    )

    print('=' * 40)
    print(f'✅ 输出文件:')
    for f in output_files:
        print(f'   {Path(f).name}')

    print('=' * 40)
    print(f'🎉 处理完成！共输出 {len(output_files)} 个文件')
    print('   可直接运行 import_knowledge.py 导入知识库')
    print('=' * 40)


if __name__ == '__main__':
    main()
