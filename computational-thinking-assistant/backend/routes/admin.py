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


@admin_bp.route('/api/admin/users', methods=['POST'])
@login_required
@require_permission('manage_users')
def create_user():
    """创建新用户"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        nickname = data.get('nickname', '').strip()
        email = data.get('email', '').strip() or None
        role = data.get('role', 'student')
        is_active = data.get('is_active', True)

        if not username:
            return jsonify({'status': 'error', 'message': '用户名不能为空'}), 400
        if not password:
            return jsonify({'status': 'error', 'message': '密码不能为空'}), 400
        if role not in ['student', 'teacher', 'admin']:
            return jsonify({'status': 'error', 'message': '角色无效'}), 400
        if User.query.filter_by(username=username).first():
            return jsonify({'status': 'error', 'message': '用户名已存在'}), 400

        user = User(
            username=username,
            nickname=nickname or username,
            email=email,
            role=role,
            is_active=is_active
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        print(f"✅ 创建用户: {username} ({role})")
        return jsonify({'status': 'success', 'message': f'用户 {username} 创建成功', 'data': user.to_dict()}), 201

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'创建失败: {str(e)}'}), 500


@admin_bp.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@login_required
@require_permission('manage_users')
def update_user(user_id):
    """更新用户信息（昵称、邮箱、角色、状态、密码、师生归属）"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404

        data = request.get_json()

        if 'nickname' in data:
            user.nickname = data['nickname'].strip() or user.nickname
        if 'email' in data:
            user.email = data['email'].strip() or None
        if 'is_active' in data:
            if user_id == g.user_id and not data['is_active']:
                return jsonify({'status': 'error', 'message': '不能禁用自己'}), 400
            user.is_active = bool(data['is_active'])
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        if 'role' in data:
            new_role = data['role']
            if new_role not in ['student', 'teacher', 'admin']:
                return jsonify({'status': 'error', 'message': '角色无效'}), 400
            if user_id == g.user_id and new_role != user.role:
                return jsonify({'status': 'error', 'message': '不能修改自己的角色'}), 400
            user.role = new_role

        # 更新教师的学生列表（仅当 role 是 teacher）
        if 'student_ids' in data and user.role == 'teacher':
            student_ids = data['student_ids'] or []
            students = User.query.filter(
                User.id.in_(student_ids),
                User.role == 'student'
            ).all()
            user.students = students

        # 更新学生的教师列表（仅当 role 是 student）
        if 'teacher_ids' in data and user.role == 'student':
            teacher_ids = data['teacher_ids'] or []
            teachers = User.query.filter(
                User.id.in_(teacher_ids),
                User.role == 'teacher'
            ).all()
            user.teachers = teachers

        db.session.commit()
        print(f"✅ 更新用户: {user.username}")
        return jsonify({'status': 'success', 'message': f'用户 {user.username} 已更新', 'data': user.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'更新失败: {str(e)}'}), 500


@admin_bp.route('/api/admin/teachers', methods=['GET'])
@login_required
@require_permission('manage_users')
def get_all_teachers():
    """获取所有教师列表（用于分配学生）"""
    try:
        teachers = User.query.filter_by(role='teacher', is_active=True)\
            .order_by(User.username.asc()).all()
        return jsonify({
            'status': 'success',
            'data': [{'id': t.id, 'username': t.username, 'nickname': t.nickname or t.username} for t in teachers]
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
