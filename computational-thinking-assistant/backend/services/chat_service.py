# -*- coding: utf-8 -*-
"""
聊天服务 - 管理会话和消息（数据库操作）
"""
from datetime import datetime
from database import db
from models.chat_session import ChatSession
from models.chat_message import ChatMessage
from config import Config
import uuid


class ChatService:
    """
    聊天服务类
    负责：会话管理、消息存储、数据库操作
    不负责：调用 AI（由 LLMService 负责）
    """
    
    # ========== 功能 1：获取用户的会话列表 ==========
    
    @staticmethod
    def get_user_sessions(user_id):
        """
        获取用户的所有会话（按更新时间倒序）
        
        Args:
            user_id: 用户 ID
        
        Returns:
            list: 会话列表
            [
                {"id": 3, "title": "当前对话", "is_active": True, "updated_at": "..."},
                {"id": 2, "title": "关于指针", "is_active": False, "updated_at": "..."},
            ]
        
        为什么要这个？
        └─ 前端侧边栏展示会话列表
        """
        try:
            sessions = ChatSession.query.filter_by(user_id=user_id)\
                .order_by(ChatSession.updated_at.desc())\
                .all()
            
            print(f"📋 用户 {user_id} 共有 {len(sessions)} 个会话")
            
            return [session.to_dict(include_messages=False) for session in sessions]
            
        except Exception as e:
            print(f"❌ 获取会话列表失败: {e}")
            return []
    
    # ========== 功能 2：获取/创建当前活跃会话 ==========
    
    @staticmethod
    def get_or_create_active_session(user_id):
        """
        获取用户的当前活跃会话，如果没有就创建一个
        
        Args:
            user_id: 用户 ID
        
        Returns:
            ChatSession: 活跃会话对象
        
        逻辑：
        1. 查找 is_active=True 的会话
        2. 如果找到，返回它
        3. 如果没找到，创建新会话并返回
        
        为什么需要这个？
        └─ 用户登录时调用，确保总有一个可用的会话
        """
        try:
            # 查找活跃会话
            active_session = ChatSession.query.filter_by(
                user_id=user_id,
                is_active=True
            ).first()
            
            if active_session:
                print(f"✅ 找到活跃会话: {active_session.session_id}")
                return active_session
            
            # 没有活跃会话，创建新的
            new_session = ChatSession(
                session_id=f"session_{uuid.uuid4().hex[:16]}",
                user_id=user_id,
                title=Config.DEFAULT_SESSION_TITLE,
                is_active=True
            )
            
            db.session.add(new_session)
            db.session.commit()
            
            print(f"✅ 创建新会话: {new_session.session_id}")
            return new_session
            
        except Exception as e:
            print(f"❌ 获取/创建会话失败: {e}")
            db.session.rollback()
            raise
    
    # ========== 功能 3：保存消息 ==========
    
    @staticmethod
    def save_message(session_id, role, content):
        """
        保存一条消息到指定会话
        
        Args:
            session_id: 会话 session_id（字符串）
            role: 'user' 或 'assistant'
            content: 消息内容
        
        Returns:
            ChatMessage: 保存的消息对象
        
        逻辑：
        1. 查找会话
        2. 使用 ChatSession.add_message() 保存消息
           └─ 自动处理：消息限制、标题生成、时间更新
        
        为什么在这里处理50条限制？
        └─ 统一管理，不容易遗漏
        """
        try:
            # 查找会话（通过 session_id 字符串）
            session = ChatSession.query.filter_by(session_id=session_id).first()
            
            if not session:
                raise ValueError(f"会话不存在: {session_id}")
            
            # 使用 ChatSession 的 add_message 方法
            # 它会自动处理：消息限制、标题生成、计数更新
            new_message = session.add_message(role, content)
            
            print(f"💾 保存消息: {role} - {content[:30]}... (会话: {session_id})")
            
            return new_message
            
        except Exception as e:
            print(f"❌ 保存消息失败: {e}")
            db.session.rollback()
            raise
    
    # ========== 功能 4：获取会话消息 ==========
    
    @staticmethod
    def get_session_messages(session_id, limit=50):
        """
        获取指定会话的消息
        
        Args:
            session_id: 会话 session_id（字符串）
            limit: 返回数量（默认50）
        
        Returns:
            list: 消息列表
            [
                {"role": "user", "content": "你好", "created_at": "..."},
                {"role": "assistant", "content": "你好！", "created_at": "..."},
            ]
        
        为什么要 limit？
        └─ 首次加载时可能只需要最近20条
           滚动加载更多时再请求更早的
        """
        try:
            # 查找会话
            session = ChatSession.query.filter_by(session_id=session_id).first()
            
            if not session:
                print(f"⚠️ 会话不存在: {session_id}")
                return []
            
            # 使用 ChatSession 的 get_messages 方法
            messages = session.get_messages(limit=limit)
            
            print(f"📬 获取会话消息: {session_id} (共 {len(messages)} 条)")
            
            return messages
            
        except Exception as e:
            print(f"❌ 获取消息失败: {e}")
            return []
    
    # ========== 功能 5：切换会话 ==========
    
    @staticmethod
    def switch_session(user_id, session_id):
        """
        切换到指定会话
        
        Args:
            user_id: 用户 ID
            session_id: 目标会话 session_id（字符串）
        
        Returns:
            dict: 会话信息及其消息
            {
                "session": {...},
                "messages": [...]
            }
        
        逻辑：
        1. 将用户所有会话的 is_active 设为 False
        2. 将指定会话的 is_active 设为 True
        3. 返回该会话及其消息
        
        为什么要这个？
        └─ 用户点击侧边栏的历史会话时调用
        """
        try:
            # 1. 查找目标会话
            target_session = ChatSession.query.filter_by(
                user_id=user_id,
                session_id=session_id
            ).first()
            
            if not target_session:
                raise ValueError(f"会话不存在或不属于该用户: {session_id}")
            
            # 2. 使用 ChatSession 的 set_active 方法
            # 它会自动处理：将其他会话设为非活跃
            target_session.set_active()
            
            # 3. 返回会话信息和消息
            result = {
                'session': target_session.to_dict(include_messages=False),
                'messages': target_session.get_messages()
            }
            
            print(f"🔄 切换到会话: {session_id}")
            
            return result
            
        except Exception as e:
            print(f"❌ 切换会话失败: {e}")
            db.session.rollback()
            raise
    
    # ========== 功能 6：归档当前会话并创建新会话 ==========
    
    @staticmethod
    def archive_and_create_new(user_id):
        """
        归档当前会话，创建新会话（清空聊天时调用）
        
        Args:
            user_id: 用户 ID
        
        Returns:
            ChatSession: 新创建的会话
        
        逻辑：
        1. 找到当前活跃会话
        2. 设置 is_active = False（归档）
        3. 创建新会话，is_active = True
        4. 返回新会话
        
        为什么叫"归档"而不是"删除"？
        └─ 历史会话要保留，用户可以查看
        """
        try:
            # 1. 归档当前活跃会话
            current_session = ChatSession.query.filter_by(
                user_id=user_id,
                is_active=True
            ).first()
            
            if current_session:
                current_session.is_active = False
                db.session.commit()
                print(f"📦 归档会话: {current_session.session_id}")
            
            # 2. 创建新会话
            new_session = ChatSession(
                session_id=f"session_{uuid.uuid4().hex[:16]}",
                user_id=user_id,
                title=Config.DEFAULT_SESSION_TITLE,
                is_active=True
            )
            
            db.session.add(new_session)
            db.session.commit()
            
            print(f"✅ 创建新会话: {new_session.session_id}")
            
            return new_session
            
        except Exception as e:
            print(f"❌ 归档并创建新会话失败: {e}")
            db.session.rollback()
            raise
    
    # ========== 功能 7：获取 AI 上下文 ==========
    
    @staticmethod
    def get_context_for_ai(session_id, limit=10):
        """
        获取发送给 AI 的上下文消息（OpenAI API 格式）
        
        Args:
            session_id: 会话 session_id（字符串）
            limit: 上下文长度（默认10条）
        
        Returns:
            list: OpenAI 格式的消息列表
            [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."},
            ]
        
        为什么单独写这个函数？
        └─ AI 只需要最近 N 条消息
           和展示给用户的可能不一样（用户看50条，AI看10条）
        """
        try:
            # 查找会话
            session = ChatSession.query.filter_by(session_id=session_id).first()
            
            if not session:
                print(f"⚠️ 会话不存在: {session_id}，返回空上下文")
                return []
            
            # 获取最近 N 条消息
            messages = session.get_messages(limit=limit)
            
            # 转换为 OpenAI API 格式（只保留 role 和 content）
            context = [
                {
                    'role': msg['role'],
                    'content': msg['content']
                }
                for msg in messages
            ]
            
            print(f"🧠 获取 AI 上下文: {session_id} (最近 {len(context)} 条消息)")
            
            return context
            
        except Exception as e:
            print(f"❌ 获取 AI 上下文失败: {e}")
            return []
    
    # ========== 辅助方法：获取会话详情 ==========
    
    @staticmethod
    def get_session_detail(session_id):
        """
        获取会话详情（包含消息）
        
        Args:
            session_id: 会话 session_id（字符串）
        
        Returns:
            dict: 会话详情
        """
        try:
            session = ChatSession.query.filter_by(session_id=session_id).first()
            
            if not session:
                return None
            
            return session.to_dict(include_messages=True)
            
        except Exception as e:
            print(f"❌ 获取会话详情失败: {e}")
            return None
    
    # ========== 辅助方法：删除会话 ==========
    
    @staticmethod
    def delete_session(user_id, session_id):
        """
        删除指定会话（包括所有消息）
        
        Args:
            user_id: 用户 ID（用于权限验证）
            session_id: 会话 session_id（字符串）
        
        Returns:
            bool: 是否删除成功
        """
        try:
            session = ChatSession.query.filter_by(
                user_id=user_id,
                session_id=session_id
            ).first()
            
            if not session:
                print(f"⚠️ 会话不存在或无权限: {session_id}")
                return False
            
            # 删除会话（级联删除所有消息）
            db.session.delete(session)
            db.session.commit()
            
            print(f"🗑️ 删除会话: {session_id}")
            
            return True
            
        except Exception as e:
            print(f"❌ 删除会话失败: {e}")
            db.session.rollback()
            return False