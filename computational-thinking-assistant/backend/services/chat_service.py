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
            user_id: 用户ID
            session_id: 目标会话ID
            
        Returns:
            dict: 包含会话信息和消息列表
        """
        try:
            print(f"🔄 切换会话: {session_id}, 用户: {user_id}")
            
            # 1. 验证会话所有权
            target_session = ChatSession.query.filter_by(
                session_id=session_id,
                user_id=user_id
            ).first()
            
            if not target_session:
                raise ValueError("会话不存在或无权访问")
            
            # 2. ⭐⭐⭐ 手动更新所有会话状态（最可靠的方式）⭐⭐⭐
            # 先将所有会话设为非活跃
            all_sessions = ChatSession.query.filter_by(user_id=user_id).all()
            for session in all_sessions:
                if session.id == target_session.id:
                    session.is_active = True
                    session.updated_at = datetime.now()
                else:
                    session.is_active = False
            
            # 3. 一次性提交
            db.session.commit()
            
            # 4. ⭐ 重新查询目标会话，确保获取最新状态
            db.session.refresh(target_session)
            
            # 5. 获取消息
            messages = ChatMessage.query.filter_by(
                session_id=target_session.id
            ).order_by(ChatMessage.created_at.asc()).all()
            
            print(f"✅ 切换成功，消息数: {len(messages)}")
            
            return {
                'session': {
                    'session_id': target_session.session_id,
                    'title': target_session.title,
                    'is_active': target_session.is_active,
                    'created_at': target_session.created_at.isoformat(),
                    'updated_at': target_session.updated_at.isoformat(),
                    'message_count': len(messages)
                },
                'messages': [
                    {
                        'role': msg.role,
                        'content': msg.content,
                        'created_at': msg.created_at.isoformat()
                    }
                    for msg in messages
                ]
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 切换会话失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
   
    
    # ========== 功能 7：获取 AI 上下文 ==========
    
    @staticmethod
    def get_context_for_ai(session_id, limit=None):
        """
        获取发送给 AI 的上下文消息（OpenAI API 格式）
        
        Args:
            session_id: 会话 session_id（字符串）
            limit: ⭐ 已废弃，永远返回全部消息
        
        Returns:
            list: OpenAI 格式的消息列表
        """
        try:
            # 查找会话
            session = ChatSession.query.filter_by(session_id=session_id).first()
            
            if not session:
                print(f"⚠️ 会话不存在: {session_id}")
                return []
            
            # ⭐⭐⭐ 修改：获取全部消息（不再限制） ⭐⭐⭐
            messages = session.get_messages(limit=None)  # ⭐ 传入 None 表示全部
            
            # 转换为 OpenAI API 格式
            context = [
                {
                    'role': msg['role'],
                    'content': msg['content']
                }
                for msg in messages
            ]
            
            print(f"🧠 获取 AI 上下文: {session_id} (全部 {len(context)} 条消息)")
            
            return context
            
        except Exception as e:
            print(f"❌ 获取 AI 上下文失败: {e}")
            return []
    
    # ========== 辅助方法：获取会话详情 ==========
    
    @staticmethod
    def get_session_detail(session_id, user_id):  # ⭐ 确保有两个参数
        """
        获取会话详情
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            ChatSession 对象或 None
        """
        try:
            # 查询会话，确保属于指定用户
            session = ChatSession.query.filter_by(
                session_id=session_id,
                user_id=user_id
            ).first()
            
            return session
            
        except Exception as e:
            print(f"❌ 获取会话详情失败: {str(e)}")
            return None
    
    # ========== 辅助方法：删除会话 ==========
    
    @staticmethod
    def delete_session(session_id, user_id):  # ⭐ 确保有两个参数
        """
        删除会话及其所有消息
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            bool: 删除是否成功
        """
        try:
            # 1. 验证会话所有权
            session = ChatSession.query.filter_by(
                session_id=session_id,
                user_id=user_id
            ).first()
            
            if not session:
                print(f"❌ 会话不存在: {session_id}")
                return False
            
            # 2. 删除该会话的所有消息
            ChatMessage.query.filter_by(session_id=session.id).delete()
            print(f"✅ 已删除会话 {session_id} 的所有消息")
            
            # 3. 删除会话
            db.session.delete(session)
            db.session.commit()
            print(f"✅ 已删除会话: {session_id}")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 删除会话失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    # ⭐ 新增：重命名会话方法
    @staticmethod
    def rename_session(session_id, user_id, new_title):
        """
        重命名会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            new_title: 新标题
            
        Returns:
            ChatSession: 更新后的会话对象，如果失败返回 None
        """
        try:
            # 验证会话所有权
            session = ChatSession.query.filter_by(
                session_id=session_id,
                user_id=user_id
            ).first()
            
            if not session:
                print(f"❌ 会话不存在或无权修改: {session_id}")
                return None
            
            # 更新标题
            old_title = session.title
            session.title = new_title
            session.updated_at = datetime.now()
            
            db.session.commit()
            
            print(f"✅ 会话重命名成功: '{old_title}' -> '{new_title}'")
            
            return session
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 重命名会话失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    @staticmethod
    def archive_and_create_new(user_id):
        """
        归档当前活跃会话并创建新会话
        
        Args:
            user_id: 用户ID
            
        Returns:
            dict: 新会话信息
        """
        try:
            import uuid
            from datetime import datetime
            
            print(f"📦 归档当前会话并创建新会话，用户ID: {user_id}")
            
            # 1. ⭐⭐⭐ 查询并逐个更新（最可靠）⭐⭐⭐
            active_sessions = ChatSession.query.filter_by(
                user_id=user_id,
                is_active=True
            ).all()
            
            for session in active_sessions:
                session.is_active = False
                session.updated_at = datetime.now()
                print(f"   归档会话: {session.session_id}")
            
            # 2. 创建新会话
            new_session_id = f"session_{uuid.uuid4().hex[:16]}"
            new_session = ChatSession(
                session_id=new_session_id,
                user_id=user_id,
                title="新对话",
                is_active=True,
                message_count=0
            )
            
            db.session.add(new_session)
            
            # 3. 一次性提交所有更改
            db.session.commit()
            
            # 4. ⭐ 刷新新会话对象
            db.session.refresh(new_session)
            
            print(f"✅ 新会话已创建: {new_session_id}")
            
            return {
                'session_id': new_session.session_id,
                'title': new_session.title,
                'is_active': new_session.is_active,
                'created_at': new_session.created_at.isoformat(),
                'updated_at': new_session.updated_at.isoformat(),
                'message_count': 0
            }
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 创建新会话失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return None