# -*- coding: utf-8 -*-
"""
用户模型
"""
from datetime import datetime
from database import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """
    用户表
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    nickname = db.Column(db.String(80), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # ========== 🆕 角色权限字段 ==========
    role = db.Column(
        db.String(20), 
        default='student',
        index=True,
        nullable=False,
        comment='用户角色：student(学生), teacher(教师), admin(管理员)'
    )
    
    # 关系：一个用户有多个聊天会话
    chat_sessions = db.relationship('ChatSession', backref='user', lazy=True, cascade='all, delete-orphan')
    
    # ========== 🆕 角色权限常量 ==========
    ROLE_STUDENT = 'student'
    ROLE_TEACHER = 'teacher'
    ROLE_ADMIN = 'admin'
    
    # 权限定义（操作 -> 角色列表）
    PERMISSIONS = {
        # 基础功能（所有角色）
        'ask': ['student', 'teacher', 'admin'],                    # 提问
        'view_knowledge': ['student', 'teacher', 'admin'],         # 查看知识库
        'view_sessions': ['student', 'teacher', 'admin'],          # 查看自己的会话
        'create_session': ['student', 'teacher', 'admin'],         # 创建会话
        
        # 知识库管理（教师、管理员）
        'upload_doc': ['teacher', 'admin'],                        # 上传文档
        'manage_knowledge': ['teacher', 'admin'],                  # 管理知识块
        'delete_knowledge': ['teacher', 'admin'],                  # 删除知识块
        'edit_knowledge': ['teacher', 'admin'],                    # 编辑知识块
        'view_knowledge_stats': ['teacher', 'admin'],              # 查看知识库统计
        
        # 学习分析（教师、管理员）
        'view_analytics': ['teacher', 'admin'],                    # 查看学习分析
        
        # 用户管理（仅管理员）
        'manage_users': ['admin'],                                 # 管理用户
        'view_all_sessions': ['admin'],                            # 查看所有会话
        'delete_user': ['admin'],                                  # 删除用户
        'change_user_role': ['admin'],                             # 修改用户角色
        'view_system_stats': ['admin'],                            # 查看系统统计
    }
    
    # ========== 原有方法 ==========
    
    def set_password(self, password):
        """
        设置密码（加密存储）
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        验证密码
        
        Args:
            password: 明文密码
            
        Returns:
            bool: 密码是否正确
        """
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """
        转换为字典（用于 JSON 序列化）
        """
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nickname': self.nickname,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            # 🆕 添加角色信息
            'role': self.role,
            'role_display': self.get_role_display(),
            'permissions': self.get_all_permissions()
        }
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    # ========== 🆕 角色权限方法 ==========
    
    def has_permission(self, action):
        """
        检查用户是否有权限执行某操作
        
        Args:
            action: 操作名称（如 'upload_doc'）
            
        Returns:
            bool: 是否有权限
            
        示例:
            >>> user = User.query.get(1)
            >>> user.has_permission('upload_doc')
            True  # 如果是教师或管理员
            False # 如果是学生
        """
        # 检查用户是否激活
        if not self.is_active:
            return False
        
        # 获取该操作允许的角色列表
        allowed_roles = self.PERMISSIONS.get(action, [])
        
        # 判断用户角色是否在允许列表中
        return self.role in allowed_roles
    
    def has_any_permission(self, actions):
        """
        检查是否有任意一个权限
        
        Args:
            actions: 操作列表
            
        Returns:
            bool: 是否至少有一个权限
            
        示例:
            >>> user.has_any_permission(['upload_doc', 'manage_users'])
            True  # 如果有其中任意一个权限
        """
        return any(self.has_permission(action) for action in actions)
    
    def has_all_permissions(self, actions):
        """
        检查是否有所有权限
        
        Args:
            actions: 操作列表
            
        Returns:
            bool: 是否拥有所有权限
            
        示例:
            >>> user.has_all_permissions(['view_knowledge', 'upload_doc'])
            True  # 如果同时拥有两个权限
        """
        return all(self.has_permission(action) for action in actions)
    
    def get_all_permissions(self):
        """
        获取用户的所有权限列表
        
        Returns:
            list: 权限名称列表
            
        示例:
            >>> user.get_all_permissions()
            ['ask', 'view_knowledge', 'view_sessions', ...]
        """
        return [
            action 
            for action, allowed_roles in self.PERMISSIONS.items()
            if self.role in allowed_roles
        ]
    
    def is_student(self):
        """判断是否是学生"""
        return self.role == self.ROLE_STUDENT
    
    def is_teacher(self):
        """判断是否是教师"""
        return self.role == self.ROLE_TEACHER
    
    def is_admin(self):
        """判断是否是管理员"""
        return self.role == self.ROLE_ADMIN
    
    def set_role(self, new_role):
        """
        设置用户角色
        
        Args:
            new_role: 新角色（'student', 'teacher', 'admin'）
            
        Returns:
            bool: 是否成功
        """
        valid_roles = [self.ROLE_STUDENT, self.ROLE_TEACHER, self.ROLE_ADMIN]
        
        if new_role not in valid_roles:
            print(f"❌ 无效的角色: {new_role}")
            return False
        
        old_role = self.role
        self.role = new_role
        
        print(f"✅ 用户 {self.username} 角色变更: {old_role} -> {new_role}")
        
        try:
            db.session.commit()
            return True
        except Exception as e:
            print(f"❌ 角色变更失败: {e}")
            db.session.rollback()
            return False
    
    def get_role_display(self):
        """
        获取角色的中文显示名称
        
        Returns:
            str: 角色中文名
        """
        role_names = {
            self.ROLE_STUDENT: '学生',
            self.ROLE_TEACHER: '教师',
            self.ROLE_ADMIN: '管理员'
        }
        return role_names.get(self.role, '未知')
    
    @staticmethod
    def get_permission_matrix():
        """
        获取权限矩阵（用于文档/管理界面）
        
        Returns:
            dict: 权限矩阵
            {
                'ask': {
                    'name': '提问',
                    'roles': ['student', 'teacher', 'admin']
                },
                ...
            }
        """
        # 操作的中文名称
        action_names = {
            # 基础功能
            'ask': '提问',
            'view_knowledge': '查看知识库',
            'view_sessions': '查看自己的会话',
            'create_session': '创建会话',
            
            # 知识库管理
            'upload_doc': '上传文档',
            'manage_knowledge': '管理知识块',
            'delete_knowledge': '删除知识块',
            'edit_knowledge': '编辑知识块',
            'view_knowledge_stats': '查看知识库统计',
            
            # 学习分析
            'view_analytics': '查看学习分析',
            
            # 用户管理
            'manage_users': '管理用户',
            'view_all_sessions': '查看所有会话',
            'delete_user': '删除用户',
            'change_user_role': '修改用户角色',
            'view_system_stats': '查看系统统计',
        }
        
        matrix = {}
        for action, roles in User.PERMISSIONS.items():
            matrix[action] = {
                'name': action_names.get(action, action),
                'roles': roles,
                'student': 'student' in roles,
                'teacher': 'teacher' in roles,
                'admin': 'admin' in roles
            }
        
        return matrix
    
    @classmethod
    def create_with_role(cls, username, password, role='student', email=None, nickname=None):
        """
        创建带有指定角色的用户
        
        Args:
            username: 用户名
            password: 密码
            role: 角色（默认 'student'）
            email: 邮箱
            nickname: 昵称
            
        Returns:
            User: 创建的用户对象
        """
        # 验证角色
        valid_roles = [cls.ROLE_STUDENT, cls.ROLE_TEACHER, cls.ROLE_ADMIN]
        if role not in valid_roles:
            raise ValueError(f"无效的角色: {role}，必须是 {valid_roles} 之一")
        
        # 创建用户
        user = cls(
            username=username,
            email=email,
            nickname=nickname or username,
            role=role
        )
        user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            print(f"✅ 创建用户成功: {username} ({role})")
            return user
        except Exception as e:
            db.session.rollback()
            print(f"❌ 创建用户失败: {e}")
            raise