# -*- coding: utf-8 -*-
"""
学习统计计算服务
提供各种学习数据的统计分析功能
"""

from datetime import datetime, timedelta
from sqlalchemy import func, case
from database import db
from models.learning_record import LearningRecord
from models.error_pattern import ErrorPattern
from models.chat_session import ChatSession
import json


class StatsCalculator:
    """学习统计计算服务"""
    
    @staticmethod
    def get_user_overview(user_id, days=30):
        """
        获取用户学习概览
        
        Args:
            user_id: 用户ID
            days: 统计天数（默认30天）
        
        Returns:
            dict: 学习概览数据
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 1. 总学习时长（估算：基于会话时长）
        sessions = ChatSession.query.filter(
            ChatSession.user_id == user_id,
            ChatSession.created_at >= cutoff_date
        ).all()
        
        total_duration = 0
        for session in sessions:
            if session.updated_at and session.created_at:
                duration = (session.updated_at - session.created_at).total_seconds() / 3600
                total_duration += duration
        
        # 2. 提问次数
        question_count = LearningRecord.query.filter_by(
            user_id=user_id,
            action_type='ask'
        ).filter(
            LearningRecord.created_at >= cutoff_date
        ).count()
        
        # 3. 代码提交次数和正确率
        code_records = LearningRecord.query.filter_by(
            user_id=user_id,
            action_type='code_submit'
        ).filter(
            LearningRecord.created_at >= cutoff_date
        ).all()
        
        code_count = len(code_records)
        correct_count = sum(1 for r in code_records if r.is_correct)
        accuracy = (correct_count / code_count * 100) if code_count > 0 else 0
        
        # 4. 活跃天数
        active_dates = db.session.query(
            func.date(LearningRecord.created_at)
        ).filter_by(
            user_id=user_id
        ).filter(
            LearningRecord.created_at >= cutoff_date
        ).distinct().all()
        
        active_days = len(active_dates)
        
        # 5. 知识点查看次数
        view_count = LearningRecord.query.filter_by(
            user_id=user_id,
            action_type='view_knowledge'
        ).filter(
            LearningRecord.created_at >= cutoff_date
        ).count()
        
        return {
            'total_duration_hours': round(total_duration, 1),
            'question_count': question_count,
            'code_count': code_count,
            'accuracy': round(accuracy, 1),
            'active_days': active_days,
            'avg_daily_questions': round(question_count / max(active_days, 1), 1),
            'view_count': view_count,
            'period_days': days
        }
    
    @staticmethod
    def get_learning_trend(user_id, days=30):
        """
        获取学习趋势（按天统计）
        
        Args:
            user_id: 用户ID
            days: 统计天数
        
        Returns:
            list: 每日统计数据
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 按日期分组统计
        daily_stats = db.session.query(
            func.date(LearningRecord.created_at).label('date'),
            func.count(LearningRecord.id).label('count'),
            func.sum(
                case(
                    (LearningRecord.action_type == 'code_submit', 1),
                    else_=0
                )
            ).label('code_count'),
            func.sum(
                case(
                    (LearningRecord.is_correct == True, 1),
                    else_=0
                )
            ).label('correct_count')
        ).filter_by(
            user_id=user_id
        ).filter(
            LearningRecord.created_at >= cutoff_date
        ).group_by(
            func.date(LearningRecord.created_at)
        ).all()
        
        # 填充缺失日期（显示为0）
        result = []
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=days-i-1)).date()
            stat = next((s for s in daily_stats if s.date == date), None)
            
            if stat:
                accuracy = (stat.correct_count / stat.code_count * 100) if stat.code_count > 0 else 0
                result.append({
                    'date': date.isoformat(),
                    'total_count': stat.count,
                    'code_count': stat.code_count,
                    'correct_count': stat.correct_count,
                    'accuracy': round(accuracy, 1)
                })
            else:
                result.append({
                    'date': date.isoformat(),
                    'total_count': 0,
                    'code_count': 0,
                    'correct_count': 0,
                    'accuracy': 0
                })
        
        return result
    
    @staticmethod
    def get_knowledge_mastery(user_id, days=30):
        """
        获取知识点掌握情况
        
        Args:
            user_id: 用户ID
            days: 统计天数
        
        Returns:
            list: 知识点掌握度列表
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 获取涉及知识点的记录
        records = LearningRecord.query.filter_by(
            user_id=user_id
        ).filter(
            LearningRecord.created_at >= cutoff_date,
            LearningRecord.knowledge_topics.isnot(None)
        ).all()
        
        # 统计每个知识点的出现次数和正确率
        topic_stats = {}
        
        for record in records:
            if not record.knowledge_topics:
                continue
            
            topics = record.knowledge_topics.split(',')
            
            for topic in topics:
                topic = topic.strip()
                if not topic:
                    continue
                
                if topic not in topic_stats:
                    topic_stats[topic] = {
                        'topic': topic,
                        'total_count': 0,
                        'code_count': 0,
                        'correct_count': 0,
                        'view_count': 0
                    }
                
                topic_stats[topic]['total_count'] += 1
                
                if record.action_type == 'code_submit':
                    topic_stats[topic]['code_count'] += 1
                    if record.is_correct:
                        topic_stats[topic]['correct_count'] += 1
                
                elif record.action_type == 'view_knowledge':
                    topic_stats[topic]['view_count'] += 1
        
        # 计算掌握度（正确率）
        result = []
        for topic, stats in topic_stats.items():
            if stats['code_count'] > 0:
                mastery = (stats['correct_count'] / stats['code_count']) * 100
            else:
                mastery = 0
            
            result.append({
                'topic': topic,
                'total_count': stats['total_count'],
                'code_count': stats['code_count'],
                'correct_count': stats['correct_count'],
                'view_count': stats['view_count'],
                'mastery': round(mastery, 1)
            })
        
        # 按出现次数排序
        result.sort(key=lambda x: x['total_count'], reverse=True)
        
        return result
    
    @staticmethod
    def get_error_distribution(user_id):
        """
        获取错误分布统计
        
        Args:
            user_id: 用户ID
        
        Returns:
            dict: 错误分布数据
        """
        patterns = ErrorPattern.query.filter_by(user_id=user_id).all()
        
        # 按类型统计
        distribution = {
            'syntax': {'count': 0, 'occurrences': 0},
            'logic': {'count': 0, 'occurrences': 0},
            'concept': {'count': 0, 'occurrences': 0}
        }
        
        for pattern in patterns:
            error_type = pattern.error_type
            if error_type in distribution:
                distribution[error_type]['count'] += 1
                distribution[error_type]['occurrences'] += pattern.occurrence_count
        
        # 获取高频错误（出现3次以上）
        frequent_errors = [
            {
                'error_type': p.error_type,
                'description': p.error_description,
                'occurrence_count': p.occurrence_count,
                'related_topic': p.related_topic,
                'last_seen': p.last_seen.isoformat() if p.last_seen else None
            }
            for p in patterns if p.occurrence_count >= 3
        ]
        
        # 按出现次数排序
        frequent_errors.sort(key=lambda x: x['occurrence_count'], reverse=True)
        
        return {
            'distribution': distribution,
            'frequent_errors': frequent_errors[:10],  # 最多返回10个
            'total_patterns': len(patterns),
            'total_occurrences': sum(p.occurrence_count for p in patterns)
        }
    
    @staticmethod
    def get_code_quality_trend(user_id, days=30):
        """
        获取代码质量趋势
        
        Args:
            user_id: 用户ID
            days: 统计天数
        
        Returns:
            list: 代码质量趋势数据
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 获取所有代码提交记录
        records = LearningRecord.query.filter_by(
            user_id=user_id,
            action_type='code_submit'
        ).filter(
            LearningRecord.created_at >= cutoff_date
        ).order_by(
            LearningRecord.created_at.asc()
        ).all()
        
        # 提取评分
        scores = []
        for record in records:
            try:
                content = json.loads(record.content) if record.content else {}
                score = content.get('score', 0)
                
                scores.append({
                    'date': record.created_at.isoformat(),
                    'score': score,
                    'level': content.get('level', 'F')
                })
            except:
                continue
        
        # 计算移动平均（5次提交）
        if len(scores) > 0:
            for i in range(len(scores)):
                window_start = max(0, i - 4)
                window_scores = [s['score'] for s in scores[window_start:i+1]]
                moving_avg = sum(window_scores) / len(window_scores)
                scores[i]['moving_avg'] = round(moving_avg, 1)
        
        return scores
    
    @staticmethod
    def get_activity_heatmap(user_id, days=90):
        """
        获取活动热力图数据（按小时统计）
        
        Args:
            user_id: 用户ID
            days: 统计天数
        
        Returns:
            dict: 热力图数据
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 按小时分组统计
        hourly_stats = db.session.query(
            func.extract('hour', LearningRecord.created_at).label('hour'),
            func.count(LearningRecord.id).label('count')
        ).filter_by(
            user_id=user_id
        ).filter(
            LearningRecord.created_at >= cutoff_date
        ).group_by(
            func.extract('hour', LearningRecord.created_at)
        ).all()
        
        # 构建24小时数组（0-23）
        heatmap = [0] * 24
        
        for stat in hourly_stats:
            hour = int(stat.hour)
            heatmap[hour] = stat.count
        
        # 找出最活跃的时间段
        max_count = max(heatmap)
        peak_hours = [i for i, count in enumerate(heatmap) if count == max_count]
        
        return {
            'hourly_counts': heatmap,
            'peak_hours': peak_hours,
            'total_activities': sum(heatmap)
        }