# -*- coding: utf-8 -*-
"""
聊天会话模型
"""
from datetime import datetime
from database import db


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
        获取该会话的最近 N 条消息
        
        Args:
            limit: 返回的消息数量，None 表示返回全部
        """
        from models.chat_message import ChatMessage
        
        query = self.messages.order_by(ChatMessage.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        messages = query.all()
        messages.reverse()  # 反转顺序（最旧的在前）
        
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
        from models.chat_message import ChatMessage
        from config import Config  # ⭐ 在方法内部导入，避免初始化时的循环引用
        
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
        
        # 4. ⭐ 如果消息超过配置的最大值，删除最旧的
        max_messages = Config.MAX_MESSAGES_PER_SESSION
        
        if self.message_count > max_messages:
            oldest_message = self.messages.order_by(
                ChatMessage.created_at.asc()
            ).first()
            
            if oldest_message:
                db.session.delete(oldest_message)
                self.message_count -= 1
                print(f"🗑️ 删除会话 {self.session_id} 的最旧消息（超过 {max_messages} 条限制）")
        
        # 5. 如果是第一条用户消息，自动生成标题
        if self.message_count == 1 and role == 'user':
            self.title = content[:30] + ('...' if len(content) > 30 else '')
            print(f"📝 自动生成标题: {self.title}")
        
        db.session.commit()
        
        return new_message
    
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
            'message_count': self.message_count
        }
        
        if include_messages:
            result['messages'] = self.get_messages()
        
        return result
    
    def set_active(self):
        """
        将当前会话设为活跃
        同时将同一用户的其他会话设为非活跃
        """
        ChatSession.query.filter_by(
            user_id=self.user_id,
            is_active=True
        ).update({'is_active': False})
        
        self.is_active = True
        db.session.commit()
        
        print(f"✅ 会话 {self.session_id} 已设为活跃")
    
    def clear_messages(self):
        """
        清除会话的所有消息
        """
        from models.chat_message import ChatMessage
        
        ChatMessage.query.filter_by(session_id=self.id).delete()
        self.message_count = 0
        self.updated_at = datetime.now()
        db.session.commit()
        
        print(f"🗑️ 会话 {self.session_id} 的所有消息已清除")
    
    def __repr__(self):
        return f'<ChatSession {self.session_id} - {self.title}>'