# -*- coding: utf-8 -*-
"""Locust 压测脚本：覆盖登录、代码分析、流式问答三个关键接口。"""

from locust import HttpUser, between, task


class LearningAssistantUser(HttpUser):
    wait_time = between(0.2, 1.0)

    def on_start(self):
        self.token = None
        self.headers = {'Content-Type': 'application/json'}

        with self.client.post(
            '/api/auth/login',
            json={'username': 'load_user', 'password': '123456'},
            name='auth_login',
            catch_response=True,
        ) as resp:
            if resp.status_code == 200:
                body = resp.json()
                token = body.get('token')
                if token:
                    self.token = token
                    self.headers['Authorization'] = f'Bearer {token}'
                    resp.success()
                else:
                    resp.failure('missing token')
            else:
                resp.failure(f'login failed: {resp.status_code}')

    @task(2)
    def health_check(self):
        self.client.get('/api/test', name='api_test')

    @task(3)
    def code_analyze(self):
        if not self.token:
            return

        code = '#include <stdio.h>\nint main(){printf("hello");return 0;}'
        with self.client.post(
            '/api/code/analyze',
            json={'code': code, 'analysis_type': 'full'},
            headers=self.headers,
            name='code_analyze',
            catch_response=True,
        ) as resp:
            if resp.status_code == 200 and '"status":"success"' in resp.text.replace(' ', ''):
                resp.success()
            else:
                resp.failure(f'bad response: {resp.status_code}')

    @task(3)
    def chat_stream(self):
        if not self.token:
            return

        with self.client.post(
            '/api/chat/stream',
            json={'message': '请解释一下指针'},
            headers=self.headers,
            name='chat_stream',
            catch_response=True,
        ) as resp:
            if resp.status_code == 200 and '"type": "done"' in resp.text:
                resp.success()
            else:
                resp.failure(f'bad stream response: {resp.status_code}')
