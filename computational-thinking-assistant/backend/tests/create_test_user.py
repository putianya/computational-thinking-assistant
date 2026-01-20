# -*- coding: utf-8 -*-
"""
创建测试用户
"""
from app import app
from database import db
from models.user import User

def create_test_user():
    """创建测试用户"""
    with app.app_context():
        # 检查用户是否已存在
        existing_user = User.query.filter_by(username='admin').first()
        
        if existing_user:
            print(f"⚠️ 用户 'admin' 已存在")
            print(f"   ID: {existing_user.id}")
            print(f"   Email: {existing_user.email}")
            print(f"   创建时间: {existing_user.created_at}")
            
            # 可选：重置密码
            response = input("\n是否重置密码为 'admin123'? (y/n): ")
            if response.lower() == 'y':
                existing_user.set_password('admin123')
                db.session.commit()
                print("✅ 密码已重置为 'admin123'")
            return
        
        # 创建新用户
        print("📝 创建新用户...")
        user = User(
            username='admin',
            email='admin@example.com',
            nickname='管理员'
        )
        user.set_password('admin123')
        
        db.session.add(user)
        db.session.commit()
        
        print("=" * 60)
        print("✅ 测试用户创建成功！")
        print(f"   用户名: admin")
        print(f"   密码:   admin123")
        print(f"   邮箱:   admin@example.com")
        print(f"   昵称:   管理员")
        print("=" * 60)

if __name__ == '__main__':
    create_test_user()