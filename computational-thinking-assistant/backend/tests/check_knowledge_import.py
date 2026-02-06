# -*- coding: utf-8 -*-
"""检查知识库导入情况"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models.knowledge_chunk import KnowledgeChunk
from services.vector_service import get_vector_service

def check_import():
    """检查导入情况"""
    print("\n" + "=" * 60)
    print("🔍 检查知识库导入情况")
    print("=" * 60)
    
    with app.app_context():
        # 1. 检查数据库
        from database import db
        
        chunks = KnowledgeChunk.query.filter_by(source='01_C.md').all()
        
        print(f"\n📊 数据库中的知识块:")
        print(f"   来源: 01_C.md")
        print(f"   数量: {len(chunks)}")
        
        if chunks:
            print(f"\n📋 知识块列表:")
            for i, chunk in enumerate(chunks, 1):
                print(f"\n   {i}. 【{chunk.chapter}】")
                print(f"      ID: {chunk.id}")
                print(f"      小节: {chunk.section or 'N/A'}")
                print(f"      长度: {chunk.char_count} 字符")
                print(f"      向量ID: {chunk.vector_id}")
                print(f"      内容预览: {chunk.content[:60]}...")
        else:
            print("   ⚠️  未找到任何知识块")
        
        # 2. 检查向量数据库
        print(f"\n📊 向量数据库:")
        vs = get_vector_service()
        info = vs.get_collection_info()
        
        print(f"   集合名: {info['name']}")
        print(f"   文档总数: {info['count']}")
        print(f"   向量维度: {info['embedding_dim']}")
        
        # 3. 测试检索
        print(f"\n🔍 测试检索: '什么是C语言'")
        results = vs.search("什么是C语言", top_k=3)
        
        if results:
            print(f"   找到 {len(results)} 个结果:")
            for i, doc in enumerate(results, 1):
                print(f"\n   {i}. 相似度: {doc['score']:.4f}")
                print(f"      来源: {doc.get('metadata', {}).get('source', 'N/A')}")
                print(f"      章节: {doc.get('metadata', {}).get('chapter', 'N/A')}")
                print(f"      内容: {doc['text'][:80]}...")
        else:
            print("   ⚠️  未找到任何结果")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    check_import()