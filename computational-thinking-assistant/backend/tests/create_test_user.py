# -*- coding: utf-8 -*-
"""
创建测试用户 - 生成不同角色的测试账号
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from database import db
from models.user import User


def create_test_users():
    """创建测试用户（学生、教师、管理员）"""
    
    with app.app_context():
        print("=" * 60)
        print("🚀 开始创建测试用户...")
        print("=" * 60)
        
        # ========== 定义要创建的用户 ==========
        test_users = [
            {
                'username': 'student1',
                'password': '123456',
                'role': 'student',
                'nickname': '张三',
                'email': 'student1@example.com'
            },
            {
                'username': 'teacher1',
                'password': '123456',
                'role': 'teacher',
                'nickname': '李老师',
                'email': 'teacher1@example.com'
            },
            {
                'username': 'admin',
                'password': 'admin123',
                'role': 'admin',
                'nickname': '系统管理员',
                'email': 'admin@example.com'
            }
        ]
        
        created_count = 0
        skipped_count = 0
        
        # ========== 逐个创建用户 ==========
        for user_data in test_users:
            username = user_data['username']
            
            # 检查用户是否已存在
            existing_user = User.query.filter_by(username=username).first()
            
            if existing_user:
                print(f"\n⚠️  用户 '{username}' 已存在，跳过创建")
                print(f"   角色: {existing_user.get_role_display()}")
                print(f"   邮箱: {existing_user.email}")
                skipped_count += 1
                continue
            
            # 创建新用户
            try:
                user = User.create_with_role(
                    username=user_data['username'],
                    password=user_data['password'],
                    role=user_data['role'],
                    email=user_data['email'],
                    nickname=user_data['nickname']
                )
                
                print(f"\n✅ 创建用户: {username}")
                print(f"   角色: {user.get_role_display()}")
                print(f"   密码: {user_data['password']}")
                print(f"   邮箱: {user.email}")
                print(f"   昵称: {user.nickname}")
                
                created_count += 1
                
            except Exception as e:
                print(f"\n❌ 创建用户 '{username}' 失败: {e}")
                continue
        
        # ========== 打印汇总信息 ==========
        print("\n" + "=" * 60)
        print("📊 创建汇总")
        print("=" * 60)
        print(f"✅ 成功创建: {created_count} 个")
        print(f"⚠️  已存在跳过: {skipped_count} 个")
        print(f"📝 总计: {created_count + skipped_count} 个")
        
        if created_count > 0:
            print("\n" + "=" * 60)
            print("🔑 测试账号列表")
            print("=" * 60)
            
            # 查询并显示所有测试用户
            for user_data in test_users:
                user = User.query.filter_by(username=user_data['username']).first()
                if user:
                    print(f"\n【{user.get_role_display()}】")
                    print(f"   用户名: {user.username}")
                    print(f"   密码:   {user_data['password']}")
                    print(f"   邮箱:   {user.email}")
                    print(f"   昵称:   {user.nickname}")
                    print(f"   权限:   {', '.join(user.get_all_permissions()[:5])}...")
            
            print("\n" + "=" * 60)
            print("🎯 快速登录提示")
            print("=" * 60)
            print("学生账号: student1 / 123456")
            print("教师账号: teacher1 / 123456")
            print("管理员:   admin    / admin123")
            print("=" * 60)
        
        # ========== 显示权限矩阵（可选） ==========
        show_matrix = input("\n是否显示权限矩阵? (y/n): ").strip().lower()
        if show_matrix == 'y':
            print("\n" + "=" * 80)
            print("📋 权限矩阵")
            print("=" * 80)
            print(f"{'操作':<30} {'学生':<10} {'教师':<10} {'管理员':<10}")
            print("-" * 80)
            
            matrix = User.get_permission_matrix()
            
            # 按类别分组显示
            categories = {
                '基础功能': ['ask', 'view_knowledge', 'view_sessions', 'create_session'],
                '知识库管理': ['upload_doc', 'manage_knowledge', 'delete_knowledge', 'edit_knowledge', 'view_knowledge_stats'],
                '系统管理': ['manage_users', 'view_all_sessions', 'delete_user', 'change_user_role', 'view_system_stats']
            }
            
            for category, actions in categories.items():
                print(f"\n【{category}】")
                for action in actions:
                    if action in matrix:
                        info = matrix[action]
                        student_mark = '✓' if info['student'] else '✗'
                        teacher_mark = '✓' if info['teacher'] else '✗'
                        admin_mark = '✓' if info['admin'] else '✗'
                        print(f"  {info['name']:<28} {student_mark:<10} {teacher_mark:<10} {admin_mark:<10}")
            
            print("=" * 80)


if __name__ == '__main__':
    create_test_users()