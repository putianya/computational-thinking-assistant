# -*- coding: utf-8 -*-
"""
文本预处理模块 - RAG 功能支持

功能：
1. 问题清洗 - 提高向量检索准确率
2. 作业识别 - 防止直接给出答案
3. 敏感词过滤 - 确保系统安全
"""

import re
from typing import Dict, List, Tuple


class TextProcessor:
    """文本预处理类"""
    
    # ========== 1. 作业检测关键词库 ==========
    HOMEWORK_KEYWORDS = [
        # 直接要求类
        "帮我写", "帮写", "代写", "完成作业",
        "完整代码", "全部代码", "整个程序",
        
        # 题目特征类
        "编写一个程序", "实现一个程序", "写一个程序",
        "编程实现", "代码实现", "用代码实现",
        
        # 作业相关
        "作业", "习题", "练习题", "课后题",
        "第几题", "第几章", "第几节",
    ]
    
    # ========== 2. 敏感词库 ==========
    SENSITIVE_KEYWORDS = [
        # 政治敏感（示例，实际应更全面）
        # 注意：这里只是示例，实际部署时需要完善
        
        # 违法内容
        "黄赌毒", "诈骗", "盗窃", "暴力",
        
        # 不当言论
        "攻击", "辱骂", "歧视",
    ]
    
    # ========== 3. 标点符号映射表 ==========
    PUNCTUATION_MAP = {
        # 中文标点 -> 英文标点
        '，': ',',
        '。': '.',
        '！': '!',
        '？': '?',
        '；': ';',
        '：': ':',
        '（': '(',
        '）': ')',
        '【': '[',
        '】': ']',
        '《': '<',
        '》': '>',
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
    }
    
    
    @staticmethod
    def clean_question(text: str) -> str:
        """
        清洗用户输入的问题
        
        Args:
            text: 原始问题文本
            
        Returns:
            清洗后的文本
            
        示例:
            >>> clean_question("指针是什么？？？   ")
            "指针是什么?"
        """
        if not text:
            return ""
        
        # 1. 去除首尾空格
        text = text.strip()
        
        # 2. 统一中英文标点
        for cn_punct, en_punct in TextProcessor.PUNCTUATION_MAP.items():
            text = text.replace(cn_punct, en_punct)
        
        # 3. 去除多余空格（多个空格变一个）
        text = re.sub(r'\s+', ' ', text)
        
        # 4. 去除重复标点符号
        # "???" -> "?"
        # "!!!" -> "!"
        text = re.sub(r'([?.!])\1+', r'\1', text)
        
        # 5. 去除特殊字符（保留中文、英文、数字、常用标点）
        text = re.sub(r'[^\w\s,.!?;:()\[\]<>\'"-]', '', text)
        
        return text
    
    
    @staticmethod
    def is_homework_question(text: str) -> Tuple[bool, str]:
        """
        识别是否是作业题
        
        Args:
            text: 问题文本
            
        Returns:
            (是否作业题, 匹配到的关键词)
            
        示例:
            >>> is_homework_question("帮我写一个排序程序")
            (True, "帮我写")
            
            >>> is_homework_question("什么是指针?")
            (False, "")
        """
        if not text:
            return False, ""
        
        # 转小写进行匹配
        text_lower = text.lower()
        
        # 检查每个关键词
        for keyword in TextProcessor.HOMEWORK_KEYWORDS:
            if keyword in text_lower:
                print(f"⚠️ 检测到作业关键词: '{keyword}'")
                return True, keyword
        
        # 正则检测题目模式
        # 如: "第1题"、"第一章第3题"
        if re.search(r'第\s*[0-9一二三四五六七八九十]+\s*题', text):
            print(f"⚠️ 检测到题目编号模式")
            return True, "题目编号"
        
        return False, ""
    
    
    @staticmethod
    def contains_sensitive_content(text: str) -> Tuple[bool, List[str]]:
        """
        检测敏感内容
        
        Args:
            text: 待检测文本
            
        Returns:
            (是否包含敏感词, 匹配到的敏感词列表)
            
        示例:
            >>> contains_sensitive_content("正常的问题")
            (False, [])
            
            >>> contains_sensitive_content("包含敏感词的内容")
            (True, ["敏感词"])
        """
        if not text:
            return False, []
        
        text_lower = text.lower()
        matched_keywords = []
        
        # 检查每个敏感词
        for keyword in TextProcessor.SENSITIVE_KEYWORDS:
            if keyword in text_lower:
                matched_keywords.append(keyword)
        
        if matched_keywords:
            print(f"🚨 检测到敏感内容: {matched_keywords}")
            return True, matched_keywords
        
        return False, []
    
    
    @staticmethod
    def preprocess_for_retrieval(text: str) -> str:
        """
        为向量检索预处理文本
        
        Args:
            text: 原始问题
            
        Returns:
            适合向量检索的文本
            
        处理流程:
        1. 清洗问题
        2. 转小写（提高匹配率）
        3. 去除停用词（可选）
        """
        # 1. 清洗
        text = TextProcessor.clean_question(text)
        
        # 2. 转小写（英文部分）
        # 保留中文不变
        result = []
        for char in text:
            if 'A' <= char <= 'Z':
                result.append(char.lower())
            else:
                result.append(char)
        
        return ''.join(result)
    
    
    @staticmethod
    def analyze_question(text: str) -> Dict:
        """
        综合分析问题
        
        Args:
            text: 原始问题
            
        Returns:
            分析结果字典
            {
                'original': 原始文本,
                'cleaned': 清洗后文本,
                'for_retrieval': 用于检索的文本,
                'is_homework': 是否作业题,
                'homework_keyword': 匹配的作业关键词,
                'has_sensitive': 是否包含敏感词,
                'sensitive_words': 敏感词列表,
                'should_reject': 是否应拒绝回答
            }
        """
        # 1. 清洗文本
        cleaned = TextProcessor.clean_question(text)
        
        # 2. 检测作业
        is_homework, hw_keyword = TextProcessor.is_homework_question(cleaned)
        
        # 3. 检测敏感词
        has_sensitive, sensitive_words = TextProcessor.contains_sensitive_content(cleaned)
        
        # 4. 生成检索文本
        retrieval_text = TextProcessor.preprocess_for_retrieval(cleaned)
        
        # 5. 判断是否应拒绝
        should_reject = has_sensitive  # 包含敏感词则拒绝
        
        result = {
            'original': text,
            'cleaned': cleaned,
            'for_retrieval': retrieval_text,
            'is_homework': is_homework,
            'homework_keyword': hw_keyword,
            'has_sensitive': has_sensitive,
            'sensitive_words': sensitive_words,
            'should_reject': should_reject
        }
        
        print(f"\n{'='*60}")
        print(f"📝 问题分析结果:")
        print(f"   原始文本: {result['original']}")
        print(f"   清洗后: {result['cleaned']}")
        print(f"   检索用: {result['for_retrieval']}")
        print(f"   作业题: {'是' if result['is_homework'] else '否'} ({hw_keyword})")
        print(f"   敏感词: {'有' if result['has_sensitive'] else '无'} ({sensitive_words})")
        print(f"   应拒绝: {'是' if result['should_reject'] else '否'}")
        print(f"{'='*60}\n")
        
        return result


# ========== 便捷函数 ==========

def clean_question(text: str) -> str:
    """便捷函数：清洗问题"""
    return TextProcessor.clean_question(text)


def is_homework_question(text: str) -> bool:
    """便捷函数：检测作业"""
    is_hw, _ = TextProcessor.is_homework_question(text)
    return is_hw


def contains_sensitive_content(text: str) -> bool:
    """便捷函数：检测敏感词"""
    has_sensitive, _ = TextProcessor.contains_sensitive_content(text)
    return has_sensitive


def analyze_question(text: str) -> Dict:
    """便捷函数：综合分析"""
    return TextProcessor.analyze_question(text)


# ========== 测试代码 ==========

if __name__ == "__main__":
    # 测试用例
    test_cases = [
        "指针是什么？？？   ",
        "帮我写一个冒泡排序程序",
        "请问Python的列表和元组有什么区别?",
        "第3章第5题怎么做",
        "什么是计算思维？",
    ]
    
    print("\n🧪 文本预处理测试\n")
    
    for i, question in enumerate(test_cases, 1):
        print(f"\n{'─'*60}")
        print(f"测试 {i}: {question}")
        result = analyze_question(question)