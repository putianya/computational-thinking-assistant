# -*- coding: utf-8 -*-
"""
问题分类器模块

功能：
1. 识别问题类型（概念、语法、错误、示例、算法）
2. 为 RAG 检索提供策略参数
3. 辅助选择回答模板

作者: 计算思维助手团队
日期: 2026-01-21
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ClassificationResult:
    """分类结果数据类"""
    question_type: str  # 问题类型
    confidence: float   # 置信度 (0-1)
    keywords: List[str] # 匹配到的关键词
    retrieval_params: Dict  # 检索参数建议
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'type': self.question_type,
            'confidence': self.confidence,
            'keywords': self.keywords,
            'retrieval_params': self.retrieval_params
        }


class QuestionClassifier:
    """
    问题分类器
    
    分类结果用于：
    1. 选择不同的知识库检索策略
    2. 调整检索参数（top_k、相似度阈值）
    3. 选择不同的回答模板
    """
    
    # ========== 1. 概念类问题关键词 ==========
    CONCEPT_KEYWORDS = {
        # 概念询问词
        'what': ['什么是', '啥是', '何为', '定义', '概念', '含义', 
                 'what is', 'what are', '解释一下', '介绍一下'],
        
        # 原理询问词
        'why': ['为什么', '为何', '原因', '原理', 'why', '怎么会'],
        
        # 区别对比词
        'difference': ['区别', '不同', '差异', 'difference', '对比', 
                      '比较', 'vs', '和...的区别'],
    }
    
    # ========== 2. 语法类问题关键词 ==========
    SYNTAX_KEYWORDS = {
        # 如何做
        'how': ['如何', '怎么', '怎样', 'how to', 'how do'],
        
        # 语法关键词
        'syntax': ['语法', '写法', '格式', 'syntax', '用法', '使用方法'],
        
        # 声明定义
        'declare': ['定义', '声明', '创建', 'define', 'declare', 
                   '初始化', 'initialize'],
    }
    
    # ========== 3. 错误诊断类关键词 ==========
    ERROR_KEYWORDS = {
        # 错误提示
        'error': ['报错', '错误', 'error', 'bug', '异常', 'exception'],
        
        # 问题描述
        'problem': ['出问题', '不行', '不对', '失败', 'failed', '不工作', 
                   '运行不了', '编译不过'],
        
        # 调试相关
        'debug': ['调试', 'debug', '找不到', '无法', 'cannot', '不能'],
    }
    
    # ========== 4. 代码示例类关键词 ==========
    EXAMPLE_KEYWORDS = {
        # 示例请求
        'example': ['例子', '示例', 'example', '样例', 'sample', 
                   '演示', 'demo'],
        
        # 代码请求
        'code': ['代码', 'code', '程序', 'program'],
        
        # 给我看看
        'show': ['给我', '看看', 'show me', '展示'],
    }
    
    # ========== 5. 算法实现类关键词 ==========
    ALGORITHM_KEYWORDS = {
        # 实现
        'implement': ['实现', '实施', 'implement', '完成', '编写'],
        
        # 算法名称
        'algorithm': ['算法', 'algorithm', '排序', 'sort', '搜索', 'search',
                     '遍历', 'traverse', '递归', 'recursion'],
        
        # 步骤
        'steps': ['步骤', 'steps', '过程', 'process', '流程'],
    }
    
    # ========== 6. 检索参数配置 ==========
    RETRIEVAL_CONFIGS = {
        'concept': {
            'top_k': 5,              # 检索前5个相似文档
            'similarity_threshold': 0.75,  # 相似度阈值
            'strategy': 'semantic',  # 语义检索
            'template': 'concept_explanation'  # 概念解释模板
        },
        'syntax': {
            'top_k': 3,
            'similarity_threshold': 0.80,
            'strategy': 'hybrid',    # 混合检索（语义+关键词）
            'template': 'syntax_guide'
        },
        'error': {
            'top_k': 8,              # 错误诊断需要更多参考
            'similarity_threshold': 0.70,
            'strategy': 'keyword',   # 关键词检索（错误信息精确匹配）
            'template': 'error_diagnosis'
        },
        'example': {
            'top_k': 4,
            'similarity_threshold': 0.75,
            'strategy': 'code_search',  # 代码检索
            'template': 'code_example'
        },
        'algorithm': {
            'top_k': 6,
            'similarity_threshold': 0.78,
            'strategy': 'semantic',
            'template': 'algorithm_explanation'
        },
        'general': {  # 默认配置
            'top_k': 5,
            'similarity_threshold': 0.75,
            'strategy': 'semantic',
            'template': 'general_answer'
        }
    }
    
    
    @staticmethod
    def _match_keywords(question: str, keyword_dict: Dict[str, List[str]]) -> Tuple[int, List[str]]:
        """
        匹配关键词
        
        Args:
            question: 问题文本
            keyword_dict: 关键词字典
            
        Returns:
            (匹配数量, 匹配到的关键词列表)
        """
        question_lower = question.lower()
        matched_keywords = []
        
        for category, keywords in keyword_dict.items():
            for keyword in keywords:
                if keyword.lower() in question_lower:
                    matched_keywords.append(keyword)
        
        return len(matched_keywords), matched_keywords
    
    
    @staticmethod
    def _calculate_confidence(match_count: int, question_length: int) -> float:
        """
        计算置信度
        
        Args:
            match_count: 匹配到的关键词数量
            question_length: 问题长度（字符数）
            
        Returns:
            置信度 (0-1)
            
        算法：
        - 基础分：匹配数量 * 0.25
        - 调整：考虑问题长度（短问题匹配更重要）
        - 上限：0.95
        """
        if match_count == 0:
            return 0.0
        
        # 基础置信度
        base_confidence = min(match_count * 0.25, 0.9)
        
        # 长度调整因子（问题越短，匹配越重要）
        length_factor = 1.0 if question_length < 20 else 0.9
        
        confidence = min(base_confidence * length_factor, 0.95)
        
        return confidence
    
    
    @staticmethod
    def classify(question: str) -> ClassificationResult:
        """
        分类问题类型
        
        Args:
            question: 用户问题
            
        Returns:
            ClassificationResult 对象
            
        示例:
            >>> result = QuestionClassifier.classify("什么是指针?")
            >>> print(result.question_type)  # 'concept'
            >>> print(result.confidence)      # 0.85
            >>> print(result.keywords)        # ['什么是']
        """
        if not question or not question.strip():
            return ClassificationResult(
                question_type='general',
                confidence=0.0,
                keywords=[],
                retrieval_params=QuestionClassifier.RETRIEVAL_CONFIGS['general']
            )
        
        question = question.strip()
        question_length = len(question)
        
        # ========== 1. 匹配各类别关键词 ==========
        results = {}
        
        # 概念类
        count, keywords = QuestionClassifier._match_keywords(
            question, 
            QuestionClassifier.CONCEPT_KEYWORDS
        )
        if count > 0:
            results['concept'] = {
                'count': count,
                'keywords': keywords,
                'confidence': QuestionClassifier._calculate_confidence(count, question_length)
            }
        
        # 语法类
        count, keywords = QuestionClassifier._match_keywords(
            question,
            QuestionClassifier.SYNTAX_KEYWORDS
        )
        if count > 0:
            results['syntax'] = {
                'count': count,
                'keywords': keywords,
                'confidence': QuestionClassifier._calculate_confidence(count, question_length)
            }
        
        # 错误诊断类
        count, keywords = QuestionClassifier._match_keywords(
            question,
            QuestionClassifier.ERROR_KEYWORDS
        )
        if count > 0:
            results['error'] = {
                'count': count,
                'keywords': keywords,
                'confidence': QuestionClassifier._calculate_confidence(count, question_length)
            }
        
        # 代码示例类
        count, keywords = QuestionClassifier._match_keywords(
            question,
            QuestionClassifier.EXAMPLE_KEYWORDS
        )
        if count > 0:
            results['example'] = {
                'count': count,
                'keywords': keywords,
                'confidence': QuestionClassifier._calculate_confidence(count, question_length)
            }
        
        # 算法实现类
        count, keywords = QuestionClassifier._match_keywords(
            question,
            QuestionClassifier.ALGORITHM_KEYWORDS
        )
        if count > 0:
            results['algorithm'] = {
                'count': count,
                'keywords': keywords,
                'confidence': QuestionClassifier._calculate_confidence(count, question_length)
            }
        
        # ========== 2. 选择最佳分类 ==========
        if not results:
            # 没有匹配到任何关键词，返回通用类别
            question_type = 'general'
            confidence = 0.5
            keywords = []
        else:
            # 选择置信度最高的类别
            best_type = max(results.items(), key=lambda x: x[1]['confidence'])
            question_type = best_type[0]
            confidence = best_type[1]['confidence']
            keywords = best_type[1]['keywords']
        
        # ========== 3. 特殊规则调整 ==========
        
        # 规则1：同时包含"如何"和"实现" -> 算法类
        if '如何' in question and ('实现' in question or 'implement' in question.lower()):
            if 'algorithm' in results:
                question_type = 'algorithm'
                confidence = max(confidence, 0.85)
        
        # 规则2：包含代码片段（```) -> 错误诊断或示例
        if '```' in question or 'error:' in question.lower():
            question_type = 'error'
            confidence = max(confidence, 0.80)
        
        # 规则3：纯"是什么"问题 -> 概念类
        if re.match(r'^.{1,10}(是什么|什么是|啥是)', question):
            question_type = 'concept'
            confidence = max(confidence, 0.90)
        
        # ========== 4. 获取检索参数 ==========
        retrieval_params = QuestionClassifier.RETRIEVAL_CONFIGS.get(
            question_type,
            QuestionClassifier.RETRIEVAL_CONFIGS['general']
        )
        
        # ========== 5. 构建结果 ==========
        result = ClassificationResult(
            question_type=question_type,
            confidence=confidence,
            keywords=keywords[:5],  # 最多返回5个关键词
            retrieval_params=retrieval_params
        )
        
        # 打印日志
        print(f"\n{'='*60}")
        print(f"🔍 问题分类结果:")
        print(f"   问题: {question}")
        print(f"   类型: {result.question_type}")
        print(f"   置信度: {result.confidence:.2f}")
        print(f"   关键词: {result.keywords}")
        print(f"   检索策略: {result.retrieval_params['strategy']}")
        print(f"   Top-K: {result.retrieval_params['top_k']}")
        print(f"   相似度阈值: {result.retrieval_params['similarity_threshold']}")
        print(f"{'='*60}\n")
        
        return result
    
    
    @staticmethod
    def batch_classify(questions: List[str]) -> List[ClassificationResult]:
        """
        批量分类问题
        
        Args:
            questions: 问题列表
            
        Returns:
            分类结果列表
        """
        return [QuestionClassifier.classify(q) for q in questions]
    
    
    @staticmethod
    def get_type_statistics(questions: List[str]) -> Dict[str, int]:
        """
        统计问题类型分布
        
        Args:
            questions: 问题列表
            
        Returns:
            类型统计字典 {'concept': 5, 'syntax': 3, ...}
        """
        results = QuestionClassifier.batch_classify(questions)
        
        stats = {}
        for result in results:
            question_type = result.question_type
            stats[question_type] = stats.get(question_type, 0) + 1
        
        return stats


# ========== 便捷函数 ==========

def classify_question(question: str) -> Dict:
    """
    便捷函数：分类单个问题
    
    Returns:
        字典格式的分类结果
    """
    result = QuestionClassifier.classify(question)
    return result.to_dict()


def get_retrieval_params(question: str) -> Dict:
    """
    便捷函数：获取检索参数
    
    Returns:
        检索参数字典
    """
    result = QuestionClassifier.classify(question)
    return result.retrieval_params


# ========== 测试代码 ==========

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 问题分类器测试")
    print("="*60)
    
    # 测试用例
    test_questions = [
        # 概念类
        "什么是指针?",
        "指针和引用的区别是什么?",
        
        # 语法类
        "如何定义一个数组?",
        "Python 中怎么创建字典?",
        
        # 错误诊断类
        "为什么我的代码报错 NameError?",
        "程序运行不了，提示 segmentation fault",
        
        # 代码示例类
        "给我一个链表的例子",
        "能展示一个冒泡排序的代码吗?",
        
        # 算法实现类
        "如何实现快速排序?",
        "用递归实现二分查找的步骤",
        
        # 混合类
        "如何实现一个栈，并给我示例代码",
    ]
    
    print("\n📝 测试分类结果:\n")
    
    for i, question in enumerate(test_questions, 1):
        result = QuestionClassifier.classify(question)
        print(f"{i}. {question}")
        print(f"   └─ 类型: {result.question_type} (置信度: {result.confidence:.2f})")
        print(f"   └─ 关键词: {result.keywords}")
        print()
    
    # 统计测试
    print("\n📊 类型统计:")
    stats = QuestionClassifier.get_type_statistics(test_questions)
    for qtype, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        print(f"   {qtype}: {count} 个")
    
    print("\n" + "="*60)
    print("✅ 测试完成")
    print("="*60 + "\n")