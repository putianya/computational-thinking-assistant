# -*- coding: utf-8 -*-
"""
聊天会话模型
"""
from datetime import datetime
from database import db
from models.chat_message import ChatMessage

class ChatSession(db.Model):
    """
    聊天会话表
    """
    __tablename__ = 'chat_sessions'
    
    # ========== 表字段 ==========
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # ⭐ 修复：使用字符串常量作为默认值
    title = db.Column(db.String(200), nullable=True, default='新对话')
    
    is_active = db.Column(db.Boolean, default=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    message_count = db.Column(db.Integer, default=0)
    
    # ========== 关系 ==========
    messages = db.relationship(
        'ChatMessage', 
        backref='session', 
        lazy='dynamic',
        cascade='all, delete-orphan',
        order_by='ChatMessage.created_at'
    )
    
    # ========== 方法 ==========
    
    def get_messages(self, limit=None):
        """
        获取该会话的消息
        
        ⭐⭐⭐ 修复：确保按时间升序返回（最早的在前）⭐⭐⭐
        """
        from models.chat_message import ChatMessage
        
        # ⭐ 直接按升序查询，不需要反转
        query = ChatMessage.query.filter_by(session_id=self.id)\
            .order_by(ChatMessage.created_at.asc())  # ⭐ 升序：最早的在前
            
        if limit:
            # 如果有限制，取最新的 N 条
            total = ChatMessage.query.filter_by(session_id=self.id).count()
            if total > limit:
                # 计算需要跳过的数量
                offset = total - limit
                query = ChatMessage.query.filter_by(session_id=self.id)\
                    .order_by(ChatMessage.created_at.asc())\
                    .offset(offset)\
                    .limit(limit)
        
        messages = query.all()
        
        return [msg.to_dict() for msg in messages]
    
    def add_message(self, role, content):
        """
        添加消息到会话
        
        Args:
            role: 'user' 或 'assistant'
            content: 消息内容
        
        Returns:
            ChatMessage: 新创建的消息对象
        """
        from config import Config
        
        # 1. 创建新消息
        new_message = ChatMessage(
            session_id=self.id,
            role=role,
            content=content
        )
        db.session.add(new_message)
        
        # 2. 更新消息计数
        self.message_count += 1
        
        # 3. 更新会话的最后修改时间
        self.updated_at = datetime.now()
        
        # ⭐⭐⭐ 4. 修改：不再删除旧消息 ⭐⭐⭐
        # ❌ 删除以下代码块：
        # max_messages = Config.MAX_MESSAGES_PER_SESSION
        # if self.message_count > max_messages:
        #     oldest_message = self.messages.order_by(ChatMessage.created_at.asc()).first()
        #     if oldest_message:
        #         db.session.delete(oldest_message)
        #         self.message_count -= 1
        
        # ✅ 新增：记录对话轮数（消息数 / 2）
        self.conversation_rounds = self.message_count // 2
        
        # 5. 如果是第一条用户消息，自动生成标题
        if self.message_count == 1 and role == 'user':
            self.title = content[:30] + ('...' if len(content) > 30 else '')
            print(f"📝 自动生成标题: {self.title}")
        
        db.session.commit()
        
        return new_message
    
    def get_conversation_rounds(self):
        """
        获取对话轮数
        
        Returns:
            int: 对话轮数（消息数 / 2）
        """
        return self.message_count // 2
    
    def to_dict(self, include_messages=False):
        """
        转换为字典
        
        Args:
            include_messages: 是否包含消息列表
        
        Returns:
            dict: 会话信息字典
        """
        result = {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'title': self.title,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'message_count': self.message_count,
            'conversation_rounds': self.get_conversation_rounds()  # ⭐ 新增
        }
        
        if include_messages:
            result['messages'] = self.get_messages()
        
        return result
    
    def clear_messages(self):
        """
        清空会话的所有消息
        """
        try:
            ChatMessage.query.filter_by(session_id=self.id).delete()
            
            self.message_count = 0
            self.updated_at = datetime.now()
            
            db.session.commit()
            
            print(f"🗑️ 清空会话消息: {self.session_id}")
            
        except Exception as e:
            print(f"❌ 清空消息失败: {e}")
            db.session.rollback()
            raise
    
    def set_active(self):
        """
        将当前会话设为活跃
        同时将同一用户的其他会话设为非活跃
    
        ⭐ 使用逐个查询的方式，确保对象状态正确更新
        """
        try:
            # ⭐⭐⭐ 方法1：逐个查询并更新（最可靠）⭐⭐⭐
            # 查询该用户所有活跃会话
            active_sessions = self.__class__.query.filter_by(
                user_id=self.user_id,
                is_active=True
            ).all()
            
            # 逐个设为非活跃
            for session in active_sessions:
                if session.id != self.id:  # 排除当前会话
                    session.is_active = False
                    session.updated_at = datetime.now()
            
            # 设置当前会话为活跃
            self.is_active = True
            self.updated_at = datetime.now()
            
            # 一次性提交所有更改
            db.session.commit()
            
            print(f"✅ 会话 {self.session_id} 已设为活跃")
            
        except Exception as e:
            print(f"❌ 设置活跃会话失败: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            raise
    
    def __repr__(self):
        return f'<ChatSession {self.session_id} - {self.title}>'