# -*- coding: utf-8 -*-
"""
学习报告模型
生成和存储用户的学习分析报告
"""

from datetime import datetime, timedelta
from database import db
from models.learning_record import LearningRecord
from models.error_pattern import ErrorPattern


class LearningReport(db.Model):
    """
    学习报告表
    存储定期生成的用户学习分析报告
    """
    __tablename__ = 'learning_reports'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='主键')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), 
                        nullable=False, index=True, comment='用户ID')
    
    # 报告时间范围
    start_date = db.Column(db.DateTime, nullable=False, index=True, comment='开始日期')
    end_date = db.Column(db.DateTime, nullable=False, index=True, comment='结束日期')
    
    # 报告类型：daily(日报), weekly(周报), monthly(月报)
    report_type = db.Column(db.String(20), nullable=False, comment='报告类型')
    
    # 学习统计数据（JSON格式）
    statistics = db.Column(db.Text, nullable=True, comment='学习统计数据(JSON)')
    
    # 知识点掌握情况（JSON格式）
    topic_mastery = db.Column(db.Text, nullable=True, comment='知识点掌握情况(JSON)')
    
    # 错误分析（JSON格式）
    error_analysis = db.Column(db.Text, nullable=True, comment='错误分析(JSON)')
    
    # 学习建议（JSON格式）
    suggestions = db.Column(db.Text, nullable=True, comment='学习建议(JSON)')
    
    # 总体评分（0-100）
    overall_score = db.Column(db.Integer, nullable=True, comment='总体评分')
    
    # 创建时间
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, 
                          index=True, comment='创建时间')

    # 关联关系
    user = db.relationship('User', backref=db.backref('learning_reports', lazy='dynamic'))

    def __repr__(self):
        return f'<LearningReport {self.id}: {self.report_type} for User {self.user_id}>'

    def to_dict(self):
        """转换为字典格式"""
        import json
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'report_type': self.report_type,
            'statistics': json.loads(self.statistics) if self.statistics else None,
            'topic_mastery': json.loads(self.topic_mastery) if self.topic_mastery else None,
            'error_analysis': json.loads(self.error_analysis) if self.error_analysis else None,
            'suggestions': json.loads(self.suggestions) if self.suggestions else None,
            'overall_score': self.overall_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    @staticmethod
    def generate_report(user_id, report_type='weekly'):
        """
        生成学习报告
        
        Args:
            user_id: 用户ID
            report_type: 报告类型 ('daily', 'weekly', 'monthly')
        
        Returns:
            LearningReport: 生成的报告对象
        """
        import json
        
        # 确定报告时间范围
        end_date = datetime.utcnow()
        
        if report_type == 'daily':
            start_date = end_date - timedelta(days=1)
        elif report_type == 'weekly':
            start_date = end_date - timedelta(days=7)
        elif report_type == 'monthly':
            start_date = end_date - timedelta(days=30)
        else:
            raise ValueError(f"Invalid report_type: {report_type}")
        
        # 1. 统计学习数据
        records = LearningRecord.query.filter(
            LearningRecord.user_id == user_id,
            LearningRecord.created_at >= start_date,
            LearningRecord.created_at <= end_date
        ).all()
        
        statistics = {
            'total_actions': len(records),
            'ask_count': sum(1 for r in records if r.action_type == 'ask'),
            'code_submit_count': sum(1 for r in records if r.action_type == 'code_submit'),
            'view_knowledge_count': sum(1 for r in records if r.action_type == 'view_knowledge'),
            'total_duration_minutes': sum(r.duration_seconds or 0 for r in records) // 60,
            'average_session_duration': None  # 可以后续计算
        }
        
        # 2. 知识点掌握分析
        topic_records = [r for r in records if r.knowledge_topics]
        topic_counts = {}
        topic_correct = {}
        
        for record in topic_records:
            if record.knowledge_topics:
                topics = [t.strip() for t in record.knowledge_topics.split(',')]
                for topic in topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
                    
                    if record.is_correct is not None:
                        if topic not in topic_correct:
                            topic_correct[topic] = {'correct': 0, 'total': 0}
                        
                        topic_correct[topic]['total'] += 1
                        if record.is_correct:
                            topic_correct[topic]['correct'] += 1
        
        topic_mastery = []
        for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            mastery_info = {
                'topic': topic,
                'practice_count': count
            }
            
            if topic in topic_correct and topic_correct[topic]['total'] > 0:
                correct_rate = topic_correct[topic]['correct'] / topic_correct[topic]['total']
                mastery_info['accuracy'] = round(correct_rate * 100, 2)
                mastery_info['mastery_level'] = _get_mastery_level(correct_rate)
            
            topic_mastery.append(mastery_info)
        
        # 3. 错误分析
        error_patterns = ErrorPattern.query.filter(
            ErrorPattern.user_id == user_id,
            ErrorPattern.last_seen >= start_date
        ).order_by(ErrorPattern.occurrence_count.desc()).limit(10).all()
        
        error_analysis = {
            'total_error_types': len(error_patterns),
            'frequent_errors': [
                {
                    'error_type': ep.error_type,
                    'description': ep.error_description,
                    'related_topic': ep.related_topic,
                    'count': ep.occurrence_count
                }
                for ep in error_patterns
            ]
        }
        
        # 4. 生成学习建议
        suggestions = _generate_suggestions(statistics, topic_mastery, error_analysis)
        
        # 5. 计算总体评分
        overall_score = _calculate_overall_score(statistics, topic_mastery, error_analysis)
        
        # 创建报告
        report = LearningReport(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            report_type=report_type,
            statistics=json.dumps(statistics, ensure_ascii=False),
            topic_mastery=json.dumps(topic_mastery, ensure_ascii=False),
            error_analysis=json.dumps(error_analysis, ensure_ascii=False),
            suggestions=json.dumps(suggestions, ensure_ascii=False),
            overall_score=overall_score
        )
        
        db.session.add(report)
        db.session.commit()
        
        return report

    @staticmethod
    def get_latest_report(user_id, report_type=None):
        """
        获取用户最新的学习报告
        
        Args:
            user_id: 用户ID
            report_type: 报告类型筛选
        
        Returns:
            LearningReport: 最新报告对象
        """
        query = LearningReport.query.filter_by(user_id=user_id)
        
        if report_type:
            query = query.filter_by(report_type=report_type)
        
        return query.order_by(LearningReport.created_at.desc()).first()

    @staticmethod
    def get_reports(user_id, limit=10, offset=0):
        """
        获取用户的学习报告列表
        
        Args:
            user_id: 用户ID
            limit: 限制数量
            offset: 偏移量
        
        Returns:
            list: 报告列表
        """
        reports = LearningReport.query.filter_by(user_id=user_id) \
                                      .order_by(LearningReport.created_at.desc()) \
                                      .limit(limit).offset(offset).all()
        
        return reports


