# -*- coding: utf-8 -*-
"""
学习行为记录模型
记录用户的学习行为，用于分析学习模式和生成个性化建议
"""

from datetime import datetime
from database import db


class LearningRecord(db.Model):
    """
    学习行为记录表
    记录用户在系统中的各种学习行为
    """
    __tablename__ = 'learning_records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), 
                        nullable=False, index=True, comment='用户ID')
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id', ondelete='SET NULL'), 
                           nullable=True, index=True, comment='会话ID')
    
    # 行为类型：ask(提问), code_submit(代码提交), view_knowledge(查看知识)
    action_type = db.Column(db.String(50), nullable=False, index=True, comment='行为类型')
    
    # 行为内容（JSON格式）
    content = db.Column(db.Text, nullable=True, comment='行为内容(JSON格式)')
    
    # 涉及的知识点（逗号分隔）
    knowledge_topics = db.Column(db.String(500), nullable=True, comment='涉及的知识点')
    
    # 是否正确（用于代码分析）
    is_correct = db.Column(db.Boolean, nullable=True, comment='是否正确(代码分析用)')
    
    # 持续时间（秒）
    duration_seconds = db.Column(db.Integer, nullable=True, comment='持续时间(秒)')
    
    # 创建时间
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, 
                          index=True, comment='创建时间')

    # 关联关系
    user = db.relationship('User', backref=db.backref('learning_records', lazy='dynamic'))
    session = db.relationship('ChatSession', backref=db.backref('learning_records', lazy='dynamic'))

    def __repr__(self):
        return f'<LearningRecord {self.id}: {self.action_type} by User {self.user_id}>'

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'action_type': self.action_type,
            'content': self.content,
            'knowledge_topics': self.knowledge_topics,
            'is_correct': self.is_correct,
            'duration_seconds': self.duration_seconds,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def create_record(user_id, action_type, content=None, session_id=None, 
                     knowledge_topics=None, is_correct=None, duration_seconds=None):
        """
        创建学习记录
        
        Args:
            user_id: 用户ID
            action_type: 行为类型 ('ask', 'code_submit', 'view_knowledge')
            content: 行为内容
            session_id: 会话ID
            knowledge_topics: 涉及的知识点（逗号分隔字符串）
            is_correct: 是否正确
            duration_seconds: 持续时间
        
        Returns:
            LearningRecord: 创建的记录对象
        """
        record = LearningRecord(
            user_id=user_id,
            action_type=action_type,
            content=content,
            session_id=session_id,
            knowledge_topics=knowledge_topics,
            is_correct=is_correct,
            duration_seconds=duration_seconds
        )
        
        db.session.add(record)
        db.session.commit()
        
        return record

    @staticmethod
    def get_user_records(user_id, limit=100, offset=0, action_type=None):
        """
        获取用户的学习记录
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            offset: 偏移量
            action_type: 筛选行为类型
        
        Returns:
            list: 学习记录列表
        """
        query = LearningRecord.query.filter_by(user_id=user_id)
        
        if action_type:
            query = query.filter_by(action_type=action_type)
        
        records = query.order_by(LearningRecord.created_at.desc()) \
                      .limit(limit).offset(offset).all()
        
        return records

    @staticmethod
    def get_recent_topics(user_id, days=7):
        """
        获取用户最近学习的知识点
        
        Args:
            user_id: 用户ID
            days: 天数
        
        Returns:
            list: 知识点列表（按频率排序）
        """
        from datetime import timedelta
        from sqlalchemy import func
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        records = LearningRecord.query.filter(
            LearningRecord.user_id == user_id,
            LearningRecord.created_at >= cutoff_date,
            LearningRecord.knowledge_topics.isnot(None)
        ).all()
        
        # 统计知识点频率
        topic_count = {}
        for record in records:
            if record.knowledge_topics:
                topics = [t.strip() for t in record.knowledge_topics.split(',')]
                for topic in topics:
                    topic_count[topic] = topic_count.get(topic, 0) + 1
        
        # 按频率排序
        sorted_topics = sorted(topic_count.items(), key=lambda x: x[1], reverse=True)
        
        return [{'topic': topic, 'count': count} for topic, count in sorted_topics]
