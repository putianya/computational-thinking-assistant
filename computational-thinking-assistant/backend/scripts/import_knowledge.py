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
    
    # 查找所有标题位置
    matches = list(header_pattern.finditer(markdown_text))
    
    if not matches:
        # 如果没有标题，将整个文档作为一块
        if markdown_text.strip():
            # ⭐ 直接调用分割函数
            sub_chunks = split_long_chunk(
                markdown_text.strip(), 
                source_file.replace('.md', ''),
                None,
                1,
                max_length
            )
            chunks.extend(sub_chunks)
        return chunks
    
    # 遍历每个标题，提取对应的内容块
    for i, match in enumerate(matches):
        # 标题级别（## = 2, ### = 3）
        level = len(match.group(1))
        
        # 标题文本
        title = match.group(2).strip()
        
        # 内容起始位置
        start_pos = match.start()
        
        # 内容结束位置（下一个标题开始，或文档末尾）
        if i + 1 < len(matches):
            end_pos = matches[i + 1].start()
        else:
            end_pos = len(markdown_text)
        
        # 提取完整内容（包含标题）
        content = markdown_text[start_pos:end_pos].strip()
        
        # 过滤条件
        if not content:
            continue
        
        # 过滤纯代码块（至少要有一些说明文字）
        code_block_pattern = re.compile(r'```[\s\S]+?```')
        content_without_code = code_block_pattern.sub('', content)
        
        if len(content_without_code.strip()) < 20:
            continue  # 跳过内容过少的块
        
        # 判断层级关系
        if level == 2:
            chapter = title
            section = None
        elif level == 3:
            # 找到上一个 ## 标题作为章节
            chapter = None
            for prev_match in reversed(matches[:i]):
                if len(prev_match.group(1)) == 2:
                    chapter = prev_match.group(2).strip()
                    break
            
            if not chapter:
                chapter = source_file.replace('.md', '')
            
            section = title
        else:
            # 其他级别（#### 等）归入上一个章节
            chapter = source_file.replace('.md', '')
            section = title
        
        # ⭐⭐⭐ 新增：检查块长度，超长则分割 ⭐⭐⭐
        if len(content) > max_length:
            print(f"⚠️  块过长 ({len(content)} 字符)，进行分割: {chapter} - {section}")
            sub_chunks = split_long_chunk(content, chapter, section, level, max_length)
            chunks.extend(sub_chunks)
        else:
            # 添加到结果
            chunks.append({
                'content': content,
                'source': source_file,
                'chapter': chapter,
                'section': section,
                'level': level
            })
    
    return chunks


# ⭐⭐⭐ 新增：长块分割函数 ⭐⭐⭐
def split_long_chunk(content, chapter, section, level, max_length=1000):
    """
    分割超长的知识块
    
    策略：
    1. 按空行（\\n\\n）分割段落
    2. 合并段落直到接近 max_length
    3. 如果单个段落超长，按句号分割
    
    Args:
        content: 原始内容
        chapter: 章节名
        section: 小节名
        level: 标题级别
        max_length: 最大长度
        
    Returns:
        list: 分割后的块列表
    """
    # 1. 按空行分割段落
    paragraphs = re.split(r'\n\s*\n', content)
    
    sub_chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # 2. 尝试合并段落
        if len(current_chunk) + len(para) + 2 <= max_length:
            # 可以合并
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
        else:
            # 无法合并
            if current_chunk:
                # 保存当前块
                sub_chunks.append({
                    'content': current_chunk,
                    'source': f"{chapter}.md" if chapter else "unknown.md",
                    'chapter': chapter,
                    'section': section,
                    'level': level
                })
            
            # 3. 检查单个段落是否超长
            if len(para) > max_length:
                # 按句号分割
                sentences = re.split(r'([。.!?！？])', para)
                
                temp_chunk = ""
                for i in range(0, len(sentences), 2):
                    sentence = sentences[i]
                    punct = sentences[i + 1] if i + 1 < len(sentences) else ""
                    
                    full_sentence = sentence + punct
                    
                    if len(temp_chunk) + len(full_sentence) <= max_length:
                        temp_chunk += full_sentence
                    else:
                        if temp_chunk:
                            sub_chunks.append({
                                'content': temp_chunk,
                                'source': f"{chapter}.md" if chapter else "unknown.md",
                                'chapter': chapter,
                                'section': section,
                                'level': level
                            })
                        temp_chunk = full_sentence
                
                current_chunk = temp_chunk
            else:
                current_chunk = para
    
    # 4. 保存最后一个块
    if current_chunk:
        sub_chunks.append({
            'content': current_chunk,
            'source': f"{chapter}.md" if chapter else "unknown.md",
            'chapter': chapter,
            'section': section,
            'level': level
        })
    
    print(f"   ✂️  分割成 {len(sub_chunks)} 个子块")
    return sub_chunks


