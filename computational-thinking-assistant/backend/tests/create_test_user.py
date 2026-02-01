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
            # 学生账号
            {
                'username': 'student1',
                'password': '123456',
                'role': 'student',
                'nickname': '张三',
                'email': 'student1@example.com'
            },
            {
                'username': 'student2',
                'password': '123456',
                'role': 'student',
                'nickname': '李四',
                'email': 'student2@example.com'
            },
            
            # 教师账号
            {
                'username': 'teacher1',
                'password': '123456',
                'role': 'teacher',
                'nickname': '王老师',
                'email': 'teacher1@example.com'
            },
            {
                'username': 'teacher2',
                'password': '123456',
                'role': 'teacher',
                'nickname': '刘老师',
                'email': 'teacher2@example.com'
            },
            
            # 管理员账号
            {
                'username': 'admin',
                'password': 'admin123',
                'role': 'admin',
                'nickname': '系统管理员',
                'email': 'admin@example.com'
            },
            {
                'username': 'admin2',
                'password': 'admin123',
                'role': 'admin',
                'nickname': '超级管理员',
                'email': 'admin2@example.com'
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
        
        if created_count > 0 or skipped_count > 0:
            print("\n" + "=" * 60)
            print("🔑 测试账号列表")
            print("=" * 60)
            
            # 按角色分组显示
            roles = {
                'student': '学生',
                'teacher': '教师',
                'admin': '管理员'
            }
            
            for role_key, role_display in roles.items():
                print(f"\n【{role_display}账号】")
                print("-" * 60)
                
                # 查询该角色的所有用户
                users = User.query.filter_by(role=role_key).all()
                
                if not users:
                    print("   暂无用户")
                    continue
                
                for user in users:
                    # 从 test_users 中找到原始密码
                    user_data = next(
                        (u for u in test_users if u['username'] == user.username), 
                        None
                    )
                    password = user_data['password'] if user_data else '******'
                    
                    print(f"\n   用户名: {user.username}")
                    print(f"   密码:   {password}")
                    print(f"   邮箱:   {user.email}")
                    print(f"   昵称:   {user.nickname}")
                    
                    # 显示前5个权限
                    permissions = user.get_all_permissions()
                    if len(permissions) > 5:
                        perm_display = ', '.join(permissions[:5]) + '...'
                    else:
                        perm_display = ', '.join(permissions)
                    print(f"   权限:   {perm_display}")
            
            print("\n" + "=" * 60)
            print("🎯 快速登录提示")
            print("=" * 60)
            print("\n学生账号:")
            print("  student1 / 123456  (张三)")
            print("  student2 / 123456  (李四)")
            
            print("\n教师账号:")
            print("  teacher1 / 123456  (王老师)")
            print("  teacher2 / 123456  (刘老师)")
            
            print("\n管理员账号:")
            print("  admin    / admin123  (系统管理员)")
            print("  admin2   / admin123  (超级管理员)")
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
                '基础功能': [
                    'ask', 'view_knowledge', 'view_sessions', 'create_session'
                ],
                '知识库管理': [
                    'upload_doc', 'manage_knowledge', 'delete_knowledge', 
                    'edit_knowledge', 'view_knowledge_stats'
                ],
                '系统管理': [
                    'manage_users', 'view_all_sessions', 'delete_user', 
                    'change_user_role', 'view_system_stats'
                ]
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
            
            print("\n" + "=" * 80)
            print("\n💡 权限说明:")
            print("   ✓ = 有权限")
            print("   ✗ = 无权限")
            print("=" * 80)


if __name__ == '__main__':
    create_test_users()