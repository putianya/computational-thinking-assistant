# -*- coding: utf-8 -*-
"""向量服务单元测试（pytest + 依赖桩件）。"""

import importlib
import os
import sys
import types

import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class _FakeCollection:
    def __init__(self):
        self.name = "test_collection"
        self.metadata = {"hnsw:space": "cosine"}
        self._rows = []

    def add(self, documents, embeddings, metadatas, ids):
        for d, e, m, i in zip(documents, embeddings, metadatas, ids):
            self._rows.append({"id": i, "doc": d, "emb": e, "meta": m})

    def query(self, query_embeddings, n_results, include):
        # 固定返回一个高相似度和一个低相似度结果，覆盖阈值过滤逻辑
        limited = self._rows[:n_results]
        ids = [r["id"] for r in limited]
        docs = [r["doc"] for r in limited]
        metas = [r["meta"] for r in limited]
        distances = [0.2 if i == 0 else 1.6 for i in range(len(limited))]
        return {
            "ids": [ids],
            "documents": [docs],
            "metadatas": [metas],
            "distances": [distances],
        }

    def count(self):
        return len(self._rows)


class _FakePersistentClient:
    def __init__(self, path=None, settings=None):
        self._collection = _FakeCollection()

    def get_or_create_collection(self, name, metadata=None):
        return self._collection

    def create_collection(self, name, metadata=None):
        self._collection = _FakeCollection()
        return self._collection

    def delete_collection(self, name):
        self._collection = _FakeCollection()


class _FakeSentenceTransformer:
    def __init__(self, *args, **kwargs):
        pass

    def to(self, _device):
        return self

    def eval(self):
        return self

    def get_sentence_embedding_dimension(self):
        return 3

    def encode(self, texts, convert_to_numpy=True, show_progress_bar=False):
        embeddings = []
        for text in texts:
            length = float(len(text))
            embeddings.append([length, 1.0, 0.5])
        return np.array(embeddings)


def _load_vector_service_module(monkeypatch, tmp_path):
    fake_chromadb = types.ModuleType("chromadb")
    fake_chromadb.PersistentClient = _FakePersistentClient

    fake_chromadb_config = types.ModuleType("chromadb.config")

    class _FakeSettings:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    fake_chromadb_config.Settings = _FakeSettings

    fake_torch = types.ModuleType("torch")
    fake_st = types.ModuleType("sentence_transformers")
    fake_st.SentenceTransformer = _FakeSentenceTransformer

    monkeypatch.setitem(sys.modules, "chromadb", fake_chromadb)
    monkeypatch.setitem(sys.modules, "chromadb.config", fake_chromadb_config)
    monkeypatch.setitem(sys.modules, "torch", fake_torch)
    monkeypatch.setitem(sys.modules, "sentence_transformers", fake_st)

    from config import Config

    monkeypatch.setattr(Config, "CHROMA_PERSIST_DIR", str(tmp_path / "chromadb"))
    monkeypatch.setattr(Config, "SIMILARITY_THRESHOLD", 0.65)

    module = importlib.import_module("services.vector_service")
    module = importlib.reload(module)
    module._vector_service_instance = None
    return module


def test_add_documents_success(monkeypatch, tmp_path):
    module = _load_vector_service_module(monkeypatch, tmp_path)
    vector_service = module.get_vector_service()

    docs = [
        {"content": "指针用于存储地址", "source": "chapter1", "chunk_id": 101},
        {"content": "数组通过下标访问", "source": "chapter2", "chunk_id": 102},
    ]
    result = vector_service.add_documents(docs)

    assert result["success"] is True
    assert result["added_count"] == 2
    assert len(result["vector_ids"]) == 2
    assert vector_service.collection.count() == 2


def test_search_filters_by_similarity_threshold(monkeypatch, tmp_path):
    module = _load_vector_service_module(monkeypatch, tmp_path)
    vector_service = module.get_vector_service()
    vector_service.add_documents(
        [
            {"content": "指针是变量", "source": "c", "chunk_id": 201},
            {"content": "链表节点连接", "source": "ds", "chunk_id": 202},
        ]
    )

    results = vector_service.search("什么是指针", top_k=2)

    assert len(results) == 1
    assert results[0]["score"] >= 0.65
    assert results[0]["chunk_id"] == 201


def test_get_collection_info_returns_expected_schema(monkeypatch, tmp_path):
    module = _load_vector_service_module(monkeypatch, tmp_path)
    vector_service = module.get_vector_service()

    info = vector_service.get_collection_info()

    assert info["success"] is True
    assert info["count"] == 0
    assert info["embedding_dim"] == 3
    assert "metadata" in info
    