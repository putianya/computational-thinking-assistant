# -*- coding: utf-8 -*-
"""
知识库导入脚本

功能：
1. 读取 data/knowledge/ 目录下的 Markdown 文件
2. 按标题分块（每块约 200-500 字）
3. 导入到 ChromaDB 向量数据库
4. 同步到 KnowledgeChunk 数据表

作者: 计算思维助手团队
日期: 2026-01-26
"""
import sys
import os
import re
import jieba  # ⭐ 添加 jieba 导入
import argparse
from pathlib import Path
from datetime import datetime
import traceback
import hashlib

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from database import db
from models.knowledge_chunk import KnowledgeChunk
from services.vector_service import get_vector_service


# ========== 步骤 1：读取文件 ==========

def load_markdown_files(directory):
    """
    读取目录下所有 Markdown 文件
    
    Args:
        directory: 文件夹路径
        
    Returns:
        list: [(文件路径, 文件内容), ...]
    """
    directory_path = Path(directory)
    
    # 检查目录是否存在
    if not directory_path.exists():
        print(f"❌ 目录不存在: {directory}")
        return []
    
    markdown_files = []
    
    # 遍历目录，查找所有 .md 文件
    for file_path in directory_path.glob('*.md'):
        try:
            # 读取文件内容（使用 utf-8 编码）
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            markdown_files.append((file_path, content))
            print(f"✅ 读取文件: {file_path.name} ({len(content)} 字符)")
            
        except Exception as e:
            print(f"❌ 读取失败 {file_path.name}: {e}")
    
    return markdown_files


# ========== 步骤 2：分块 ==========

def split_by_headers(markdown_text, source_file, max_length=1000):
    """
    按 Markdown 标题分块
    
    规则:
        - 按 ## 或 ### 标题分块
        - 保留标题层级关系
        - 过滤空块和纯代码块
        - ⭐ 如果某块超过 max_length，进行二次分割
    
    Args:
        markdown_text: Markdown 文本
        source_file: 源文件名
        max_length: 单块最大字符数（默认 1000）
        
    Returns:
        list: [
            {
                'content': '## 什么是指针\n指针是...',
                'source': 'test_pointer.md',
                'chapter': '什么是指针',
                'section': None,
                'level': 2
            },
            ...
        ]
    """
    chunks = []
    
    # 正则表达式：匹配 Markdown 标题（## 或 ###）
    header_pattern = re.compile(r'^(###+)\s+(.+)$', re.MULTILINE)
    
    # 查找所有标题
    matches = list(header_pattern.finditer(markdown_text))
    
    print(f"\n   找到 {len(matches)} 个标题:")
    for i, match in enumerate(matches, 1):
        level = len(match.group(1))
        title = match.group(2).strip()
        print(f"      {i}. {'#' * level} {title} (位置: {match.start()})")
    
    if not matches:
        print(f"   ⚠️  未找到标题，尝试手动分割")
        
        # ⭐⭐⭐ 如果正则失败，尝试手动分割 ⭐⭐⭐
        manual_chunks = manual_split_by_lines(markdown_text, source_file)
        if manual_chunks:
            print(f"   ✅ 手动分割成功: {len(manual_chunks)} 个块")
            return manual_chunks
        
        # 最后手段：整个文档作为一块
        if markdown_text.strip():
            sub_chunks = split_long_chunk(
                markdown_text.strip(), 
                source_file.replace('.md', ''),
                '',
                1,
                max_length
            )
            chunks.extend(sub_chunks)
        return chunks
    
    # 遍历每个标题，提取对应的内容块
    for i, match in enumerate(matches):
        level = len(match.group(1))
        title = match.group(2).strip()
        start_pos = match.start()
        
        # 内容结束位置
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(markdown_text)
        
        # 提取完整内容
        content = markdown_text[start_pos:end_pos].strip()
        
        if not content:
            continue
        
        # 过滤纯代码块
        code_block_pattern = re.compile(r'```[\s\S]+?```')
        content_without_code = code_block_pattern.sub('', content)
        
        if len(content_without_code.strip()) < 20:
            continue
        
        # 判断层级关系
        if level == 2:
            chapter = title
            section = ''
        elif level == 3:
            chapter = None
            for prev_match in reversed(matches[:i]):
                if len(prev_match.group(1)) == 2:
                    chapter = prev_match.group(2).strip()
                    break
            
            if not chapter:
                chapter = source_file.replace('.md', '')
            
            section = title
        else:
            chapter = source_file.replace('.md', '')
            section = title
        
        # 检查块长度
        if len(content) > max_length:
            print(f"⚠️  块过长 ({len(content)} 字符)，进行分割: {chapter} - {section}")
            sub_chunks = split_long_chunk(
                content, 
                chapter, 
                section or '',
                level, 
                max_length
            )
            chunks.extend(sub_chunks)
        else:
            chunks.append({
                'content': content,
                'source': source_file,
                'chapter': chapter,
                'section': section or '',
                'level': level
            })
    
    return chunks

