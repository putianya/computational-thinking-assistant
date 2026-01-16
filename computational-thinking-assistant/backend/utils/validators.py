"""
数据验证工具
职责: 验证请求数据的合法性
"""
from flask import request, jsonify
from functools import wraps

def validate_json_request(required_fields=None):
    """
    装饰器: 验证 JSON 请求
    
    Args:
        required_fields: 必需字段列表
        
    Usage:
        @validate_json_request(['message'])
        def chat():
            ...
    """
    if required_fields is None:
        required_fields = []
    
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # 检查 Content-Type
            if not request.is_json:
                return jsonify({
                    'status': 'error',
                    'message': '请求必须是 JSON 格式'
                }), 400
            
            # 获取数据
            data = request.get_json()
            
            # 检查必需字段
            for field in required_fields:
                if field not in data or not data[field]:
                    return jsonify({
                        'status': 'error',
                        'message': f'缺少必需字段: {field}'
                    }), 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

def validate_message_length(max_length=1000):
    """
    装饰器: 验证消息长度
    
    Args:
        max_length: 最大长度
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            data = request.get_json()
            message = data.get('message', '')
            
            if len(message) > max_length:
                return jsonify({
                    'status': 'error',
                    'message': f'消息长度不能超过 {max_length} 字符'
                }), 400
            
            return f(*args, **kwargs)
        return wrapper
    return decorator