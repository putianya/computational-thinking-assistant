# -*- coding: utf-8 -*-
"""
向量检索测试脚本

功能：
1. 测试 ChromaDB 向量检索功能
2. 测试不同类型的问题检索效果
3. 验证相似度阈值和 Top-K 参数
4. 输出详细的检索结果分析

使用方法：
    python tests/test_vector_search.py
    python tests/test_vector_search.py --query "什么是指针"
    python tests/test_vector_search.py --top-k 5 --threshold 0.6

作者: 计算思维助手团队
日期: 2026-01-26
"""
import sys
import os
import argparse
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.vector_service import get_vector_service
from utils.question_classifier import classify_question


# ========== 测试用例库 ==========

TEST_QUERIES = {
    '概念类': [
        "什么是指针？",
        "解释一下链表的概念",
        "指针和引用有什么区别？",
        "什么是野指针？",
    ],
    '语法类': [
        "如何声明一个指针？",
        "指针怎么赋值？",
        "链表如何插入节点？",
        "如何创建一个链表节点？",
    ],
    '错误类': [
        "野指针报错怎么解决？",
        "指针访问越界如何处理？",
        "为什么会出现段错误？",
        "悬空指针如何避免？",
    ],
    '算法类': [
        "如何反转一个链表？",
        "如何查找链表中的节点？",
        "链表如何排序？",
        "如何删除链表中的重复元素？",
    ],
}


# ========== 测试函数 ==========

def test_single_query(query, top_k=3, threshold=0.7):
    """
    测试单个查询
    
    Args:
        query: 问题文本
        top_k: 返回结果数量
        threshold: 相似度阈值
    """
    print("\n" + "=" * 80)
    print(f"🔍 查询: {query}")
    print("=" * 80)
    
    # 1. 问题分类
    classification = classify_question(query)
    
    # ⭐ 使用正确的键名（兼容两种方式）
    category = classification.get('category') or classification.get('type', 'general')
    confidence = classification.get('confidence', 0.0)
    
    print(f"\n📊 问题类型: {category} (置信度: {confidence:.2f})")
    print(f"   建议参数: top_k={classification.get('top_k', top_k)}, threshold={classification.get('threshold', threshold)}")
    
    # 2. 向量检索
    vector_service = get_vector_service()
    
    # ⭐⭐⭐ 修复：使用正确的参数名 ⭐⭐⭐
    results = vector_service.search(
        query=query,              # ⭐ 参数名改为 'query'
        top_k=top_k
        
        # ⭐ 注意：vector_service.search() 没有 min_similarity 参数
        # 相似度过滤在返回结果后手动处理
    )
    
    # 3. 手动过滤低相似度结果
    filtered_results = [
        doc for doc in results 
        if doc.get('score', 0) >= threshold
    ]
    
    # 4. 输出结果
    if not filtered_results:
        print(f"\n❌ 未找到相似度 >= {threshold} 的相关内容")
        return
    
    print(f"\n✅ 找到 {len(filtered_results)} 个相关结果（阈值 >= {threshold}）")
    print("-" * 80)
    
    # 遍历结果
    for i, doc in enumerate(filtered_results, 1):
        print(f"\n📄 结果 {i}:")
        print(f"   ID: {doc.get('id', 'N/A')}")
        print(f"   相似度: {doc.get('score', 0):.4f}")
        print(f"   来源: {doc.get('metadata', {}).get('source', 'N/A')}")
        print(f"   章节: {doc.get('metadata', {}).get('chapter', 'N/A')}")
        print(f"   小节: {doc.get('metadata', {}).get('section', 'N/A')}")
        print(f"   内容预览: {doc.get('text', '')[:150]}...")
        print("-" * 80)


def test_batch_queries(category=None, top_k=3, threshold=0.7):
    """
    批量测试多个查询
    
    Args:
        category: 测试类别 (None 表示全部)
        top_k: 返回结果数量
        threshold: 相似度阈值
    """
    if category and category in TEST_QUERIES:
        categories = {category: TEST_QUERIES[category]}
    else:
        categories = TEST_QUERIES
    
    print("\n" + "=" * 80)
    print("🧪 批量测试向量检索")
    print("=" * 80)
    print(f"参数: top_k={top_k}, threshold={threshold}")
    print("=" * 80)
    
    total_queries = 0
    successful_queries = 0
    
    for cat_name, queries in categories.items():
        print(f"\n\n{'#' * 80}")
        print(f"# 测试类别: {cat_name}")
        print(f"{'#' * 80}")
        
        for query in queries:
            total_queries += 1
            
            # 测试单个查询
            try:
                test_single_query(query, top_k, threshold)
                successful_queries += 1
            except Exception as e:
                print(f"\n❌ 查询失败: {e}")
                import traceback
                traceback.print_exc()
    
    # 输出统计
    print("\n" + "=" * 80)
    print("📊 测试统计")
    print("=" * 80)
    print(f"总查询数: {total_queries}")
    print(f"成功查询: {successful_queries}")
    print(f"失败查询: {total_queries - successful_queries}")
    print(f"成功率: {successful_queries / total_queries * 100:.1f}%")
    print("=" * 80)