def manual_split_by_lines(markdown_text, source_file):
    """
    ⭐⭐⭐ 新增：手动按行分割（正则失败时的后备方案）⭐⭐⭐
    """
    chunks = []
    lines = markdown_text.split('\n')
    
    current_chapter = None
    current_section = None
    current_content = []
    current_level = 2
    
    for line in lines:
        stripped = line.strip()
        
        # 检测标题（宽松匹配）
        if stripped.startswith('##') and not stripped.startswith('###'):
            # 保存之前的内容
            if current_content:
                content = '\n'.join(current_content).strip()
                if content:
                    chunks.append({
                        'content': content,
                        'source': source_file,
                        'chapter': current_chapter or source_file.replace('.md', ''),
                        'section': current_section or '',
                        'level': current_level
                    })
                current_content = []
            
            # 提取新标题
            title = stripped.lstrip('#').strip()
            current_chapter = title
            current_section = ''
            current_level = 2
            current_content.append(line)
        
        elif stripped.startswith('###'):
            # 三级标题
            if current_content:
                content = '\n'.join(current_content).strip()
                if content:
                    chunks.append({
                        'content': content,
                        'source': source_file,
                        'chapter': current_chapter or source_file.replace('.md', ''),
                        'section': current_section or '',
                        'level': current_level
                    })
                current_content = []
            
            title = stripped.lstrip('#').strip()
            current_section = title
            current_level = 3
            current_content.append(line)
        
        else:
            current_content.append(line)
    
    # 保存最后一块
    if current_content:
        content = '\n'.join(current_content).strip()
        if content:
            chunks.append({
                'content': content,
                'source': source_file,
                'chapter': current_chapter or source_file.replace('.md', ''),
                'section': current_section or '',
                'level': current_level
            })
    
    return chunks


# # ⭐⭐⭐ 新增：长块分割函数 ⭐⭐⭐
# def split_long_chunk(content, chapter, section, level, max_length=1000):
#     """
#     分割超长的知识块
    
#     策略：
#     1. 按空行（\\n\\n）分割段落
#     2. 合并段落直到接近 max_length
#     3. 如果单个段落超长，按句号分割
    
#     Args:
#         content: 原始内容
#         chapter: 章节名
#         section: 小节名
#         level: 标题级别
#         max_length: 最大长度
        
#     Returns:
#         list: 分割后的块列表
#     """
#     # 1. 按空行分割段落
#     paragraphs = re.split(r'\n\s*\n', content)
    
#     sub_chunks = []
#     current_chunk = ""
    
#     for para in paragraphs:
#         para = para.strip()
#         if not para:
#             continue
        
#         # 2. 尝试合并段落
#         if len(current_chunk) + len(para) + 2 <= max_length:
#             # 可以合并
#             if current_chunk:
#                 current_chunk += "\n\n" + para
#             else:
#                 current_chunk = para
#         else:
#             # 无法合并
#             if current_chunk:
#                 # 保存当前块
#                 sub_chunks.append({
#                     'content': current_chunk,
#                     'source': f"{chapter}.md" if chapter else "unknown.md",
#                     'chapter': chapter,
#                     'section': section,
#                     'level': level
#                 })
            
#             # 3. 检查单个段落是否超长
#             if len(para) > max_length:
#                 # 按句号分割
#                 sentences = re.split(r'([。.!?！？])', para)
                
#                 temp_chunk = ""
#                 for i in range(0, len(sentences), 2):
#                     sentence = sentences[i]
#                     punct = sentences[i + 1] if i + 1 < len(sentences) else ""
                    
#                     full_sentence = sentence + punct
                    
#                     if len(temp_chunk) + len(full_sentence) <= max_length:
#                         temp_chunk += full_sentence
#                     else:
#                         if temp_chunk:
#                             sub_chunks.append({
#                                 'content': temp_chunk,
#                                 'source': f"{chapter}.md" if chapter else "unknown.md",
#                                 'chapter': chapter,
#                                 'section': section,
#                                 'level': level
#                             })
#                         temp_chunk = full_sentence
                
