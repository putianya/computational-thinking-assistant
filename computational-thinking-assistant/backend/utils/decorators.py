# -*- coding: utf-8 -*-
"""
装饰器工具 - 登录验证等
"""
from functools import wraps
from flask import request, jsonify, g
from services.auth_service import AuthService


def login_required(f):
    """
    登录验证装饰器
    
    用法：
        @app.route('/api/user/profile')
        @login_required
        def get_profile():
            user_id = g.user_id  # 从装饰器中获取用户ID
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. 从请求头获取 Token
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'status': 'error',
                'message': '未登录，请先登录'
            }), 401
        
        # 2. 提取 Token（格式：Bearer <token>）
        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            return jsonify({
                'status': 'error',
                'message': 'Token 格式错误'
            }), 401
        
        # 3. 验证 Token
        verify_result = AuthService.verify_token(token)
        
        if not verify_result['valid']:
            return jsonify({
                'status': 'error',
                'message': verify_result['message']
            }), 401
        
        # 4. Token 有效，将用户信息存到 g 对象
        g.user_id = verify_result['user_id']
        g.username = verify_result['username']
        
        # 5. 调用原函数
        return f(*args, **kwargs)
    
    return decorated_function