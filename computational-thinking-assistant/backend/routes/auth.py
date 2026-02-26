# -*- coding: utf-8 -*-
"""
认证路由 Blueprint
包含：register, login, logout, verify_token, get_user_profile
"""
import traceback
from flask import Blueprint, request, jsonify, g
from models.user import User
from services.auth_service import AuthService
from utils.decorators import login_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        nickname = data.get('nickname')

        if not username or not password:
            return jsonify({'status': 'error', 'message': '用户名和密码不能为空'}), 400

        result = AuthService.register(username, password, email, nickname)

        if result['success']:
            return jsonify({
                'status': 'success',
                'message': result['message'],
                'user': result['user']
            }), 201
        else:
            return jsonify({'status': 'error', 'message': result['message']}), 400

    except Exception as e:
        print(f"❌ 注册错误: {e}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'注册失败: {str(e)}'}), 500


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        print("\n" + "=" * 60)
        print("🔍 收到登录请求")

        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            print("❌ 用户名或密码为空")
            return jsonify({'status': 'error', 'message': '用户名和密码不能为空'}), 400

        print(f"👤 尝试登录用户: {username}")
        result = AuthService.login(username, password)

        if result['success']:
            print(f"✅ 登录成功: {username}")
            return jsonify({
                'status': 'success',
                'message': result['message'],
                'token': result['token'],
                'user': result['user']
            }), 200
        else:
            print(f"❌ 登录失败: {result['message']}")
            return jsonify({'status': 'error', 'message': result['message']}), 401

    except Exception as e:
        print(f"💥 登录异常: {e}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'登录失败: {str(e)}'}), 500


@auth_bp.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    """
    用户退出登录

    说明：
    - 目前采用 JWT 无状态认证，Token 存储在前端
    - 后端无需维护 Token 黑名单（除非需要强制失效）
    - 前端清除 localStorage 即可完成登出
    - 此接口主要用于记录登出日志和数据统计

    返回格式：
    {
        "status": "success",
        "message": "退出成功"
    }
    """
    try:
        user_id = g.user_id
        user = User.query.get(user_id)

        if not user:
            return jsonify({
                'status': 'error',
                'message': '用户不存在'
            }), 404

        username = user.username

        print("\n" + "=" * 60)
        print(f"👋 用户退出登录")
        print(f"   用户ID: {user_id}")
        print(f"   用户名: {username}")
        print(f"   角色: {user.get_role_display()}")
        print("=" * 60 + "\n")

        return jsonify({
            'status': 'success',
            'message': '退出成功'
        }), 200

    except Exception as e:
        print(f"❌ 退出登录失败: {e}")
        traceback.print_exc()

        return jsonify({
            'status': 'error',
            'message': f'退出失败: {str(e)}'
        }), 500


@auth_bp.route('/api/auth/verify', methods=['POST'])
def verify_token():
    """验证 Token"""
    try:
        data = request.get_json()
        token = data.get('token')

        if not token:
            return jsonify({'status': 'error', 'message': 'Token 不能为空'}), 400

        result = AuthService.verify_token(token)

        if result['valid']:
            return jsonify({
                'status': 'success',
                'message': result['message'],
                'user_id': result['user_id'],
                'username': result['username']
            }), 200
        else:
            return jsonify({'status': 'error', 'message': result['message']}), 401

    except Exception as e:
        print(f"❌ Token 验证错误: {e}")
        return jsonify({'status': 'error', 'message': f'验证失败: {str(e)}'}), 500


@auth_bp.route('/api/user/profile', methods=['GET'])
@login_required
def get_user_profile():
    """获取用户信息（需要登录）"""
    try:
        user = User.query.get(g.user_id)

        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404

        return jsonify({'status': 'success', 'user': user.to_dict()}), 200

    except Exception as e:
        print(f"❌ 获取用户信息错误: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