# ========== 步骤 3：导入到向量数据库 ==========

def import_to_vector_db(chunks):
    """
    导入知识块到 ChromaDB
    
    Args:
        chunks: 知识块列表
        
    Returns:
        dict: 导入结果
    """
    if not chunks:
        return {
            'success': False,
            'message': '没有可导入的知识块'
        }
    
    print("\n" + "=" * 60)
    print("📤 导入到向量数据库...")
    print("=" * 60)
    
    # 获取向量服务
    vector_service = get_vector_service()
    
    # 提取数据
    texts = [chunk['content'] for chunk in chunks]
    metadatas = [
        {
            'source': chunk['source'],
            'chapter': chunk['chapter'],
            'section': chunk.get('section'),
            'level': chunk.get('level', 2)
        }
        for chunk in chunks
    ]
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    
    # 批量导入
    result = vector_service.add_documents(
        texts=texts,
        metadatas=metadatas,
        ids=ids
    )
    
    return result


# ========== 步骤 4：同步到数据库表 ==========

def sync_to_database(chunks):
    """
    同步知识块到 KnowledgeChunk 表
    """
    print("\n" + "=" * 60)
    print("💾 同步到数据库表...")
    print("=" * 60)
    
    with app.app_context():
        # ⭐ 先检查模型字段
        print("\n🔍 检查 KnowledgeChunk 模型字段:")
        for col in KnowledgeChunk.__table__.columns:
            print(f"   - {col.name}")
        
        # ⭐⭐⭐ 新增：清空现有数据 ⭐⭐⭐
        print("\n🗑️  清空现有数据...")
        deleted_count = KnowledgeChunk.query.delete()
        db.session.commit()
        print(f"   已删除 {deleted_count} 条旧记录")
        
        inserted_count = 0
        
        for i, chunk in enumerate(chunks):
            try:
                chunk_data = {
                    'vector_id': f"chunk_{i}",
                    'content': chunk['content'],
                    'chapter': chunk['chapter'],
                    'section': chunk.get('section'),
                    'keywords': extract_keywords(chunk['content'])
                }
                
                if hasattr(KnowledgeChunk, 'source'):
                    chunk_data['source'] = chunk['source']
                elif hasattr(KnowledgeChunk, 'source_file'):
                    chunk_data['source_file'] = chunk['source']
                elif hasattr(KnowledgeChunk, 'file_name'):
                    chunk_data['file_name'] = chunk['source']
                
                knowledge_chunk = KnowledgeChunk(**chunk_data)
                db.session.add(knowledge_chunk)
                db.session.flush()
                
                inserted_count += 1
                
                if (i + 1) % 10 == 0:
                    print(f"   已插入 {i + 1}/{len(chunks)} 条...")
                
            except Exception as e:
                print(f"❌ 插入失败 (chunk_{i}): {e}")
                print(f"   数据: {chunk['source']} - {chunk['chapter']}")
                db.session.rollback()
                continue
        
        try:
            db.session.commit()
            print(f"✅ 成功插入 {inserted_count} 条记录")
            return inserted_count
        
        except Exception as e:
            db.session.rollback()
            print(f"❌ 数据库提交失败: {e}")
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
        
        result = ','.join(unique_keywords[:10])  # 最多保留 10 个
        
        return result
        
    except Exception as e:
        print(f"⚠️ 关键词提取失败: {e}")
        return ""