#                 current_chunk = temp_chunk
#             else:
#                 current_chunk = para
    
#     # 4. 保存最后一个块
#     if current_chunk:
#         sub_chunks.append({
#             'content': current_chunk,
#             'source': f"{chapter}.md" if chapter else "unknown.md",
#             'chapter': chapter,
#             'section': section,
#             'level': level
#         })
    
#     print(f"   ✂️  分割成 {len(sub_chunks)} 个子块")
#     return sub_chunks

def split_long_chunk(content, chapter, section, level, max_length=1000):
    """分割超长文本块"""
    chunks = []
    
    # ⭐⭐⭐ 修复：确保参数不为 None ⭐⭐⭐
    chapter = chapter or '未分类'
    section = section or ''
    
    # 按段落分割
    paragraphs = content.split('\n\n')
    
    current_chunk = ''
    chunk_index = 1
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # 如果加上这段会超长
        if len(current_chunk) + len(para) + 2 > max_length:
            # 保存当前块
            if current_chunk:
                chunks.append({
                    'content': current_chunk.strip(),
                    'source': 'split_chunk',
                    'chapter': chapter,
                    'section': f"{section} (第{chunk_index}部分)" if section else f"第{chunk_index}部分",
                    'level': level
                })
                chunk_index += 1
                current_chunk = ''
        
        # 添加段落
        if current_chunk:
            current_chunk += '\n\n'
        current_chunk += para
    
    # 保存最后一个块
    if current_chunk:
        chunks.append({
            'content': current_chunk.strip(),
            'source': 'split_chunk',
            'chapter': chapter,
            'section': f"{section} (第{chunk_index}部分)" if section else f"第{chunk_index}部分",
            'level': level
        })
    
    return chunks


# ========== 步骤 3：导入到向量数据库 ==========

def import_to_vector_db(chunks):
    """
    导入知识块到 ChromaDB
    
    ⭐⭐⭐ 新流程：使用已有的 chunk_id 添加到向量 metadata ⭐⭐⭐
    
    Args:
        chunks: 知识块列表（必须已包含 chunk_id）
        
    Returns:
        dict: 导入结果
    """
    if not chunks:
        return {
            'success': False,
            'message': '知识块列表为空',
            'added_count': 0 
        }
    
    print("\n" + "=" * 60)
    print("🧠 生成向量并关联 chunk_id")
    print("=" * 60)
    
    # 获取向量服务
    vector_service = get_vector_service()
    
    # 构建文档格式
    documents = []
    for i, chunk in enumerate(chunks):
        doc = {
            'content': chunk['content'],
            'source': chunk.get('source', 'unknown'),
            'chapter': chunk.get('chapter', '未分类'),
            'section': chunk.get('section') or '',
            'level': chunk.get('level', 2),
            'chunk_id': chunk.get('chunk_id')  # ⭐⭐⭐ 传入 chunk_id ⭐⭐⭐
        }
        
        documents.append(doc)
        
        # 打印前几条的 chunk_id
        if i < 3:
            print(f"   [{i+1}] chunk_id={chunk.get('chunk_id')}, chapter={chunk.get('chapter', '')[:30]}")
    
    # 调用向量服务的 add_documents 方法
    result = vector_service.add_documents(documents)
    
    if result['success']:
        print(f"\n✅ 向量生成成功: {result['added_count']} 个")

        # ⭐⭐⭐ 将 vector_id 存回 chunks ⭐⭐⭐
        if 'vector_ids' in result:
            for i, vector_id in enumerate(result['vector_ids']):
                if i < len(chunks):
                    chunks[i]['vector_id'] = vector_id
                    
                    # 打印前几条的关联结果
                    if i < 3:
                        print(f"   [{i+1}] chunk_id={chunks[i].get('chunk_id')} -> vector_id={vector_id}")
    else:
        print(f"❌ 向量生成失败: {result['message']}")
    
    print("=" * 60)
    
    return result


# ========== 步骤 4：同步到数据库表 ==========

