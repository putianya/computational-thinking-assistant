# -*- coding: utf-8 -*-
"""
问题分类器模块（修复版）
"""
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
from config import Config


@dataclass
class ClassificationResult:
    """分类结果数据类"""
    question_type: str
    confidence: float
    keywords: List[str]
    retrieval_params: Dict
    needs_rag: bool = True
    threshold: float = None
    skip_reason: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'category': self.question_type,
            'type': self.question_type,
            'confidence': self.confidence,
            'keywords': self.keywords,
            'retrieval_params': self.retrieval_params,
            'top_k': self.retrieval_params.get('top_k', 5),
            'threshold': self.threshold,
            'needs_rag': self.needs_rag,
            'skip_reason': self.skip_reason,
            'has_threshold_suggestion': self.threshold is not None
        }


class QuestionClassifier:
    """问题分类器"""
    
    # ========== 闲聊关键词 ==========
    CHAT_KEYWORDS = {
        'greeting': [
            '你好', '您好', 'hello', 'hi', '嗨', '早上好', '下午好', '晚上好',
            '早安', '晚安', '在吗', '在不在', '你在吗'
        ],
        'thanks': [
            '谢谢', '感谢', 'thanks', 'thank you', '多谢', '非常感谢', '谢了'
        ],
        'goodbye': [
            '再见', '拜拜', 'bye', 'goodbye', '回见', '下次见'
        ],
        'chitchat': [
            '你是谁', '你叫什么', '你的名字', '介绍一下你自己',
            '你能做什么', '你会什么', '你有什么功能',
            '今天天气', '现在几点', '你好吗', '你怎么样'
        ],
        'simple_command': [
            '继续', 'continue', '接着说', '然后呢', '还有呢',
            '好的', 'ok', '明白了', '知道了', '懂了',
            '是的', '对', '没错', '嗯', '好'
        ],
        'simple_task': [
            '数到', '从.*数到', '算一下', '计算'
        ]
    }
    
    # ========== 概念类关键词 ==========
    CONCEPT_KEYWORDS = {
        'what': ['什么是', '啥是', '何为', '定义', '概念', '含义', 'what is', '解释一下', '介绍一下'],
        'why': ['为什么', '为何', '原因', '原理', 'why', '怎么会'],
        'difference': ['区别', '不同', '差异', 'difference', '对比', '比较', 'vs'],
    }
    
    # ========== 语法类关键词 ==========
    SYNTAX_KEYWORDS = {
        'how': ['如何', '怎么', '怎样', 'how to', 'how do'],
        'syntax': ['语法', '写法', '格式', 'syntax', '用法', '使用方法'],
        'declare': ['定义', '声明', '创建', 'define', 'declare', '初始化'],
    }
    
    # ========== 错误诊断类关键词 ==========
    ERROR_KEYWORDS = {
        'error': ['报错', '错误', 'error', 'bug', '异常', 'exception', '段错误'],
        'problem': ['出问题', '不行', '不对', '失败', 'failed', '不工作', '运行不了', '编译不过'],
        'debug': ['调试', 'debug', '找不到', '无法', 'cannot', '不能'],
    }
    
    # ========== 代码示例类关键词 ==========
    EXAMPLE_KEYWORDS = {
        'example': ['例子', '示例', 'example', '样例', 'sample', '演示', 'demo'],
        'code': ['代码', 'code', '程序', 'program'],
        'show': ['给我', '看看', 'show me', '展示', '写一个'],
    }
    
    # ========== 算法实现类关键词 ==========
    ALGORITHM_KEYWORDS = {
        'implement': ['实现', '实施', 'implement', '完成', '编写'],
        'algorithm': ['算法', 'algorithm', '排序', 'sort', '搜索', 'search', '遍历', '递归'],
        'steps': ['步骤', 'steps', '过程', 'process', '流程'],
    }
    
    # ========== 编程领域关键词 ==========
    PROGRAMMING_KEYWORDS = [
        # 语言名称
        'c语言', 'C语言', 'c', 'C',  # ⭐ 新增单个字母 'c'
        'c++', 'C++', 'cpp', 'CPP',
        'python', 'Python', 'java', 'Java',
        'javascript', 'JavaScript', 'js', 'JS',
        
        # C语言核心概念
        'main', 'printf', 'scanf', 'include', 'stdio',
        'stdlib', 'string.h', 'math.h',
        
        # 数据类型
        'int', 'char', 'float', 'double', 'void',
        'short', 'long', 'unsigned', 'signed',

        '指针', 'pointer', '数组', 'array', '函数', 'function',
        '变量', 'variable', '循环', 'loop', 'for', 'while',
        '条件', 'if', 'else', 'switch', '结构体', 'struct',
        'typedef', 'malloc', 'free', '内存', 'memory',
        '链表', '栈', '队列', '树', '图', '堆',
        '节点', 'node', '二叉树', '哈希', 'hash',
        '排序', '查找', '搜索', '递归', '迭代', '动态规划',
        '编译', '运行', '调试', 'debug', '报错', 'error',
        '语法', 'syntax', '代码', 'code', '程序', 'program',
        'c语言', 'c++', 'python', 'java',
    ]
    
    # ========== 检索参数配置 ==========
    RETRIEVAL_CONFIGS = {
        'concept': {'top_k': 5, 'threshold': 0.60, 'strategy': 'semantic', 'template': 'concept_explanation'},
        'syntax': {'top_k': 3, 'threshold': 0.65, 'strategy': 'hybrid', 'template': 'syntax_guide'},
        'error': {'top_k': 8, 'threshold': 0.50, 'strategy': 'keyword', 'template': 'error_diagnosis'},
        'example': {'top_k': 4, 'threshold': 0.58, 'strategy': 'code_search', 'template': 'code_example'},
        'algorithm': {'top_k': 6, 'threshold': 0.60, 'strategy': 'semantic', 'template': 'algorithm_explanation'},
        'general': {'top_k': 5, 'threshold': 0.70, 'strategy': 'semantic', 'template': 'general_answer'},
        'chat': {'top_k': 0, 'threshold': 1.0, 'strategy': 'none', 'template': 'chat_response'}
    }
    
    # ========== 辅助方法 ==========
    
    @staticmethod
    def _match_keywords(question: str, keyword_dict: Dict[str, List[str]]) -> Tuple[int, List[str]]:
        """匹配关键词"""
        question_lower = question.lower()
        matched_keywords = []
        
        for category, keywords in keyword_dict.items():
            for keyword in keywords:
                if keyword.lower() in question_lower:
                    matched_keywords.append(keyword)
        
        return len(matched_keywords), matched_keywords
    
    @staticmethod
    def _calculate_confidence(match_count: int, question_length: int) -> float:
        """计算置信度"""
        if match_count == 0:
            return 0.0
        
        base_confidence = min(match_count * 0.25, 0.9)
        length_factor = 1.0 if question_length < 20 else 0.9
        return min(base_confidence * length_factor, 0.95)
    
    @staticmethod
    def _contains_programming_topic(question: str) -> bool:
        """检查问题是否包含编程相关主题（宽松匹配）"""
        question_lower = question.lower()
        
        # 1. 关键词匹配
        for keyword in QuestionClassifier.PROGRAMMING_KEYWORDS:
            if keyword.lower() in question_lower:
                print(f"🔍 匹配到编程关键词: '{keyword}'")
                return True
        
        # 2. 模式匹配
        patterns = [
            r'什么是\s*\w*语言',   # "什么是C语言"
            r'\w*语言.*什么',       # "C语言是什么"
            r'如何.*编程',          # "如何编程"
            r'怎么.*写.*代码',      # "怎么写代码"
            r'程序.*怎么',          # "程序怎么写"
            r'语言.*特点',          # "C语言的特点"
        ]
        
        for pattern in patterns:
            if re.search(pattern, question_lower):
                print(f"🔍 匹配到编程模式: {pattern}")
                return True
        
        return False
    
    @staticmethod
    def _is_chat_question(question: str) -> Tuple[bool, str, str]:
        """
        检查是否是闲聊/问候类问题
        
        ⭐⭐⭐ 修复：确保所有路径都有返回值 ⭐⭐⭐
        """
        question_lower = question.lower().strip()
        question_length = len(question)
        
        # 1. 非常短的问题（< 5 字符）
        if question_length <= 5 and not QuestionClassifier._contains_programming_topic(question):
            simple_confirms = ['好', '嗯', 'ok', '是', '对', '没错', '行']
            if question_lower in simple_confirms:
                return True, 'simple_command', question_lower
        
        # 2. 匹配闲聊关键词
        for chat_type, keywords in QuestionClassifier.CHAT_KEYWORDS.items():
            for keyword in keywords:
                # 精确匹配
                if keyword.lower() == question_lower:
                    return True, chat_type, keyword
                
                # 正则模式
                if '.*' in keyword:
                    if re.search(keyword, question_lower):
                        return True, chat_type, keyword
                
                # 短问候匹配
                if question_length < 10 and keyword.lower() in question_lower:
                    if not QuestionClassifier._contains_programming_topic(question):
                        return True, chat_type, keyword
        
        # ⭐⭐⭐ 关键修复：确保返回默认值 ⭐⭐⭐
        return False, '', ''
    
    # ========== 主分类方法 ==========
    
    @staticmethod
    def classify(question: str) -> ClassificationResult:
        """分类问题类型"""
        
        # 空问题处理
        if not question or not question.strip():
            return ClassificationResult(
                question_type='general',
                confidence=0.5,
                keywords=[],
                retrieval_params=QuestionClassifier.RETRIEVAL_CONFIGS['general'],
                needs_rag=False,
                threshold=Config.SIMILARITY_THRESHOLD,
                skip_reason='空问题'
            )
        
        question = question.strip()
        question_length = len(question)
        
        # ========== 第一步：检测闲聊/问候 ==========
        is_chat, chat_type, chat_keyword = QuestionClassifier._is_chat_question(question)
        
        if is_chat:
            print(f"   💬 检测到闲聊类型: {chat_type} (关键词: {chat_keyword})")
            return ClassificationResult(
                question_type='chat',
                confidence=0.95,
                keywords=[chat_keyword] if chat_keyword else [],
                retrieval_params=QuestionClassifier.RETRIEVAL_CONFIGS['chat'],
                needs_rag=False,
                threshold=None,
                skip_reason=f'闲聊类问题（{chat_type}）'
            )
        
        # ========== 第二步：检测是否包含编程主题 ==========
        # ========== 第二步：检测编程主题 ==========
        has_programming_topic = QuestionClassifier._contains_programming_topic(question)
        
        if not has_programming_topic:
            # ⭐⭐⭐ 修复：即使没有明确的编程关键词，也可能需要 RAG ⭐⭐⭐
            # 检查是否包含"什么是"、"概念"等提示词
            if any(kw in question.lower() for kw in ['什么是', '什么', '概念', '定义', '解释']):
                print("🔍 检测到提问模式，尝试 RAG 检索")
                
                return ClassificationResult(
                    question_type='concept',
                    confidence=0.7,
                    keywords=['未知概念'],
                    retrieval_params=QuestionClassifier.RETRIEVAL_CONFIGS['concept'],
                    needs_rag=True,  # ⭐ 允许 RAG
                    threshold=0.65,
                    skip_reason=''
                )
            
            # 其他情况才跳过 RAG
            return ClassificationResult(
                question_type='general',
                confidence=0.9,
                keywords=[],
                retrieval_params=QuestionClassifier.RETRIEVAL_CONFIGS['general'],
                needs_rag=False,
                threshold=1.0,
                skip_reason='非编程相关问题'
            )
        
        # ========== 第三步：细分类 ==========
        results = {}
        
        # 概念类
        count, keywords = QuestionClassifier._match_keywords(
            question, QuestionClassifier.CONCEPT_KEYWORDS
        )
        if count > 0:
            results['concept'] = {
                'confidence': QuestionClassifier._calculate_confidence(count, question_length),
                'keywords': keywords
            }
        
        # 语法类
        count, keywords = QuestionClassifier._match_keywords(
            question, QuestionClassifier.SYNTAX_KEYWORDS
        )
        if count > 0:
            results['syntax'] = {
                'confidence': QuestionClassifier._calculate_confidence(count, question_length),
                'keywords': keywords
            }
        
        # 错误诊断类
        count, keywords = QuestionClassifier._match_keywords(
            question, QuestionClassifier.ERROR_KEYWORDS
        )
        if count > 0:
            results['error'] = {
                'confidence': QuestionClassifier._calculate_confidence(count, question_length),
                'keywords': keywords
            }
        
        # 代码示例类
        count, keywords = QuestionClassifier._match_keywords(
            question, QuestionClassifier.EXAMPLE_KEYWORDS
        )
        if count > 0:
            results['example'] = {
                'confidence': QuestionClassifier._calculate_confidence(count, question_length),
                'keywords': keywords
            }
        
        # 算法实现类
        count, keywords = QuestionClassifier._match_keywords(
            question, QuestionClassifier.ALGORITHM_KEYWORDS
        )
        if count > 0:
            results['algorithm'] = {
                'confidence': QuestionClassifier._calculate_confidence(count, question_length),
                'keywords': keywords
            }
        
        # ========== 第四步：选择最佳分类 ==========
        if not results:
            question_type = 'general'
            confidence = 0.5
            keywords = []
        else:
            best_type = max(results.items(), key=lambda x: x[1]['confidence'])
            question_type = best_type[0]
            confidence = best_type[1]['confidence']
            keywords = best_type[1]['keywords']
        
        # ========== 第五步：获取检索参数和阈值 ==========
        retrieval_params = QuestionClassifier.RETRIEVAL_CONFIGS.get(
            question_type,
            QuestionClassifier.RETRIEVAL_CONFIGS['general']
        ).copy()
        
        suggested_threshold = retrieval_params.get('threshold', Config.SIMILARITY_THRESHOLD)
        
        # ========== 第六步：决定是否需要 RAG ==========
        needs_rag = has_programming_topic
        skip_reason = '' if needs_rag else '无编程相关主题'
        
        return ClassificationResult(
            question_type=question_type,
            confidence=confidence,
            keywords=keywords,
            retrieval_params=retrieval_params,
            needs_rag=needs_rag,
            threshold=suggested_threshold,
            skip_reason=skip_reason
        )


# ========== 便捷函数 ==========

def classify_question(question: str) -> Dict:
    """便捷函数：分类单个问题"""
    result = QuestionClassifier.classify(question)
    return result.to_dict()


def get_retrieval_params(question: str) -> Dict:
    """便捷函数：获取检索参数"""
    result = QuestionClassifier.classify(question)
    return result.retrieval_params


def needs_rag_search(question: str) -> bool:
    """便捷函数：判断是否需要 RAG 检索"""
    result = QuestionClassifier.classify(question)
    return result.needs_rag


# ========== 测试代码 ==========

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 问题分类器测试")
    print("="*60)
    
    test_questions = [
        "你好",
        "谢谢",
        "什么是指针？",
        "如何定义一个数组？",
        "为什么会出现段错误？",
        "从1数到10",
        "今天天气怎么样",
    ]
    
    for q in test_questions:
        result = QuestionClassifier.classify(q)
        rag_status = "🔍 RAG" if result.needs_rag else "💬 跳过"
        print(f"\n{q}")
        print(f"   类型: {result.question_type} | {rag_status}")
        if result.needs_rag:
            print(f"   阈值: {result.threshold}")
        else:
            print(f"   原因: {result.skip_reason}")
    
    print("\n" + "="*60 + "\n")