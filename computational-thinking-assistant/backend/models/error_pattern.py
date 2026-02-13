# -*- coding: utf-8 -*-
"""
错误模式模型
记录和分析用户的常见错误模式，用于生成个性化学习建议
"""

from datetime import datetime
from database import db


class ErrorPattern(db.Model):
    """
    错误模式表
    记录用户的常见错误类型和模式
    """
    __tablename__ = 'error_patterns'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), 
                        nullable=False, index=True, comment='用户ID')
    
    # 错误类型：syntax(语法错误), logic(逻辑错误), concept(概念错误)
    error_type = db.Column(db.String(50), nullable=False, index=True, comment='错误类型')
    
    # 错误描述
    error_description = db.Column(db.Text, nullable=False, comment='错误描述')
    
    # 相关知识点
    related_topic = db.Column(db.String(200), nullable=True, index=True, comment='相关知识点')
    
    # 出现次数
    occurrence_count = db.Column(db.Integer, nullable=False, default=1, comment='出现次数')
    
    # 首次出现时间
    first_seen = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, 
                          index=True, comment='首次出现时间')
    
    # 最后出现时间
    last_seen = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, 
                         index=True, comment='最后出现时间')

    # 关联关系
    user = db.relationship('User', backref=db.backref('error_patterns', lazy='dynamic'))

    def __repr__(self):
        return f'<ErrorPattern {self.id}: {self.error_type} - {self.related_topic}>'

    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'error_type': self.error_type,
            'error_description': self.error_description,
            'related_topic': self.related_topic,
            'occurrence_count': self.occurrence_count,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }

    @staticmethod
    def record_error(user_id, error_type, error_description, related_topic=None):
        """
        记录用户错误
        如果是相同的错误模式，则增加计数；否则创建新记录
        
        Args:
            user_id: 用户ID
            error_type: 错误类型 ('syntax', 'logic', 'concept')
            error_description: 错误描述
            related_topic: 相关知识点
        
        Returns:
            ErrorPattern: 错误模式对象
        """
        # 查找是否存在相同的错误模式
        existing = ErrorPattern.query.filter_by(
            user_id=user_id,
            error_type=error_type,
            error_description=error_description,
            related_topic=related_topic
        ).first()
        
        if existing:
            # 更新已有记录
            existing.occurrence_count += 1
            existing.last_seen = datetime.utcnow()
        else:
            # 创建新记录
            existing = ErrorPattern(
                user_id=user_id,
                error_type=error_type,
                error_description=error_description,
                related_topic=related_topic,
                occurrence_count=1
            )
            db.session.add(existing)
        
        db.session.commit()
        return existing

    @staticmethod
    def get_user_patterns(user_id, error_type=None, limit=50):
        """
        获取用户的错误模式
        
        Args:
            user_id: 用户ID
            error_type: 筛选错误类型
            limit: 限制数量
        
        Returns:
            list: 错误模式列表（按出现次数降序）
        """
        query = ErrorPattern.query.filter_by(user_id=user_id)
        
        if error_type:
            query = query.filter_by(error_type=error_type)
        
        patterns = query.order_by(ErrorPattern.occurrence_count.desc()) \
                       .limit(limit).all()
        
        return patterns

    @staticmethod
    def get_frequent_errors(user_id, min_count=2):
        """
        获取用户的高频错误
        
        Args:
            user_id: 用户ID
            min_count: 最小出现次数
        
        Returns:
            list: 高频错误列表
        """
        patterns = ErrorPattern.query.filter(
            ErrorPattern.user_id == user_id,
            ErrorPattern.occurrence_count >= min_count
        ).order_by(ErrorPattern.occurrence_count.desc()).all()
        
        return patterns

    @staticmethod
    def get_recent_errors(user_id, days=7):
        """
        获取用户最近的错误
        
        Args:
            user_id: 用户ID
            days: 天数
        
        Returns:
            list: 最近错误列表
        """
        from datetime import timedelta
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        patterns = ErrorPattern.query.filter(
            ErrorPattern.user_id == user_id,
            ErrorPattern.last_seen >= cutoff_date
        ).order_by(ErrorPattern.last_seen.desc()).all()
        
        return patterns

    @staticmethod
    def get_error_summary(user_id):
        """
        获取用户的错误摘要统计
        
        Args:
            user_id: 用户ID
        
        Returns:
            dict: 错误统计信息
        """
        from sqlalchemy import func
        
        total_patterns = ErrorPattern.query.filter_by(user_id=user_id).count()
        
        # 按类型统计
        type_stats = db.session.query(
            ErrorPattern.error_type,
            func.count(ErrorPattern.id).label('count'),
            func.sum(ErrorPattern.occurrence_count).label('total_occurrences')
        ).filter_by(user_id=user_id) \
         .group_by(ErrorPattern.error_type) \
         .all()
        
        type_summary = {
            stat[0]: {
                'pattern_count': stat[1],
                'total_occurrences': stat[2] or 0
            }
            for stat in type_stats
        }
        
        # 按知识点统计
        topic_stats = db.session.query(
            ErrorPattern.related_topic,
            func.count(ErrorPattern.id).label('count')
        ).filter(
            ErrorPattern.user_id == user_id,
            ErrorPattern.related_topic.isnot(None)
        ).group_by(ErrorPattern.related_topic) \
         .order_by(func.count(ErrorPattern.id).desc()) \
         .limit(10).all()
        
        top_topics = [
            {'topic': stat[0], 'count': stat[1]}
            for stat in topic_stats
        ]
        
        return {
            'total_patterns': total_patterns,
            'by_type': type_summary,
            'top_topics': top_topics
        }
