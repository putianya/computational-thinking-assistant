# -*- coding: utf-8 -*-
"""
聊天消息模型
"""
from datetime import datetime
from database import db


class ChatMessage(db.Model):
    """
    聊天消息表
    """
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)  # 'user' 或 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    
    def to_dict(self):
        """
        转换为字典
        """
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<ChatMessage {self.role}: {self.content[:30]}...>'