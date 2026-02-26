# -*- coding: utf-8 -*-
"""
管理员路由 Blueprint
包含：users CRUD, role, status
"""
import traceback
from flask import Blueprint, request, jsonify, g
from database import db
from models.user import User
from utils.decorators import login_required, require_permission

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/api/admin/users', methods=['GET'])
@login_required
@require_permission('manage_users')
def get_all_users():
    """获取所有用户列表（权限：仅管理员）"""
    try:
        users = User.query.order_by(User.created_at.desc()).all()

        print(f"📋 查询用户列表: 共 {len(users)} 个用户")

        return jsonify({
            'status': 'success',
            'data': {
                'users': [user.to_dict() for user in users],
                'total': len(users)
            }
        }), 200

    except Exception as e:
        print(f"❌ 获取用户列表失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取用户列表失败: {str(e)}'
        }), 500


@admin_bp.route('/api/admin/users/<int:user_id>/role', methods=['PUT'])
@login_required
@require_permission('change_user_role')
def change_user_role(user_id):
    """
    修改用户角色（权限：需要 change_user_role 权限）

    请求格式：
    {
        "role": "teacher"  // student | teacher | admin
    }
    """
    try:
        data = request.get_json()
        new_role = data.get('role')

        if not new_role:
            return jsonify({
                'status': 'error',
                'message': '请提供新角色'
            }), 400

        valid_roles = ['student', 'teacher', 'admin']
        if new_role not in valid_roles:
            return jsonify({
                'status': 'error',
                'message': f'无效的角色，可选值: {", ".join(valid_roles)}'
            }), 400

        if user_id == g.user_id:
            return jsonify({
                'status': 'error',
                'message': '不能修改自己的角色'
            }), 400

        user = User.query.get(user_id)

        if not user:
            return jsonify({
                'status': 'error',
                'message': '用户不存在'
            }), 404

        old_role = user.role

        success = user.set_role(new_role)

        if success:
            print(f"✅ 用户 {user.username} 角色已更新: {old_role} -> {new_role}")

            return jsonify({
                'status': 'success',
                'message': f'用户 {user.username} 角色已更新为 {user.get_role_display()}',
                'data': user.to_dict()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': '角色更新失败'
            }), 500

    except Exception as e:
        print(f"❌ 修改用户角色失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'修改用户角色失败: {str(e)}'
        }), 500


@admin_bp.route('/api/admin/users/<int:user_id>/status', methods=['PUT'])
@login_required
@require_permission('manage_users')
def toggle_user_status(user_id):
    """
    启用/禁用用户（权限：需要 manage_users 权限）

    请求格式：
    {
        "is_active": false  // true | false
    }
    """
    try:
        data = request.get_json()
        is_active = data.get('is_active')

        if is_active is None:
            return jsonify({
                'status': 'error',
                'message': '请提供 is_active 参数'
            }), 400

        if user_id == g.user_id:
            return jsonify({
                'status': 'error',
                'message': '不能禁用自己的账号'
            }), 400

        user = User.query.get(user_id)

        if not user:
            return jsonify({
                'status': 'error',
                'message': '用户不存在'
            }), 404

        user.is_active = is_active
        db.session.commit()

        action = '启用' if is_active else '禁用'
        print(f"✅ 用户 {user.username} 已被{action}")

        return jsonify({
            'status': 'success',
            'message': f'用户 {user.username} 已被{action}',
            'data': user.to_dict()
        }), 200

    except Exception as e:
        print(f"❌ 切换用户状态失败: {e}")
        db.session.rollback()
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'切换用户状态失败: {str(e)}'
        }), 500


@admin_bp.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
@require_permission('delete_user')
def delete_user(user_id):
    """删除用户（危险操作，权限：需要 delete_user 权限）"""
    try:
        if user_id == g.user_id:
            return jsonify({
                'status': 'error',
                'message': '不能删除自己的账号'
            }), 400

        user = User.query.get(user_id)

        if not user:
            return jsonify({
                'status': 'error',
                'message': '用户不存在'
            }), 404

        username = user.username

        db.session.delete(user)
        db.session.commit()

        print(f"✅ 用户 {username} 已被删除")

        return jsonify({
            'status': 'success',
            'message': f'用户 {username} 已被删除'
        }), 200

    except Exception as e:
        print(f"❌ 删除用户失败: {e}")
        db.session.rollback()
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'删除用户失败: {str(e)}'
        }), 500