def test_collection_info():
    """
    测试向量数据库集合信息
    """
    print("\n" + "=" * 80)
    print("📊 向量数据库信息")
    print("=" * 80)
    
    vector_service = get_vector_service()
    
    try:
        # 获取集合信息
        info = vector_service.get_collection_info()
        
        if info.get('success'):
            print(f"✅ 集合名称: {info.get('name', 'N/A')}")
            print(f"✅ 文档总数: {info.get('count', 0)}")
            print(f"✅ 向量维度: {info.get('embedding_dim', 0)}")
            print(f"✅ 元数据: {info.get('metadata', {})}")
        else:
            print(f"❌ 获取信息失败: {info.get('message', 'unknown error')}")
        
        # 获取前 5 个文档样本
        if info.get('count', 0) > 0:
            try:
                results = vector_service.collection.get(limit=5)
                
                print(f"\n📋 样本数据 (前 5 个):")
                for i, (doc_id, doc, metadata) in enumerate(zip(
                    results['ids'], 
                    results['documents'], 
                    results['metadatas']
                ), 1):
                    print(f"\n   {i}. ID: {doc_id}")
                    print(f"      来源: {metadata.get('source', 'N/A')}")
                    print(f"      章节: {metadata.get('chapter', 'N/A')}")
                    print(f"      内容: {doc[:80]}...")
            except Exception as e:
                print(f"⚠️ 获取样本数据失败: {e}")
        
    except Exception as e:
        print(f"❌ 获取信息失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)


def test_similarity_threshold():
    """
    测试不同相似度阈值的影响
    """
    test_query = "什么是指针？"
    thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
    
    print("\n" + "=" * 80)
    print(f"🎯 相似度阈值测试: {test_query}")
    print("=" * 80)
    
    vector_service = get_vector_service()
    
    for threshold in thresholds:
        try:
            # ⭐ 使用正确的参数名
            results = vector_service.search(
                query=test_query,
                top_k=10
            )
            
            # 手动过滤
            filtered = [doc for doc in results if doc.get('score', 0) >= threshold]
            
            print(f"\n阈值 {threshold:.1f}: 返回 {len(filtered)} 个结果")
            
            if filtered:
                # 显示最高相似度
                max_score = max(doc.get('score', 0) for doc in filtered)
                print(f"   最高相似度: {max_score:.4f}")
        
        except Exception as e:
            print(f"阈值 {threshold:.1f}: ❌ 查询失败: {e}")


# ========== 主函数 ==========

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='向量检索测试脚本')
    
    parser.add_argument(
        '--query', '-q',
        type=str,
        help='单个测试查询'
    )
    
    parser.add_argument(
        '--category', '-c',
        type=str,
        choices=['概念类', '语法类', '错误类', '算法类'],
        help='批量测试的类别'
    )
    
    parser.add_argument(
        '--top-k', '-k',
        type=int,
        default=3,
        help='返回结果数量 (默认: 3)'
    )
    
    parser.add_argument(
        '--threshold', '-t',
        type=float,
        default=0.7,
        help='相似度阈值 (默认: 0.7)'
    )
    
    parser.add_argument(
        '--info', '-i',
        action='store_true',
        help='显示向量数据库信息'
    )
    
    parser.add_argument(
        '--threshold-test',
        action='store_true',
        help='测试不同相似度阈值'
    )
    
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='运行所有测试'
    )
    
    args = parser.parse_args()
    
    # 显示欢迎信息
    print("\n" + "🤖" * 40)
    print("计算思维助手 - 向量检索测试工具")
    print("🤖" * 40)
    
    # 执行测试
    try:
        if args.all:
            # 运行所有测试
            test_collection_info()
            test_similarity_threshold()
            test_batch_queries(top_k=args.top_k, threshold=args.threshold)
        
        elif args.info:
            # 显示数据库信息
            test_collection_info()
        
        elif args.threshold_test:
            # 测试阈值
            test_similarity_threshold()
        
        elif args.query:
            # 单个查询测试
            test_single_query(args.query, args.top_k, args.threshold)
        
        else:
            # 默认：批量测试
            test_batch_queries(args.category, args.top_k, args.threshold)
    
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ 测试完成\n")


if __name__ == "__main__":
    main()