# ========== 主函数 ==========

def import_knowledge():
    """
    主函数:导入知识库
    
    流程:
        1. 读取所有 Markdown 文件
        2. 分块处理
        3. 导入到向量数据库
        4. 同步到数据库表
    """
    print("=" * 60)
    print("🚀 开始导入知识库")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # ⭐⭐⭐ 修复: 正确计算知识库目录路径 ⭐⭐⭐
    # 获取脚本所在目录的父目录 (backend/)
    script_dir = Path(__file__).resolve().parent  # scripts/
    backend_dir = script_dir.parent                # backend/
    knowledge_dir = backend_dir / 'data' / 'knowledge'
    
    print(f"\n📂 读取目录: {knowledge_dir}")
    print(f"   目录是否存在: {knowledge_dir.exists()}")
    
    if not knowledge_dir.exists():
        print(f"❌ 目录不存在,请检查路径!")
        return
    
    # 列出目录中的文件
    md_files = list(knowledge_dir.glob('*.md'))
    print(f"   找到 {len(md_files)} 个 .md 文件:")
    for f in md_files:
        print(f"      - {f.name}")
    
    files = load_markdown_files(knowledge_dir)
    
    if not files:
        print("❌ 未找到任何 Markdown 文件")
        return
    
    print(f"✅ 成功读取 {len(files)} 个文件")
    
    # ========== 步骤 2: 分块 ==========
    print("\n✂️  开始分块...")
    all_chunks = []
    
    for file_path, content in files:
        chunks = split_by_headers(content, file_path.name, max_length=1000)
        all_chunks.extend(chunks)
        print(f"   {file_path.name}: {len(chunks)} 个块")
    
    print(f"\n✅ 共分割 {len(all_chunks)} 个知识块")
    
    # 打印前 3 个块的预览
    print("\n📋 知识块预览:")
    for i, chunk in enumerate(all_chunks[:3], 1):
        print(f"\n块 {i}:")
        print(f"  来源: {chunk['source']}")
        print(f"  章节: {chunk['chapter']}")
        print(f"  小节: {chunk.get('section', 'N/A')}")
        print(f"  长度: {len(chunk['content'])} 字符")
        print(f"  内容: {chunk['content'][:80]}...")
    
    # ========== 步骤 3: 导入向量数据库 ==========
    result = import_to_vector_db(all_chunks)
    
    if not result['success']:
        print(f"❌ 向量数据库导入失败: {result['message']}")
        return
    
    print(f"✅ 向量数据库导入成功: {result['count']} 个块")
    
    # ========== 步骤 4: 同步到数据库 ==========
    inserted_count = sync_to_database(all_chunks)
    
    # ========== 完成 ==========
    print("\n" + "=" * 60)
    print("🎉 知识库导入完成")
    print("=" * 60)
    print(f"📊 统计信息:")
    print(f"   文件数: {len(files)}")
    print(f"   知识块数: {len(all_chunks)}")
    print(f"   向量数据库: {result['count']} 条")
    print(f"   数据库表: {inserted_count} 条")
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
    
    Args:
        file_path: 文件路径
        
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'chunks_count': int,
            'file_name': str
        }
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
        
        # 4. 导入到向量数据库
        vector_result = import_to_vector_db(chunks)
        
        if not vector_result['success']:
            return {
                'success': False,
                'message': f"向量化失败: {vector_result['message']}",
                'chunks_count': 0,
                'file_name': file_path.name
            }
        
        # 5. 同步到数据库
        inserted_count = sync_to_database(chunks)
        
        print(f"✅ 导入成功: {file_path.name}")
        print(f"   知识块数: {len(chunks)}")
        print(f"   向量数: {vector_result['count']}")
        print(f"   数据库记录: {inserted_count}")
        print(f"{'='*60}\n")
        
        return {
            'success': True,
            'message': '导入成功',
            'chunks_count': len(chunks),
            'vector_count': vector_result['count'],
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