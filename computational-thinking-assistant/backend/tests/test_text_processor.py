# -*- coding: utf-8 -*-
"""
文本预处理模块单元测试
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.text_processor import TextProcessor


def test_clean_question():
    """测试问题清洗"""
    print("\n【测试 1】问题清洗")
    
    test_cases = [
        ("指针是什么？？？   ", "指针是什么?"),
        ("Python   列表   有哪些方法？", "Python 列表 有哪些方法?"),
        ("什么是《算法导论》？", "什么是<算法导论>?"),
    ]
    
    for original, expected in test_cases:
        result = TextProcessor.clean_question(original)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{original}' -> '{result}'")
        if result != expected:
            print(f"   预期: '{expected}'")


def test_homework_detection():
    """测试作业检测"""
    print("\n【测试 2】作业检测")
    
    homework_cases = [
        ("帮我写一个排序程序", True),
        ("第3章第5题怎么做", True),
        ("完整代码是什么", True),
    ]
    
    normal_cases = [
        ("什么是指针?", False),
        ("Python 列表有哪些方法?", False),
    ]
    
    for text, expected in homework_cases:
        is_hw, keyword = TextProcessor.is_homework_question(text)
        status = "✅" if is_hw == expected else "❌"
        print(f"{status} 作业题: '{text}' -> {is_hw} ({keyword})")
    
    for text, expected in normal_cases:
        is_hw, keyword = TextProcessor.is_homework_question(text)
        status = "✅" if is_hw == expected else "❌"
        print(f"{status} 正常题: '{text}' -> {is_hw}")


def test_sensitive_detection():
    """测试敏感词检测"""
    print("\n【测试 3】敏感词检测")
    
    # 这里只是测试框架，实际敏感词库需要更完善
    normal_case = "什么是计算思维?"
    has_sensitive, words = TextProcessor.contains_sensitive_content(normal_case)
    status = "✅" if not has_sensitive else "❌"
    print(f"{status} 正常内容: '{normal_case}' -> {has_sensitive}")


def test_full_analysis():
    """测试综合分析"""
    print("\n【测试 4】综合分析")
    
    question = "帮我写一个冒泡排序程序？？？"
    result = TextProcessor.analyze_question(question)
    
    print(f"原始: {result['original']}")
    print(f"清洗: {result['cleaned']}")
    print(f"检索: {result['for_retrieval']}")
    print(f"作业: {result['is_homework']}")
    print(f"拒绝: {result['should_reject']}")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 文本预处理模块测试")
    print("="*60)
    
    test_clean_question()
    test_homework_detection()
    test_sensitive_detection()
    test_full_analysis()
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60 + "\n")