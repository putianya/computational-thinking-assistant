# -*- coding: utf-8 -*-
"""
测试 RAG 智能降级功能
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.llm_service import LLMService
from services.vector_service import get_vector_service


def test_rag_degradation():
    """测试不同场景的 RAG 降级"""
    
    print("\n" + "=" * 70)
    print("🧪 RAG 智能降级测试")
    print("=" * 70)
    
    # 测试用例
    test_cases = [
        # 高置信度场景（知识库有精确匹配）
        {
            'question': '什么是指针？',
            'expected_mode': 'high',
            'description': '概念类问题，知识库应有高度匹配'
        },
        # 中置信度场景（知识库有相关内容）
        {
            'question': 'C语言中如何使用指针访问数组元素？',
            'expected_mode': 'medium',
            'description': '稍微复杂的问题，可能部分匹配'
        },
        # 低置信度场景（知识库无相关内容）
        {
            'question': 'Python的装饰器怎么用？',
            'expected_mode': 'low',
            'description': '知识库没有Python内容'
        },
        # 闲聊场景（不走RAG）
        {
            'question': '你好',
            'expected_mode': 'none',
            'description': '闲聊不需要RAG'
        },
    ]
    
    # 初始化服务
    llm_service = LLMService()
    vector_service = get_vector_service()
    
    print(f"\n📊 知识库状态:")
    info = vector_service.get_collection_info()
    print(f"   文档数: {info.get('count', 0)}")
    print(f"   向量维度: {info.get('embedding_dim', 0)}")
    
    # 执行测试
    results = []
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n{'─' * 70}")
        print(f"测试 {i}: {case['description']}")
        print(f"问题: {case['question']}")
        print(f"预期模式: {case['expected_mode']}")
        print(f"{'─' * 70}")
        
        try:
            # 调用 _build_messages 方法
            messages, referenced_chunks = llm_service._build_messages(
                case['question'], 
                session_id=None
            )
            
            # 分析返回的消息
            if messages:
                system_prompt = messages[0]['content'] if messages else ''
                
                # 判断实际使用的模式
                if '高度相关' in system_prompt or '必须优先使用' in system_prompt:
                    actual_mode = 'high'
                elif '可能相关' in system_prompt or '选择性使用' in system_prompt:
                    actual_mode = 'medium'
                elif '暂无相关内容' in system_prompt or '暂无收录' in system_prompt:
                    actual_mode = 'low'
                else:
                    actual_mode = 'none'
                
                # 验证结果
                passed = actual_mode == case['expected_mode']
                status = '✅ 通过' if passed else '❌ 失败'
                
                print(f"\n结果: {status}")
                print(f"   实际模式: {actual_mode}")
                print(f"   引用知识块: {len(referenced_chunks)}个")
                print(f"   消息数: {len(messages)}条")
                
                results.append({
                    'question': case['question'],
                    'expected': case['expected_mode'],
                    'actual': actual_mode,
                    'passed': passed
                })
            else:
                print("❌ 构建消息失败")
                results.append({
                    'question': case['question'],
                    'expected': case['expected_mode'],
                    'actual': 'error',
                    'passed': False
                })
                
        except Exception as e:
            print(f"❌ 测试出错: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'question': case['question'],
                'expected': case['expected_mode'],
                'actual': 'error',
                'passed': False
            })
    
    # 汇总结果
    print(f"\n{'=' * 70}")
    print("📊 测试汇总")
    print(f"{'=' * 70}")
    
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    
    print(f"\n通过: {passed_count}/{total_count}")
    print(f"通过率: {passed_count/total_count*100:.1f}%")
    
    if passed_count < total_count:
        print(f"\n❌ 失败的测试:")
        for r in results:
            if not r['passed']:
                print(f"   - {r['question']}")
                print(f"     预期: {r['expected']}, 实际: {r['actual']}")
    
    print(f"\n{'=' * 70}\n")
    
    return passed_count == total_count


if __name__ == '__main__':
    success = test_rag_degradation()
    sys.exit(0 if success else 1)