# -*- coding: utf-8 -*-
"""
装饰器工具 - 登录验证、权限验证等
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


def require_permission(action):
    """
    权限验证装饰器
    
    Args:
        action: 权限名称（如 'upload_doc', 'manage_users'）
        
    用法:
        @app.route('/api/knowledge/upload', methods=['POST'])
        @login_required
        @require_permission('upload_doc')
        def upload_document():
            ...
    
    权限列表：
        - ask: 提问（所有角色）
        - view_knowledge: 查看知识库（所有角色）
        - upload_doc: 上传文档（教师、管理员）
        - manage_knowledge: 管理知识块（教师、管理员）
        - delete_knowledge: 删除知识块（教师、管理员）
        - edit_knowledge: 编辑知识块（教师、管理员）
        - view_knowledge_stats: 查看知识库统计（教师、管理员）
        - manage_users: 管理用户（管理员）
        - view_all_sessions: 查看所有会话（管理员）
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 1. 获取当前用户 ID（由 @login_required 设置）
            user_id = getattr(g, 'user_id', None)
            
            if not user_id:
                return jsonify({
                    'status': 'error',
                    'message': '用户未认证'
                }), 401
            
            # 2. 查询用户
            from models.user import User
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({
                    'status': 'error',
                    'message': '用户不存在'
                }), 404
            
            # 3. 检查用户是否激活
            if not user.is_active:
                return jsonify({
                    'status': 'error',
                    'message': '用户已被禁用'
                }), 403
            
            # 4. 检查权限
            if not user.has_permission(action):
                print(f"❌ 权限不足: 用户 {user.username}({user.role}) 缺少 {action} 权限")
                return jsonify({
                    'status': 'error',
                    'message': f'权限不足：需要 {action} 权限',
                    'required_permission': action,
                    'user_role': user.role,
                    'user_role_display': user.get_role_display()
                }), 403
            
            # 5. 权限通过，将用户对象存到 g（可选，方便后续使用）
            g.user = user
            
            print(f"✅ 权限验证通过: {user.username}({user.role}) -> {action}")
            
            # 6. 执行原函数
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_role(*roles):
    """
    角色验证装饰器（简化版，直接检查角色）
    
    Args:
        *roles: 允许的角色列表
        
    用法:
        @app.route('/api/admin/users', methods=['GET'])
        @login_required
        @require_role('admin')
        def get_all_users():
            ...
        
        # 或者允许多个角色
        @require_role('teacher', 'admin')
        def some_function():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 1. 获取当前用户 ID
            user_id = getattr(g, 'user_id', None)
            
            if not user_id:
                return jsonify({
                    'status': 'error',
                    'message': '用户未认证'
                }), 401
            
            # 2. 查询用户
            from models.user import User
            user = User.query.get(user_id)
            
            if not user:
                return jsonify({
                    'status': 'error',
                    'message': '用户不存在'
                }), 404
            
            # 3. 检查角色
            if user.role not in roles:
                print(f"❌ 角色不匹配: 用户 {user.username} 是 {user.role}，需要 {roles}")
                return jsonify({
                    'status': 'error',
                    'message': f'权限不足：需要 {", ".join(roles)} 角色',
                    'required_roles': list(roles),
                    'user_role': user.role
                }), 403
            
            # 4. 角色匹配，存储用户对象
            g.user = user
            
            print(f"✅ 角色验证通过: {user.username}({user.role})")
            
            # 5. 执行原函数
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator