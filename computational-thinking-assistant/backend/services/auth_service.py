# -*- coding: utf-8 -*-
"""
认证服务 - 处理用户注册、登录、Token 管理
"""
import jwt
from datetime import datetime, timedelta
from database import db
from models.user import User
from config import Config


class AuthService:
    """认证服务类"""
    
    # JWT 配置
    JWT_SECRET_KEY = Config.SECRET_KEY
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24
    
    @staticmethod
    def register(username, password, email=None, nickname=None):
        """
        用户注册
        """
        try:
            # 检查用户名是否已存在
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                return {
                    'success': False,
                    'message': '用户名已存在'
                }
            
            # 检查邮箱是否已被使用
            if email:
                existing_email = User.query.filter_by(email=email).first()
                if existing_email:
                    return {
                        'success': False,
                        'message': '邮箱已被使用'
                    }
            
            # 创建新用户
            new_user = User(
                username=username,
                email=email,
                nickname=nickname or username
            )
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            print(f"✅ 用户注册成功: {username}")
            
            return {
                'success': True,
                'message': '注册成功',
                'user': new_user.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 用户注册失败: {str(e)}")
            return {
                'success': False,
                'message': f'注册失败: {str(e)}'
            }
    
    @staticmethod
    def login(username, password):
        """
        用户登录（整合验证和 Token 生成）
        """
        # 验证用户
        auth_result = AuthService.authenticate_user(username, password)
        
        if not auth_result['success']:
            return auth_result
        
        user = auth_result['user']
        
        # 生成 Token
        token = AuthService.generate_token(user.id, user.username)
        
        if not token:
            return {
                'success': False,
                'message': 'Token 生成失败'
            }
        
        return {
            'success': True,
            'message': '登录成功',
            'token': token,
            'user': user.to_dict()
        }
    
    @staticmethod
    def authenticate_user(username, password):
        """
        用户登录验证
        """
        try:
            user = User.query.filter_by(username=username).first()
            
            if not user:
                return {
                    'success': False,
                    'message': '用户名或密码错误',
                    'user': None
                }
            
            if not user.is_active:
                return {
                    'success': False,
                    'message': '账户已被禁用',
                    'user': None
                }
            
            if not user.check_password(password):
                return {
                    'success': False,
                    'message': '用户名或密码错误',
                    'user': None
                }
            
            # 更新最后登录时间
            user.last_login = datetime.now()
            db.session.commit()
            
            print(f"✅ 用户验证成功: {username}")
            
            return {
                'success': True,
                'message': '验证成功',
                'user': user
            }
            
        except Exception as e:
            print(f"❌ 用户验证失败: {str(e)}")
            return {
                'success': False,
                'message': f'验证失败: {str(e)}',
                'user': None
            }
    
    @staticmethod
    def generate_token(user_id, username):
        """
        生成 JWT Token
        """
        try:
            payload = {
                'user_id': user_id,
                'username': username,
                'exp': datetime.utcnow() + timedelta(hours=AuthService.JWT_EXPIRATION_HOURS),
                'iat': datetime.utcnow()
            }
            
            token = jwt.encode(
                payload,
                AuthService.JWT_SECRET_KEY,
                algorithm=AuthService.JWT_ALGORITHM
            )
            
            return token
            
        except Exception as e:
            print(f"❌ Token 生成失败: {str(e)}")
            return None
    
    @staticmethod
    def verify_token(token):
        """
        验证 JWT Token
        """
        try:
            payload = jwt.decode(
                token,
                AuthService.JWT_SECRET_KEY,
                algorithms=[AuthService.JWT_ALGORITHM]
            )
            
            return {
                'valid': True,
                'user_id': payload.get('user_id'),
                'username': payload.get('username'),
                'message': 'Token 有效'
            }
            
        except jwt.ExpiredSignatureError:
            return {
                'valid': False,
                'message': 'Token 已过期'
            }
        except jwt.InvalidTokenError:
            return {
                'valid': False,
                'message': 'Token 无效'
            }
        except Exception as e:
            return {
                'valid': False,
                'message': f'Token 验证失败: {str(e)}'
            }