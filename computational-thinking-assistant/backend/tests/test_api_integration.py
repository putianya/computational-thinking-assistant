# -*- coding: utf-8 -*-
"""API 集成测试（基于 Flask test_client，屏蔽外部LLM/向量依赖）。"""

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class _FakeLLMService:
    def chat_stream(self, user_message, session_id=None, max_context=None):
        yield "这是模拟回答。"


class _FakeCodeService:
    def analyze_code(self, code, analysis_type='full'):
        return {
            'success': True,
            'analysis_type': analysis_type,
            'score': 88,
            'level': 'B',
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
            'ai_analysis': {'success': True, 'problems': [], 'suggestions': [], 'summary': '模拟分析完成'},
            'suggestions': ['可以增加输入校验'],
        }


@pytest.fixture(scope='module')
def test_client():
    from app import app
    from extensions import ServiceRegistry
    from models.user import User
    from services.auth_service import AuthService

    # 用假的服务替换真实外部依赖
    ServiceRegistry.get_llm_service = classmethod(lambda cls: _FakeLLMService())
    ServiceRegistry.get_code_service = classmethod(lambda cls: _FakeCodeService())

    with app.app_context():
        existing = User.query.filter_by(username='integration_user').first()
        if not existing:
            AuthService.register(
                username='integration_user',
                password='123456',
                email='integration_user@example.com',
                nickname='integration_user',
            )

    with app.test_client() as client:
        yield client


def _login_and_get_token(client):
    resp = client.post(
        '/api/auth/login',
        json={'username': 'integration_user', 'password': '123456'},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['status'] == 'success'
    assert 'token' in data
    return data['token']


def test_auth_login_and_verify_profile(test_client):
    token = _login_and_get_token(test_client)

    profile_resp = test_client.get(
        '/api/user/profile',
        headers={'Authorization': f'Bearer {token}'},
    )
    assert profile_resp.status_code == 200
    profile = profile_resp.get_json()
    assert profile['status'] == 'success'
    assert profile['user']['username'] == 'integration_user'


def test_code_analyze_api(test_client):
    token = _login_and_get_token(test_client)
    code = '#include <stdio.h>\nint main(){printf("hi");return 0;}'

    resp = test_client.post(
        '/api/code/analyze',
        json={'code': code, 'analysis_type': 'full'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload['status'] == 'success'
    assert payload['data']['success'] is True
    assert payload['data']['score'] == 88


def test_chat_stream_api_sse(test_client):
    token = _login_and_get_token(test_client)

    resp = test_client.post(
        '/api/chat/stream',
        json={'message': '什么是指针？'},
        headers={'Authorization': f'Bearer {token}'},
    )

    assert resp.status_code == 200
    body = resp.data.decode('utf-8', errors='ignore')
    assert '"type": "session"' in body
    assert '"type": "content"' in body
    assert '"type": "done"' in body
