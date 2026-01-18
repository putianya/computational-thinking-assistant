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
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    message_count = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        """
        转换为字典
        """
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_id': self.user_id,
            'title': self.title,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'message_count': self.message_count
        }
    
    def __repr__(self):
        return f'<ChatSession {self.session_id}>'