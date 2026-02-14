# -*- coding: utf-8 -*-
"""
学习统计计算服务
⭐ 只统计学生角色的数据
⭐ 学习时长基于心跳记录精确计算
"""

from datetime import datetime, timedelta
from sqlalchemy import func, case
from database import db
from models.learning_record import LearningRecord
from models.error_pattern import ErrorPattern
from models.chat_session import ChatSession
from models.user import User


class StatsCalculator:
    """学习统计计算服务"""
    
    @staticmethod
    def _get_student_ids():
        """获取所有学生用户ID列表"""
        students = User.query.filter_by(role='student', is_active=True).all()
        return [s.id for s in students]
    
    @staticmethod
    def get_user_overview(user_id, days=30):
        """
        获取用户学习概览
        
        ⭐ 学习时长改为基于心跳记录精确计算
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # ⭐ 验证是否为学生
        user = User.query.get(user_id)
        if not user:
            return StatsCalculator._empty_overview(days)
        
        # 1. ⭐⭐⭐ 学习时长：基于心跳记录精确计算 ⭐⭐⭐
        heartbeat_count = LearningRecord.query.filter_by(
            user_id=user_id,
            action_type='heartbeat'
        ).filter(
            LearningRecord.created_at >= cutoff_date
        ).count()
        
        # 每次心跳 = 1分钟，转换为小时
        total_duration_hours = round(heartbeat_count / 60, 1)
        
        # 如果没有心跳数据，降级使用会话时长估算
        if heartbeat_count == 0:
            total_duration_hours = StatsCalculator._estimate_duration_from_sessions(
                user_id, cutoff_date
            )
        
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
        ).filter(
            LearningRecord.user_id == user_id,
            LearningRecord.created_at >= cutoff_date,
            LearningRecord.action_type != 'heartbeat'  # ⭐ 排除心跳
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
            'total_duration_hours': total_duration_hours,
            'duration_source': 'heartbeat' if heartbeat_count > 0 else 'session_estimate',
            'question_count': question_count,
            'code_count': code_count,
            'accuracy': round(accuracy, 1),
            'active_days': active_days,
            'avg_daily_questions': round(question_count / max(active_days, 1), 1),
            'view_count': view_count,
            'period_days': days
        }
    
    @staticmethod
    def _estimate_duration_from_sessions(user_id, cutoff_date):
        """
        ⭐ 降级方案：基于会话时间差估算学习时长
        单次会话最长计4小时（防止忘记关页面导致的虚高）
        """
        sessions = ChatSession.query.filter(
            ChatSession.user_id == user_id,
            ChatSession.created_at >= cutoff_date
        ).all()
        
        total_duration = 0
        for session in sessions:
            if session.updated_at and session.created_at:
                duration = (session.updated_at - session.created_at).total_seconds() / 3600
                # ⭐ 单次会话封顶4小时
                duration = min(duration, 4.0)
                # ⭐ 忽略不足30秒的会话
                if duration * 3600 >= 30:
                    total_duration += duration
        
        return round(total_duration, 1)
    
    @staticmethod
    def _empty_overview(days):
        """返回空的概览数据"""
        return {
            'total_duration_hours': 0,
            'duration_source': 'none',
            'question_count': 0,
            'code_count': 0,
            'accuracy': 0,
            'active_days': 0,
            'avg_daily_questions': 0,
            'view_count': 0,
            'period_days': days
        }
    
    @staticmethod
    def get_all_students_overview(days=30):
        """
        ⭐⭐⭐ 新增：获取所有学生的学习概览汇总 ⭐⭐⭐
        教师/管理员查看用
        """
        student_ids = StatsCalculator._get_student_ids()
        
        if not student_ids:
            return {
                'student_count': 0,
                'students': [],
                'summary': StatsCalculator._empty_overview(days)
            }
        
        students_data = []
        total_duration = 0
        total_questions = 0
        total_code = 0
        total_active_days = 0
        
        for sid in student_ids:
            user = User.query.get(sid)
            overview = StatsCalculator.get_user_overview(sid, days)
            
            students_data.append({
                'user_id': sid,
                'username': user.username,
                'nickname': user.nickname or user.username,
                **overview
            })
            
            total_duration += overview['total_duration_hours']
            total_questions += overview['question_count']
            total_code += overview['code_count']
            total_active_days += overview['active_days']
        
        # 按学习时长排序
        students_data.sort(key=lambda x: x['total_duration_hours'], reverse=True)
        
        return {
            'student_count': len(student_ids),
            'students': students_data,
            'summary': {
                'total_duration_hours': round(total_duration, 1),
                'avg_duration_hours': round(total_duration / len(student_ids), 1),
                'total_questions': total_questions,
                'total_code_submissions': total_code,
                'avg_active_days': round(total_active_days / len(student_ids), 1),
                'period_days': days
            }
        }
    
    @staticmethod
    def get_learning_trend(user_id, days=30):
        """
        获取学习趋势（按天统计）
        ⭐ 学习时长基于心跳精确计算
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 1. 按日期分组统计行为（排除心跳）
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
        ).filter(
            LearningRecord.user_id == user_id,
            LearningRecord.created_at >= cutoff_date,
            LearningRecord.action_type != 'heartbeat'  # ⭐ 排除心跳
        ).group_by(
            func.date(LearningRecord.created_at)
        ).all()
        
        # 2. ⭐ 按日期统计心跳（学习时长）
        daily_heartbeats = db.session.query(
            func.date(LearningRecord.created_at).label('date'),
            func.count(LearningRecord.id).label('heartbeat_count')
        ).filter(
            LearningRecord.user_id == user_id,
            LearningRecord.created_at >= cutoff_date,
            LearningRecord.action_type == 'heartbeat'
        ).group_by(
            func.date(LearningRecord.created_at)
        ).all()
        
        # 转为字典方便查找
        heartbeat_map = {str(h.date): h.heartbeat_count for h in daily_heartbeats}
        
        # 3. 填充缺失日期
        result = []
        for i in range(days):
            date = (datetime.utcnow() - timedelta(days=days - i - 1)).date()
            date_str = date.isoformat()
            stat = next((s for s in daily_stats if str(s.date) == date_str), None)
            hb_count = heartbeat_map.get(date_str, 0)
            
            if stat:
                code_count = stat.code_count or 0
                correct_count = stat.correct_count or 0
                accuracy = (correct_count / code_count * 100) if code_count > 0 else 0
                result.append({
                    'date': date_str,
                    'total_count': stat.count,
                    'code_count': code_count,
                    'correct_count': correct_count,
                    'accuracy': round(accuracy, 1),
                    'duration_minutes': hb_count  # ⭐ 精确学习分钟数
                })
            else:
                result.append({
                    'date': date_str,
                    'total_count': 0,
                    'code_count': 0,
                    'correct_count': 0,
                    'accuracy': 0,
                    'duration_minutes': hb_count
                })
        
        return result
    
    @staticmethod
    def get_knowledge_mastery(user_id, days=30):
        """获取知识点掌握情况"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        records = LearningRecord.query.filter(
            LearningRecord.user_id == user_id,
            LearningRecord.created_at >= cutoff_date,
            LearningRecord.knowledge_topics.isnot(None),
            LearningRecord.knowledge_topics != ''
        ).all()
        
        topic_stats = {}
        
        for record in records:
            if not record.knowledge_topics:
                continue
            
            topics = [t.strip() for t in record.knowledge_topics.split(',') if t.strip()]
            for topic in topics:
                if topic not in topic_stats:
                    topic_stats[topic] = {'total': 0, 'correct': 0}
                topic_stats[topic]['total'] += 1
                if record.is_correct:
                    topic_stats[topic]['correct'] += 1
        
        result = []
        for topic, stats in topic_stats.items():
            mastery = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            result.append({
                'topic': topic,
                'total_count': stats['total'],
                'correct_count': stats['correct'],
                'mastery': round(mastery, 1)
            })
        
        result.sort(key=lambda x: x['total_count'], reverse=True)
        
        return result
    
    @staticmethod
    def get_error_distribution(user_id):
        """获取错误分布统计"""
        patterns = ErrorPattern.query.filter_by(user_id=user_id).all()
        
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
        
        frequent_errors = ErrorPattern.query.filter(
            ErrorPattern.user_id == user_id,
            ErrorPattern.occurrence_count >= 3
        ).order_by(ErrorPattern.occurrence_count.desc()).limit(10).all()
        
        return {
            'distribution': distribution,
            'frequent_errors': [e.to_dict() for e in frequent_errors],
            'total_patterns': len(patterns)
        }
    
    @staticmethod
    def get_code_quality_trend(user_id, days=30):
        """获取代码质量趋势"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        records = LearningRecord.query.filter_by(
            user_id=user_id,
            action_type='code_submit'
        ).filter(
            LearningRecord.created_at >= cutoff_date
        ).order_by(LearningRecord.created_at.asc()).all()
        
        result = []
        scores = []
        
        for record in records:
            try:
                import json
                content = json.loads(record.content) if record.content else {}
                score = content.get('score', 0)
                scores.append(score)
                
                # 计算移动平均（最近5次）
                recent = scores[-5:]
                moving_avg = sum(recent) / len(recent)
                
                result.append({
                    'date': record.created_at.isoformat(),
                    'score': score,
                    'level': content.get('level', 'F'),
                    'moving_avg': round(moving_avg, 1)
                })
            except Exception:
                continue
        
        return result
    
    @staticmethod
    def get_activity_heatmap(user_id, days=90):
        """获取活动热力图数据"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        daily_counts = db.session.query(
            func.date(LearningRecord.created_at).label('date'),
            func.count(LearningRecord.id).label('count')
        ).filter(
            LearningRecord.user_id == user_id,
            LearningRecord.created_at >= cutoff_date,
            LearningRecord.action_type != 'heartbeat'
        ).group_by(
            func.date(LearningRecord.created_at)
        ).all()
        
        return [
            {'date': str(item.date), 'count': item.count}
            for item in daily_counts
        ]