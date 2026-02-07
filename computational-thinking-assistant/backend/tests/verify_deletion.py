# -*- coding: utf-8 -*-
"""
验证删除操作是否完整
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, BASE_DIR
from database import db
from models.knowledge_chunk import KnowledgeChunk
from services.vector_service import get_vector_service


def verify_deletion(filename):
    """验证文档是否完全删除"""
    print("\n" + "=" * 60)
    print(f"🔍 验证文档删除: {filename}")
    print("=" * 60)
    
    with app.app_context():
        # 1. 检查物理文件
        knowledge_dir = Path(BASE_DIR) / 'data' / 'knowledge'
        file_path = knowledge_dir / filename
        
        file_exists = file_path.exists()
        print(f"\n📁 物理文件:")
        print(f"   路径: {file_path}")
        print(f"   状态: {'❌ 仍存在' if file_exists else '✅ 已删除'}")
        
        # 2. 检查数据库记录
        chunks = KnowledgeChunk.query.filter_by(source=filename).all()
        print(f"\n💾 数据库记录:")
        print(f"   数量: {len(chunks)}")
        
        if chunks:
            print(f"   ❌ 仍有 {len(chunks)} 条记录:")
            for chunk in chunks[:5]:
                print(f"      - ID={chunk.id}, chapter={chunk.chapter}, vector_id={chunk.vector_id}")
        else:
            print(f"   ✅ 已清空")
        
        # 3. 检查向量数据库
        vector_service = get_vector_service()
        
        # 获取所有向量
        all_vectors = vector_service.collection.get(include=['metadatas'])
        
        # 筛选属于该文档的向量
        related_vectors = [
            vid for vid, meta in zip(all_vectors['ids'], all_vectors['metadatas'])
            if meta and meta.get('source') == filename
        ]
        
        print(f"\n🔍 向量数据库:")
        print(f"   该文档的向量数: {len(related_vectors)}")
        
        if related_vectors:
            print(f"   ❌ 仍有 {len(related_vectors)} 个向量:")
            for vid in related_vectors[:5]:
                print(f"      - {vid}")
        else:
            print(f"   ✅ 已清空")
        
        # 4. 汇总
        print(f"\n{'='*60}")
        print(f"📊 删除完整性检查:")
        
        all_clean = not file_exists and len(chunks) == 0 and len(related_vectors) == 0
        
        if all_clean:
            print(f"   ✅ 删除完整！文档已完全移除")
        else:
            print(f"   ❌ 删除不完整：")
            if file_exists:
                print(f"      - 物理文件未删除")
            if len(chunks) > 0:
                print(f"      - 数据库还有 {len(chunks)} 条记录")
            if len(related_vectors) > 0:
                print(f"      - 向量库还有 {len(related_vectors)} 个向量")
        
        print(f"{'='*60}\n")
        
        return all_clean


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='验证文档删除')
    parser.add_argument('filename', help='文档名称（如：06_数组.md）')
    args = parser.parse_args()
    
    verify_deletion(args.filename)