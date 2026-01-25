# -*- coding: utf-8 -*-
"""
向量服务测试脚本
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.vector_service import get_vector_service


def test_basic_operations():
    """测试基本操作"""
    
    print("=" * 60)
    print("🧪 向量服务基本操作测试")
    print("=" * 60)
    
    # 获取向量服务实例
    vector_service = get_vector_service()
    
    # 1. 添加测试文档
    print("\n1️⃣ 添加文档:")
    result = vector_service.add_documents(
        texts=[
            "指针是 C 语言的核心概念",
            "链表使用指针连接节点",
            "Python 不需要手动管理指针"
        ],
        ids=["test_1", "test_2", "test_3"]
    )
    print(f"✅ {result['message']}")
    
    # 2. 测试检索
    print("\n2️⃣ 检索测试:")
    queries = [
        "C语言中的指针是什么",
        "链表如何实现",
        "Python有指针吗"
    ]
    
    for query in queries:
        print(f"\n查询: {query}")
        results = vector_service.search(query, top_k=2)
        
        for doc in results:
            print(f"  ✓ [{doc['score']:.3f}] {doc['text'][:40]}...")
    
    # 3. 查看集合信息
    print("\n3️⃣ 集合信息:")
    info = vector_service.get_collection_info()
    print(f"  文档总数: {info['count']}")
    print(f"  向量维度: {info['embedding_dim']}")
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)


if __name__ == '__main__':
    test_basic_operations()
    