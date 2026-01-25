# -*- coding: utf-8 -*-
"""
检查向量数据完整性
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.vector_service import get_vector_service
import numpy as np

def check_vectors():
    """检查向量数据"""
    print("\n" + "=" * 60)
    print("🔍 检查向量数据")
    print("=" * 60)
    
    # 获取向量服务
    vs = get_vector_service()
    
    # 获取集合信息
    info = vs.get_collection_info()
    print(f"\n📊 集合信息:")
    print(f"   名称: {info['name']}")
    print(f"   文档数: {info['count']}")
    print(f"   向量维度: {info['embedding_dim']}")
    
    # 获取第一个文档的向量
    results = vs.collection.get(
        ids=["chunk_0"],
        include=['documents', 'embeddings', 'metadatas']
    )
    
    if results['embeddings']:
        embedding = results['embeddings'][0]
        print(f"\n📄 第一个文档 (chunk_0):")
        print(f"   内容: {results['documents'][0][:100]}...")
        print(f"   向量维度: {len(embedding)}")
        print(f"   向量前5位: {embedding[:5]}")
        print(f"   向量范数: {np.linalg.norm(embedding):.4f}")
        print(f"   元数据: {results['metadatas'][0]}")
    
    # 测试简单查询
    print(f"\n🔍 测试查询: '指针'")
    test_results = vs.search("指针", top_k=3)
    
    print(f"\n📊 查询结果:")
    print(f"   返回数量: {len(test_results)}")
    
    if test_results:
        for i, doc in enumerate(test_results[:3], 1):
            print(f"\n   结果 {i}:")
            print(f"      相似度: {doc['score']:.4f}")
            print(f"      内容: {doc['text'][:50]}...")
    else:
        print("   ⚠️  未返回任何结果")
    
    print("\n" + "=" * 60)

if __name__ == '__main__':
    check_vectors()