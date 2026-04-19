# -*- coding: utf-8 -*-
"""文本预处理模块单元测试（pytest 断言版）。"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.text_processor import TextProcessor


def test_clean_question_normalizes_spaces_and_punctuation():
    cases = [
        ("指针是什么？？？   ", "指针是什么?"),
        ("Python   列表   有哪些方法？", "Python 列表 有哪些方法?"),
        ("什么是《算法导论》？", "什么是<算法导论>?"),
    ]

    for raw, expected in cases:
        assert TextProcessor.clean_question(raw) == expected


def test_is_homework_question_detects_keyword_and_pattern():
    is_hw, keyword = TextProcessor.is_homework_question("帮我写一个排序程序")
    assert is_hw is True
    assert keyword == "帮我写"

    is_hw, keyword = TextProcessor.is_homework_question("第3题怎么做")
    assert is_hw is True
    assert keyword in ["题目编号", "第几题"]

    is_hw, keyword = TextProcessor.is_homework_question("什么是指针?")
    assert is_hw is False
    assert keyword == ""


def test_contains_sensitive_content_flags_keywords():
    has_sensitive, words = TextProcessor.contains_sensitive_content("这里包含诈骗和暴力内容")
    assert has_sensitive is True
    assert "诈骗" in words
    assert "暴力" in words

    has_sensitive, words = TextProcessor.contains_sensitive_content("什么是计算思维?")
    assert has_sensitive is False
    assert words == []


def test_analyze_question_returns_consistent_flags():
    result = TextProcessor.analyze_question("帮我写一个冒泡排序程序？？？")
    assert result["original"] == "帮我写一个冒泡排序程序？？？"
    assert result["cleaned"] == "帮我写一个冒泡排序程序?"
    assert result["is_homework"] is True
    assert result["has_sensitive"] is False
    assert result["should_reject"] is False