# ========== 辅助函数 ==========

def _get_mastery_level(accuracy):
    """
    根据正确率判断掌握程度
    
    Args:
        accuracy: 正确率 (0-1)
    
    Returns:
        str: 掌握程度 ('excellent', 'good', 'fair', 'poor')
    """
    if accuracy >= 0.9:
        return 'excellent'
    elif accuracy >= 0.75:
        return 'good'
    elif accuracy >= 0.6:
        return 'fair'
    else:
        return 'poor'


def _generate_suggestions(statistics, topic_mastery, error_analysis):
    """
    根据学习数据生成个性化建议
    
    Args:
        statistics: 学习统计数据
        topic_mastery: 知识点掌握情况
        error_analysis: 错误分析
    
    Returns:
        list: 建议列表
    """
    suggestions = []
    
    # 1. 基于学习活跃度的建议
    if statistics['total_actions'] < 10:
        suggestions.append({
            'type': 'activity',
            'priority': 'high',
            'message': '学习活跃度较低，建议增加练习频率，每天至少提交5次代码或提问。'
        })
    
    # 2. 基于知识点掌握情况的建议
    weak_topics = [tm for tm in topic_mastery if tm.get('accuracy', 100) < 60]
    if weak_topics:
        suggestions.append({
            'type': 'topic',
            'priority': 'high',
            'message': f'以下知识点需要加强：{", ".join([t["topic"] for t in weak_topics[:3]])}',
            'topics': [t['topic'] for t in weak_topics]
        })
    
    # 3. 基于错误模式的建议
    if error_analysis['total_error_types'] > 0:
        frequent_errors = error_analysis['frequent_errors'][:3]
        if frequent_errors:
            error_types = [e['error_type'] for e in frequent_errors]
            
            if 'syntax' in error_types:
                suggestions.append({
                    'type': 'error',
                    'priority': 'medium',
                    'message': '存在较多语法错误，建议复习C语言基本语法规则。'
                })
            
            if 'logic' in error_types:
                suggestions.append({
                    'type': 'error',
                    'priority': 'medium',
                    'message': '存在逻辑错误，建议加强算法思维训练和代码调试能力。'
                })
    
    # 4. 基于学习时长的建议
    if statistics['total_duration_minutes'] < 60:
        suggestions.append({
            'type': 'time',
            'priority': 'low',
            'message': '学习时间较少，建议每天投入至少30分钟进行系统学习。'
        })
    
    return suggestions


def _calculate_overall_score(statistics, topic_mastery, error_analysis):
    """
    计算总体学习评分
    
    Args:
        statistics: 学习统计数据
        topic_mastery: 知识点掌握情况
        error_analysis: 错误分析
    
    Returns:
        int: 评分 (0-100)
    """
    score = 0
    
    # 1. 活跃度得分（30分）
    activity_score = min(statistics['total_actions'] * 2, 30)
    score += activity_score
    
    # 2. 知识点掌握得分（40分）
    if topic_mastery:
        avg_accuracy = sum(tm.get('accuracy', 0) for tm in topic_mastery) / len(topic_mastery)
        mastery_score = (avg_accuracy / 100) * 40
        score += mastery_score
    else:
        score += 20  # 默认给一半分数
    
    # 3. 错误控制得分（30分）
    if error_analysis['total_error_types'] == 0:
        error_score = 30
    else:
        # 错误类型越少，分数越高
        error_score = max(30 - error_analysis['total_error_types'] * 3, 0)
    
    score += error_score
    
    return int(score)