def sync_to_database(chunks, vector_service):
    """
    同步知识块到 SQLite 数据库
    
    ⭐⭐⭐ 新流程：先插入数据库获得 chunk_id，再存入 chunks ⭐⭐⭐
    """
    try:
        from models.knowledge_chunk import KnowledgeChunk
        import hashlib
        
        inserted_count = 0
        skipped_count = 0
        
        print("\n" + "=" * 60)
        print("💾 同步到数据库（获取 chunk_id）")
        print("=" * 60)
        
        for i, chunk in enumerate(chunks):
            # ⭐⭐⭐ 1. 生成 content_hash ⭐⭐⭐
            content_hash = hashlib.md5(chunk['content'].encode()).hexdigest()
            
            # ⭐⭐⭐ 2. 检查是否已存在（通过 content_hash 去重）⭐⭐⭐
            existing = KnowledgeChunk.query.filter_by(
                content_hash=content_hash
            ).first()
            
            if existing:
                print(f"   [{i+1}/{len(chunks)}] ⚠️  跳过重复: {chunk['chapter'][:30]}... (ID: {existing.id})")
                skipped_count += 1
                # ⭐ 即使跳过也要记录 chunk_id（用于引用）
                chunk['chunk_id'] = existing.id
                chunk['vector_id'] = existing.vector_id or chunk.get('vector_id')
                continue
            
            # ⭐⭐⭐ 3. 提取关键词 ⭐⭐⭐
            keywords = extract_keywords(chunk['content'])
            
            # ⭐⭐⭐ 4. 创建知识块记录（不设置 vector_id，稍后更新）⭐⭐⭐
            kb_chunk = KnowledgeChunk(
                content=chunk['content'],
                content_hash=content_hash,
                source=chunk['source'],
                chapter=chunk.get('chapter') or '未分类',
                section=chunk.get('section') or '',
                keywords=keywords,
                level=chunk.get('level', 2),
                vector_id=None,  # ⭐ 先不设置，等生成后再更新
                embedding_model='paraphrase-multilingual-MiniLM-L12-v2',
                char_count=len(chunk['content']),
                word_count=len(chunk['content'].split())
            )
            
            db.session.add(kb_chunk)
            db.session.flush()  # ⭐⭐⭐ 立即获取自增 ID ⭐⭐⭐
            
            # ⭐⭐⭐ 5. 将数据库 ID 存入 chunk ⭐⭐⭐
            chunk['chunk_id'] = kb_chunk.id
            
            print(f"   [{i+1}/{len(chunks)}] ✅ ID={kb_chunk.id}: {chunk['chapter'][:30]}...")
            
            inserted_count += 1
        
        db.session.commit()
        
        print(f"\n✅ 数据库同步完成: 新增 {inserted_count} 个，跳过 {skipped_count} 个重复")
        print("=" * 60)
        
        return inserted_count
        
    except Exception as e:
        print(f"❌ 数据库同步失败: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            db.session.rollback()
        except RuntimeError as re:
            print(f"⚠️  无法回滚事务（上下文已退出）: {re}")
        
        return 0


# ⭐⭐⭐ 修复：extract_keywords 函数 ⭐⭐⭐
def extract_keywords(content):
    """
    从内容中提取关键词（使用 jieba 分词）
    
    Args:
        content: 文本内容
        
    Returns:
        str: 逗号分隔的关键词
    """
    if not content:
        return ""
    
    try:
        # 1. 去除 Markdown 标记和代码块
        clean_text = re.sub(r'```[\s\S]+?```', '', content)  # 移除代码块
        clean_text = re.sub(r'`[^`]+`', '', clean_text)      # 移除行内代码
        clean_text = re.sub(r'[#*`\[\]()]', '', clean_text)  # 移除标记符号
        clean_text = re.sub(r'https?://\S+', '', clean_text) # 移除链接
        
        # 2. jieba 分词
        words = jieba.cut(clean_text)
        
        # 3. 过滤停用词和短词
        stopwords = {
            # 常见停用词
            '是', '的', '了', '在', '和', '与', '等', '也', '就', '都', '而', '及',
            '或', '为', '有', '对', '以', '上', '下', '中', '到', '从', '用', '这',
            '那', '个', '们', '中', '要', '可', '会', '出', '如', '将', '把', '但',
            '然后', '因为', '所以', '如果', '虽然', '可以', '什么', '怎么', '为什么',
            # 英文停用词
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
            'can', 'could', 'may', 'might', 'must', 'shall',
        }
        
        keywords = [
            w.strip() 
            for w in words 
            if len(w.strip()) > 1 and w.strip() not in stopwords
        ]
        
        # 4. 统计词频，取 Top 10
        from collections import Counter
        word_freq = Counter(keywords)
        top_keywords = [word for word, count in word_freq.most_common(10)]
        
        # 5. 去重并返回
        unique_keywords = []
        seen = set()
        for kw in top_keywords:
            if kw not in seen:
                unique_keywords.append(kw)
                seen.add(kw)
        
        result = ','.join(unique_keywords[:10])
        
        return result
        
    except Exception as e:
        print(f"⚠️ 关键词提取失败: {e}")
        return ""


# ========== 主函数 ==========

def import_knowledge():
    """
    主函数：导入知识库
    
    ⭐⭐⭐ 新流程：
    1. 读取文件并分块
    2. 先插入数据库（获得 chunk_id）
    3. 再生成向量（携带 chunk_id）
    4. 最后回写 vector_id 到数据库
    ⭐⭐⭐
    """
    print("=" * 60)
    print("🚀 开始导入知识库")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 获取脚本所在目录的父目录 (backend/)
    script_dir = Path(__file__).resolve().parent  # scripts/
    backend_dir = script_dir.parent  # backend/
    knowledge_dir = backend_dir / 'data' / 'knowledge'
    
    print(f"\n📂 知识库目录: {knowledge_dir}")
    
    if not knowledge_dir.exists():
        print(f"❌ 知识库目录不存在: {knowledge_dir}")
        return
    
    # ========== 步骤 1：读取文件 ==========
    markdown_files = load_markdown_files(knowledge_dir)
    
    if not markdown_files:
        print("❌ 没有找到 Markdown 文件")
        return
    
    # ========== 步骤 2：分块处理 ==========
    all_chunks = []
    
    for file_path, content in markdown_files:
        print(f"\n📄 处理文件: {file_path.name}")
        
        chunks = split_by_headers(content, file_path.name)
        
        print(f"   ✅ 分块完成: {len(chunks)} 个块")
        
        all_chunks.extend(chunks)
    
    print(f"\n📊 总计: {len(all_chunks)} 个知识块")
    
    # ⭐⭐⭐ 步骤 3：先同步到数据库（获得 chunk_id）⭐⭐⭐
    inserted_count = 0
    try:
        with app.app_context():
            vector_service = get_vector_service()
            
            # 3.1 插入数据库，获得 chunk_id
            inserted_count = sync_to_database(all_chunks, vector_service)
            
            if inserted_count == 0:
                print("⚠️  没有新知识块需要导入（可能全部重复）")
                return
            
            # ⭐⭐⭐ 步骤 4：生成向量（携带 chunk_id）⭐⭐⭐
            result = import_to_vector_db(all_chunks)
            
            if not result['success']:
                print(f"❌ 向量生成失败: {result['message']}")
                return
            
            # ⭐⭐⭐ 步骤 5：回写 vector_id 到数据库 ⭐⭐⭐
            update_vector_metadata(all_chunks, vector_service)
            
    except Exception as e:
        print(f"❌ 导入过程出错: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ========== 步骤 6：打印汇总 ==========
    print("\n" + "=" * 60)
    print("✅ 导入完成")
    print("=" * 60)
    print(f"📊 统计:")
    print(f"   文件数: {len(markdown_files)}")
    print(f"   知识块总数: {len(all_chunks)}")
    print(f"   新增数据库记录: {inserted_count}")
    print(f"   生成向量: {len([c for c in all_chunks if c.get('vector_id')])}")
    print("=" * 60)


# ⭐⭐⭐ 添加程序入口 ⭐⭐⭐
if __name__ == '__main__':
    # 解析命令行参数(可选)
    parser = argparse.ArgumentParser(description='导入知识库到向量数据库')
    parser.add_argument('--clear', action='store_true', help='清空现有数据后导入')
    args = parser.parse_args()
    
    # 如果指定 --clear,清空向量数据库
    if args.clear:
        print("\n⚠️  清空模式: 将删除所有现有数据")
        confirm = input("确认继续? (y/N): ")
        if confirm.lower() == 'y':
            with app.app_context():
                # 清空数据库表
                KnowledgeChunk.query.delete()
                db.session.commit()
                print("✅ 数据库表已清空")
            
            # 清空向量数据库
            vector_service = get_vector_service()
            vector_service.reset_collection()
            print("✅ 向量数据库已清空")
    
    # 执行导入
    import_knowledge()


# ⭐⭐⭐ 在文件末尾添加可导入的函数 ⭐⭐⭐

def import_single_file(file_path: Path) -> dict:
    """
    导入单个 Markdown 文件到知识库
    
    ⭐⭐⭐ 新流程：先数据库后向量 ⭐⭐⭐
    
    Args:
        file_path: 文件路径
        
    Returns:
        dict: 导入结果
    """
    try:
        print(f"\n{'='*60}")
        print(f"📂 导入单个文件: {file_path.name}")
        print(f"{'='*60}")
        
        # 1. 检查文件是否存在
        if not file_path.exists():
            return {
                'success': False,
                'message': f'文件不存在: {file_path}',
                'chunks_count': 0,
                'file_name': file_path.name
            }
        
        # 2. 读取文件内容
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {
                'success': False,
                'message': f'读取文件失败: {str(e)}',
                'chunks_count': 0,
                'file_name': file_path.name
            }
        
        # 3. 分块
        chunks = split_by_headers(content, file_path.name, max_length=1000)
        
        if not chunks:
            return {
                'success': False,
                'message': '文件内容为空或无法分块',
                'chunks_count': 0,
                'file_name': file_path.name
            }
        
        print(f"✅ 分块完成: {len(chunks)} 个知识块")
        
        # ⭐⭐⭐ 4. 先同步到数据库（获得 chunk_id）⭐⭐⭐
        vector_service = get_vector_service()
        inserted_count = sync_to_database(chunks, vector_service)
        
        if inserted_count == 0:
            return {
                'success': False,
                'message': '所有内容已存在（未导入新记录）',
                'chunks_count': 0,
                'file_name': file_path.name
            }
        
        # ⭐⭐⭐ 5. 生成向量（携带 chunk_id）⭐⭐⭐
        vector_result = import_to_vector_db(chunks)
        
        if not vector_result['success']:
            return {
                'success': False,
                'message': f"向量化失败: {vector_result['message']}",
                'chunks_count': 0,
                'file_name': file_path.name
            }
        
        # ⭐⭐⭐ 6. 回写 vector_id 到数据库 ⭐⭐⭐
        update_vector_metadata(chunks, vector_service)
        
        print(f"✅ 导入成功: {file_path.name}")
        print(f"   知识块数: {len(chunks)}")
        print(f"   新增记录: {inserted_count}")
        print(f"   生成向量: {vector_result['added_count']}")
        print(f"{'='*60}\n")
        
        return {
            'success': True,
            'message': '导入成功',
            'chunks_count': len(chunks),
            'vector_count': vector_result['added_count'],
            'db_count': inserted_count,
            'file_name': file_path.name
        }
        
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        traceback.print_exc()
        return {
            'success': False,
            'message': f'导入失败: {str(e)}',
            'chunks_count': 0,
            'file_name': file_path.name if file_path else 'unknown'
        }

def update_vector_metadata(chunks, vector_service):
    """
    ⭐⭐⭐ 修改：不再更新向量 metadata（已在生成时添加），而是回写 vector_id 到数据库 ⭐⭐⭐
    
    Args:
        chunks: 包含 chunk_id 和 vector_id 的知识块列表
        vector_service: 向量服务实例
    """
    print("\n" + "=" * 60)
    print("🔗 更新数据库记录的 vector_id")
    print("=" * 60)
    
    updated_count = 0
    
    for i, chunk in enumerate(chunks):
        chunk_id = chunk.get('chunk_id')
        vector_id = chunk.get('vector_id')
        
        if not chunk_id or not vector_id:
            print(f"   [{i+1}/{len(chunks)}] ⚠️ 缺少 chunk_id 或 vector_id，跳过")
            continue
        
        try:
            # ⭐⭐⭐ 更新数据库中的 vector_id ⭐⭐⭐
            kb_chunk = KnowledgeChunk.query.get(chunk_id)
            
            if not kb_chunk:
                print(f"   [{i+1}/{len(chunks)}] ⚠️ chunk_id={chunk_id} 不存在")
                continue
            
            kb_chunk.vector_id = vector_id
            
            updated_count += 1
            
            # 打印前几条
            if i < 3:
                print(f"   [{i+1}/{len(chunks)}] ✅ chunk_id={chunk_id} 已设置 vector_id={vector_id}")
            
        except Exception as e:
            print(f"   [{i+1}/{len(chunks)}] ❌ 更新失败: {e}")
    
    # 提交所有更新
    try:
        db.session.commit()
        print(f"\n✅ vector_id 更新完成: {updated_count}/{len(chunks)} 条记录")
    except Exception as e:
        print(f"\n❌ 提交失败: {e}")
        db.session.rollback()
    
    print("=" * 60)
    
    return updated_count