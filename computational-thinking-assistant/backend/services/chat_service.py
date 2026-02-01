# -*- coding: utf-8 -*-
"""
聊天服务 - 管理会话和消息（数据库操作）
"""
import uuid
import traceback
from datetime import datetime
from database import db
from models.chat_session import ChatSession
from models.chat_message import ChatMessage
from config import Config


class ChatService:
    """聊天服务类"""
    
    # ========== 功能 1：获取用户的会话列表 ==========
    
    @staticmethod
    def get_user_sessions(user_id):
        """获取用户的所有会话"""
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
        """获取或创建活跃会话"""
        try:
            active_session = ChatSession.query.filter_by(
                user_id=user_id,
                is_active=True
            ).first()
            
            if active_session:
                print(f"✅ 找到活跃会话: {active_session.session_id}")
                return active_session
            
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
    def save_message(session_id, role, content, referenced_chunks=None):
        """保存聊天消息"""
        try:
            session = ChatSession.query.filter_by(session_id=session_id).first()
            
            if not session:
                print(f"⚠️ 会话不存在: {session_id}")
                return None
            
            message = ChatMessage(
                session_id=session.id,
                role=role,
                content=content
            )
            
            if referenced_chunks and len(referenced_chunks) > 0:
                print(f"💾 保存引用关系: {len(referenced_chunks)} 个知识块")
                chunk_ids = []
                for chunk_data in referenced_chunks:
                    if isinstance(chunk_data, dict):
                        chunk_id = chunk_data.get('id')
                    else:
                        chunk_id = chunk_data
                    if chunk_id:
                        chunk_ids.append(chunk_id)
                if chunk_ids:
                    message.set_referenced_chunks(chunk_ids)
            
            session.message_count = ChatMessage.query.filter_by(
                session_id=session.id
            ).count() + 1
            session.updated_at = datetime.now()
            
            if session.message_count == 1 and role == 'user':
                session.title = content[:30] + ('...' if len(content) > 30 else '')
            
            db.session.add(message)
            db.session.commit()
            
            print(f"✅ 消息已保存 (ID: {message.id}, 会话: {session.session_id})")
            return message
            
        except Exception as e:
            print(f"❌ 保存消息失败: {e}")
            db.session.rollback()
            traceback.print_exc()
            return None
    
    # ========== ⭐⭐⭐ 功能 4：获取会话消息（修复排序）⭐⭐⭐ ==========
    
    @staticmethod
    def get_session_messages(session_id, limit=None):
        """
        获取会话消息
        
        ⭐⭐⭐ 关键：确保按 created_at 升序排列（最早的在前）⭐⭐⭐
        """
        try:
            session = ChatSession.query.filter_by(session_id=session_id).first()
            
            if not session:
                print(f"⚠️ 会话不存在: {session_id}")
                return []
            
            # ⭐⭐⭐ 修复：始终按 created_at 升序排列 ⭐⭐⭐
            query = ChatMessage.query.filter_by(session_id=session.id)\
                .order_by(ChatMessage.created_at.asc())  # ⭐ 升序：最早的在前
            
            if limit:
                # 如果有限制，取最新的 N 条，但仍需保持时间顺序
                total = ChatMessage.query.filter_by(session_id=session.id).count()
                if total > limit:
                    # 跳过前面的，只取最后 limit 条
                    query = ChatMessage.query.filter_by(session_id=session.id)\
                        .order_by(ChatMessage.created_at.asc())\
                        .offset(total - limit)\
                        .limit(limit)
            
            messages = query.all()
            
            print(f"📬 获取会话消息: {session_id} (共 {len(messages)} 条)")
            
            # 调试：打印消息顺序
            if messages:
                print(f"   第一条: [{messages[0].role}] {messages[0].content[:20]}...")
                print(f"   最后条: [{messages[-1].role}] {messages[-1].content[:20]}...")
            
            return [msg.to_dict() for msg in messages]
            
        except Exception as e:
            print(f"❌ 获取消息失败: {e}")
            traceback.print_exc()
            return []
    
    # ========== ⭐⭐⭐ 功能 5：切换会话（修复排序）⭐⭐⭐ ==========
    
    @staticmethod
    def switch_session(user_id, session_id):
        """
        切换会话
        
        ⭐⭐⭐ 关键：确保消息按时间升序返回 ⭐⭐⭐
        """
        try:
            print(f"🔄 切换会话: {session_id}, 用户: {user_id}")
            
            target_session = ChatSession.query.filter_by(
                session_id=session_id,
                user_id=user_id
            ).first()
            
            if not target_session:
                raise ValueError(f"会话不存在: {session_id}")
            
            # 更新所有会话状态
            all_sessions = ChatSession.query.filter_by(user_id=user_id).all()
            for session in all_sessions:
                session.is_active = (session.id == target_session.id)
                session.updated_at = datetime.now()
            
            db.session.commit()
            db.session.refresh(target_session)
            
            # ⭐⭐⭐ 修复：按 created_at 升序获取消息 ⭐⭐⭐
            messages = ChatMessage.query.filter_by(
                session_id=target_session.id
            ).order_by(ChatMessage.created_at.asc()).all()  # ⭐ 升序：最早的在前
            
            print(f"✅ 切换成功，消息数: {len(messages)}")
            
            # 调试：打印消息顺序
            if messages:
                print(f"   第一条: [{messages[0].role}] {messages[0].content[:20]}...")
                print(f"   最后条: [{messages[-1].role}] {messages[-1].content[:20]}...")
            
            return {
                'session': target_session.to_dict(),
                'messages': [msg.to_dict() for msg in messages]
            }
            
        except Exception as e:
            print(f"❌ 切换会话失败: {e}")
            db.session.rollback()
            raise
    
    # ========== 功能 6：获取 AI 上下文 ==========
    
    @staticmethod
    def get_context_for_ai(session_id, limit=None):
        """获取发送给 AI 的上下文消息"""
        try:
            session = ChatSession.query.filter_by(session_id=session_id).first()
            
            if not session:
                print(f"⚠️ 会话不存在: {session_id}")
                return []
            
            # ⭐ 按 created_at 升序查询
            query = ChatMessage.query.filter_by(session_id=session.id)\
                .order_by(ChatMessage.created_at.asc())
            
            if limit:
                total = query.count()
                if total > limit:
                    query = ChatMessage.query.filter_by(session_id=session.id)\
                        .order_by(ChatMessage.created_at.desc())\
                        .limit(limit)
                    messages = list(reversed(query.all()))
                else:
                    messages = query.all()
            else:
                messages = query.all()
            
            context = []
            for msg in messages:
                context.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            print(f"🧠 获取 AI 上下文: {session_id} (全部 {len(context)} 条消息)")
            return context
            
        except Exception as e:
            print(f"❌ 获取上下文失败: {e}")
            traceback.print_exc()
            return []
    
    # ========== 其他辅助方法 ==========
    
    @staticmethod
    def get_session_detail(session_id, user_id):
        """获取会话详情"""
        try:
            session = ChatSession.query.filter_by(
                session_id=session_id,
                user_id=user_id
            ).first()
            return session
        except Exception as e:
            print(f"❌ 获取会话详情失败: {e}")
            return None
    
    @staticmethod
    def delete_session(session_id, user_id):
        """删除会话"""
        try:
            session = ChatSession.query.filter_by(
                session_id=session_id,
                user_id=user_id
            ).first()
            
            if not session:
                return False
            
            ChatMessage.query.filter_by(session_id=session.id).delete()
            db.session.delete(session)
            db.session.commit()
            
            print(f"✅ 会话已删除: {session_id}")
            return True
            
        except Exception as e:
            print(f"❌ 删除会话失败: {e}")
            db.session.rollback()
            return False
    
    @staticmethod
    def rename_session(session_id, user_id, new_title):
        """重命名会话"""
        try:
            session = ChatSession.query.filter_by(
                session_id=session_id,
                user_id=user_id
            ).first()
            
            if not session:
                return None
            
            session.title = new_title
            session.updated_at = datetime.now()
            db.session.commit()
            
            print(f"✅ 会话已重命名: {session_id} -> {new_title}")
            return session
            
        except Exception as e:
            print(f"❌ 重命名会话失败: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def archive_and_create_new(user_id):
        """
        归档当前会话，创建新会话
        
        流程：
        1. 将当前用户所有会话设为非活跃（归档）
        2. 创建新的活跃会话
        3. 返回新会话信息
        
        Args:
            user_id: 用户 ID
            
        Returns:
            dict: 新会话信息
        """
        try:
            import uuid
            from datetime import datetime
            
            print(f"\n{'='*60}")
            print(f"📝 归档并创建新会话")
            print(f"   用户 ID: {user_id}")
            print(f"{'='*60}")
            
            # 1. 将所有现有会话设为非活跃（归档）
            existing_sessions = ChatSession.query.filter_by(user_id=user_id).all()
            archived_count = 0
            
            for session in existing_sessions:
                if session.is_active:
                    session.is_active = False
                    session.updated_at = datetime.now()
                    archived_count += 1
            
            print(f"   归档会话数: {archived_count}")
            
            # 2. 创建新会话
            new_session = ChatSession(
                session_id=f"session_{uuid.uuid4().hex[:16]}",
                user_id=user_id,
                title=Config.DEFAULT_SESSION_TITLE,
                is_active=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                message_count=0
            )
            
            db.session.add(new_session)
            db.session.commit()
            
            print(f"✅ 新会话创建成功: {new_session.session_id}")
            print(f"   标题: {new_session.title}")
            print(f"{'='*60}\n")
            
            return new_session.to_dict()
            
        except Exception as e:
            print(f"❌ 归档并创建新会话失败: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            raise