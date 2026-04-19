# -*- coding: utf-8 -*-
"""RAG 智能降级鲁棒性测试（pytest 断言版）。"""

import importlib
import os
import sys
import types

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class _FakeVectorService:
    def __init__(self, scores):
        self.scores = scores
        self.called = 0

    def search(self, query, top_k=None, threshold=None):
        self.called += 1
        rows = []
        for idx, score in enumerate(self.scores, 1):
            rows.append(
                {
                    "id": f"v_{idx}",
                    "text": f"知识块{idx}",
                    "score": score,
                    "metadata": {"chunk_id": idx},
                    "chunk_id": idx,
                }
            )
        return rows


def _load_llm_module(monkeypatch):
    fake_openai = types.ModuleType("openai")

    class _DummyOpenAI:
        def __init__(self, *args, **kwargs):
            pass

    fake_openai.OpenAI = _DummyOpenAI

    fake_vector_service = types.ModuleType("services.vector_service")
    fake_vector_service.get_vector_service = lambda: _FakeVectorService([])

    fake_chat_service = types.ModuleType("services.chat_service")

    class _DummyChatService:
        @staticmethod
        def get_context_for_ai(session_id):
            return []

        @staticmethod
        def save_message(session_id, role, content, referenced_chunks=None):
            return None

    fake_chat_service.ChatService = _DummyChatService

    fake_knowledge_chunk = types.ModuleType("models.knowledge_chunk")

    class _DummyKnowledgeChunk:
        @staticmethod
        def batch_increment_retrieved(chunk_ids):
            return None

    fake_knowledge_chunk.KnowledgeChunk = _DummyKnowledgeChunk

    monkeypatch.setitem(sys.modules, "openai", fake_openai)
    monkeypatch.setitem(sys.modules, "services.vector_service", fake_vector_service)
    monkeypatch.setitem(sys.modules, "services.chat_service", fake_chat_service)
    monkeypatch.setitem(sys.modules, "models.knowledge_chunk", fake_knowledge_chunk)

    module = importlib.import_module("services.llm_service")
    return importlib.reload(module)


def _new_service(module, scores):
    svc = object.__new__(module.LLMService)
    svc.model = "mock-model"
    svc.vector_service = _FakeVectorService(scores)
    svc.RAG_HIGH_CONFIDENCE = 0.80
    svc.RAG_MEDIUM_CONFIDENCE = 0.60
    return svc


def test_rag_high_confidence_mode(monkeypatch):
    module = _load_llm_module(monkeypatch)
    service = _new_service(module, [0.92, 0.70])

    messages, referenced = service._build_messages("什么是指针？", session_id=None)

    assert len(messages) >= 3
    assert "必须优先使用" in messages[0]["content"]
    assert referenced == [1, 2]


def test_rag_medium_confidence_mode(monkeypatch):
    module = _load_llm_module(monkeypatch)
    service = _new_service(module, [0.66])

    messages, referenced = service._build_messages("C语言中如何使用指针访问数组元素？", session_id=None)

    assert len(messages) >= 3
    assert "可能相关" in messages[0]["content"]
    assert referenced == [1]


def test_rag_low_confidence_fallback_mode(monkeypatch):
    module = _load_llm_module(monkeypatch)
    service = _new_service(module, [0.35])

    messages, referenced = service._build_messages("C语言指针如何避免野指针？", session_id=None)

    assert len(messages) >= 2
    assert ("暂无相关内容" in messages[0]["content"]) or ("暂无收录" in messages[0]["content"])
    assert referenced == [1]


def test_chat_question_skips_rag_search(monkeypatch):
    module = _load_llm_module(monkeypatch)
    service = _new_service(module, [0.95])

    messages, _ = service._build_messages("你好", session_id=None)

    assert service.vector_service.called == 0
    assert "必须优先使用" not in messages[0]["content"]