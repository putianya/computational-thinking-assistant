# -*- coding: utf-8 -*-
"""压测专用后端启动器：替换外部依赖，保证可稳定打压测。"""

import os
import sys
import types

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))


# 为压测场景提供最小桩件，避免导入 routes.knowledge 时依赖外部向量库
fake_chromadb = types.ModuleType("chromadb")


class _DummyCollection:
    def __init__(self):
        self.name = "dummy"
        self.metadata = {}

    def count(self):
        return 0

    def add(self, *args, **kwargs):
        return None

    def query(self, *args, **kwargs):
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}


class _DummyClient:
    def __init__(self, *args, **kwargs):
        self._c = _DummyCollection()

    def get_or_create_collection(self, *args, **kwargs):
        return self._c

    def create_collection(self, *args, **kwargs):
        self._c = _DummyCollection()
        return self._c

    def delete_collection(self, *args, **kwargs):
        self._c = _DummyCollection()


fake_chromadb.PersistentClient = _DummyClient

fake_chromadb_config = types.ModuleType("chromadb.config")


class _DummySettings:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


fake_chromadb_config.Settings = _DummySettings

fake_st = types.ModuleType("sentence_transformers")


class _DummySentenceTransformer:
    def __init__(self, *args, **kwargs):
        pass

    def to(self, _device):
        return self

    def eval(self):
        return self

    def get_sentence_embedding_dimension(self):
        return 3

    def encode(self, texts, convert_to_numpy=True, show_progress_bar=False):
        return [[0.1, 0.1, 0.1] for _ in texts]


fake_st.SentenceTransformer = _DummySentenceTransformer
fake_torch = types.ModuleType("torch")

sys.modules.setdefault("chromadb", fake_chromadb)
sys.modules.setdefault("chromadb.config", fake_chromadb_config)
sys.modules.setdefault("sentence_transformers", fake_st)
sys.modules.setdefault("torch", fake_torch)

from app import app
from extensions import ServiceRegistry
from models.user import User
from services.auth_service import AuthService


class _FakeLLMService:
    def chat_stream(self, user_message, session_id=None, max_context=None):
        yield "这是压测模拟回复。"


class _FakeCodeService:
    def analyze_code(self, code, analysis_type='full'):
        return {
            'success': True,
            'analysis_type': analysis_type,
            'score': 90,
            'level': 'A',
            'features': {
                'lines': code.count('\n') + 1,
                'chars': len(code),
                'has_main': 'main' in code,
                'complexity': 'low',
                'includes': ['stdio.h'],
                'functions': ['main'],
                'keywords': {'if': 0, 'for': 0, 'while': 0, 'switch': 0},
            },
            'syntax_check': {'valid': True, 'error_count': 0, 'errors': [], 'warnings': []},
            'ai_analysis': {'success': True, 'problems': [], 'suggestions': [], 'summary': '压测模拟分析完成'},
            'suggestions': ['保持函数职责单一'],
        }


def prepare_mock_server():
    ServiceRegistry.get_llm_service = classmethod(lambda cls: _FakeLLMService())
    ServiceRegistry.get_code_service = classmethod(lambda cls: _FakeCodeService())

    with app.app_context():
        exists = User.query.filter_by(username='load_user').first()
        if not exists:
            AuthService.register(
                username='load_user',
                password='123456',
                email='load_user@example.com',
                nickname='load_user',
            )


if __name__ == '__main__':
    prepare_mock_server()
    app.run(host='127.0.0.1', port=5010, debug=False)
