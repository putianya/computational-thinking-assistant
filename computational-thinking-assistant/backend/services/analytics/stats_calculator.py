# -*- coding: utf-8 -*-
"""
学习统计计算服务
⭐ 只统计学生角色的数据
⭐ 学习时长基于心跳记录精确计算
"""

from datetime import datetime, timedelta
from sqlalchemy import func
from database import db
from models.learning_record import LearningRecord
from models.error_pattern import ErrorPattern
from models.chat_session import ChatSession
from models.user import User
from models.knowledge_chunk import KnowledgeChunk
from models.chat_message import ChatMessage
from models.chat_session import ChatSession
import json


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
        
         # 5. 知识点查看次数 → 改为：涉及到的不重复知识点数量
        records = LearningRecord.query.filter(
            LearningRecord.user_id == user_id,
            LearningRecord.created_at >= cutoff_date,
            LearningRecord.action_type.in_(['ask', 'code_submit']),
            LearningRecord.knowledge_topics.isnot(None),
            LearningRecord.knowledge_topics != ''
        ).all()

        # 统计不重复知识点数
        unique_topics = set()
        for r in records:
            for t in r.knowledge_topics.split(','):
                t = t.strip()
                if t:
                    unique_topics.add(t)

        view_count = len(unique_topics)  # ⭐ 不重复知识点数
        
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
    def get_all_students_overview(days=30, student_ids=None):
        """获取指定（或全部）学生的学习概览汇总"""
        if student_ids is not None:
            ids = list(student_ids)
        else:
            ids = StatsCalculator._get_student_ids()

        if not ids:
            return {'student_count': 0, 'students': [], 'summary': StatsCalculator._empty_overview(days)}

        # 以下保持原有逻辑，只是把 student_ids 变量替换为 ids
        students_data = []
        total_duration = 0
        total_questions = 0
        total_code = 0
        total_active_days = 0

        for sid in ids:
            user = User.query.get(sid)
            if not user:
                continue
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

        students_data.sort(key=lambda x: x['total_duration_hours'], reverse=True)
        count = len(students_data)

        return {
            'student_count': count,
            'students': students_data,
            'summary': {
                'total_duration_hours': round(total_duration, 1),
                'avg_duration_hours': round(total_duration / max(count, 1), 1),
                'total_questions': total_questions,
                'total_code_submissions': total_code,
                'avg_active_days': round(total_active_days / max(count, 1), 1),
                'period_days': days
            }
        }
    
    @staticmethod
    def get_learning_trend(user_id, days=30):
        """
        获取学习趋势（按天统计）
        ⭐ 学习时长基于心跳精确计算
        ⭐ 新增 avg_score 字段用于代码提交双轴图
        """
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # 生成日期列表
        date_list = []
        for i in range(days):
            d = datetime.utcnow() - timedelta(days=days - 1 - i)
            date_list.append(d.strftime('%Y-%m-%d'))
        
        # 按天统计各类行为
        trend_data = []
        
        for date_str in date_list:
            # 当天的时间范围
            try:
                day_start = datetime.strptime(date_str, '%Y-%m-%d')
            except:
                continue
            day_end = day_start + timedelta(days=1)
            
            # 心跳数 -> 学习时长（小时）
            heartbeat_count = LearningRecord.query.filter(
                LearningRecord.user_id == user_id,
                LearningRecord.action_type == 'heartbeat',
                LearningRecord.created_at >= day_start,
                LearningRecord.created_at < day_end
            ).count()
            duration_hours = round(heartbeat_count / 60, 2)
            
            # 提问次数
            question_count = LearningRecord.query.filter(
                LearningRecord.user_id == user_id,
                LearningRecord.action_type == 'ask',
                LearningRecord.created_at >= day_start,
                LearningRecord.created_at < day_end
            ).count()
            
            # 代码提交
            code_records = LearningRecord.query.filter(
                LearningRecord.user_id == user_id,
                LearningRecord.action_type == 'code_submit',
                LearningRecord.created_at >= day_start,
                LearningRecord.created_at < day_end
            ).all()
            
            code_count = len(code_records)
            correct_count = sum(1 for r in code_records if r.is_correct)
            accuracy = round((correct_count / code_count * 100), 1) if code_count > 0 else None
            
            # ⭐⭐⭐ 新增：计算平均分数 ⭐⭐⭐
            avg_score = None
            if code_records:
                scores = []
                for r in code_records:
                    try:
                        if r.content:
                            content_data = json.loads(r.content)
                            score = content_data.get('score')
                            if score is not None:
                                scores.append(score)
                    except:
                        pass
                if scores:
                    avg_score = round(sum(scores) / len(scores), 1)
            
            # 总活动数（不含心跳）
            total_count = question_count + code_count
            
            # 知识查看
            view_count = LearningRecord.query.filter(
                LearningRecord.user_id == user_id,
                LearningRecord.action_type == 'view_knowledge',
                LearningRecord.created_at >= day_start,
                LearningRecord.created_at < day_end
            ).count()
            
            total_count += view_count
            
            trend_data.append({
                'date': date_str,
                'duration': duration_hours,
                'total_count': total_count,
                'question_count': question_count,
                'code_count': code_count,
                'accuracy': accuracy,
                'avg_score': avg_score,   # ⭐ 新增
                'view_count': view_count,
            })
        
        return trend_data
    
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
    def get_knowledge_chunk_stats(limit: int = 20, user_id: int = None):
        """获取知识块引用热度统计"""
        try:
            if user_id:
                # ⭐ 按学生过滤：统计该学生对话中引用的知识块
                rows = ChatMessage.query.join(
                    ChatSession, ChatMessage.session_id == ChatSession.id
                ).filter(
                    ChatSession.user_id == user_id,
                    ChatMessage.referenced_chunks.isnot(None),
                    ChatMessage.referenced_chunks != '[]',
                    ChatMessage.referenced_chunks != ''
                ).with_entities(ChatMessage.referenced_chunks).all()

                chunk_count = {}
                for row in rows:
                    try:
                        ids = json.loads(row[0]) if row[0] else []
                        for cid in ids:
                            try:
                                cid_int = int(cid)
                                chunk_count[cid_int] = chunk_count.get(cid_int, 0) + 1
                            except (ValueError, TypeError):
                                pass
                    except Exception:
                        pass

                if not chunk_count:
                    return {'items': [], 'chunks': [], 'total_retrieved': 0,
                            'total_chunks': 0, 'total_refs': 0}

                chunks = KnowledgeChunk.query.filter(
                    KnowledgeChunk.id.in_(list(chunk_count.keys())),
                    KnowledgeChunk.is_active == True
                ).all()

                max_count = max(chunk_count.values(), default=1)
                items = sorted([
                    {
                        'chunk_id': c.id,
                        'source': c.source or '',
                        'chapter': c.chapter or c.source or f'知识块#{c.id}',
                        'section': c.section or '',
                        'has_code': c.has_code or False,
                        'retrieved_count': chunk_count.get(c.id, 0),
                        'heat_rate': round(chunk_count.get(c.id, 0) / max_count * 100, 1),
                    }
                    for c in chunks
                ], key=lambda x: -x['retrieved_count'])[:limit]

            else:
                # 全局统计
                chunks = KnowledgeChunk.query.filter_by(is_active=True)\
                    .order_by(KnowledgeChunk.retrieved_count.desc())\
                    .limit(limit).all()

                max_count = max((c.retrieved_count or 0 for c in chunks), default=1)
                items = [
                    {
                        'chunk_id': c.id,
                        'source': c.source or '',
                        'chapter': c.chapter or c.source or f'知识块#{c.id}',
                        'section': c.section or '',
                        'has_code': c.has_code or False,
                        'retrieved_count': c.retrieved_count or 0,
                        'heat_rate': round((c.retrieved_count or 0) / max_count * 100, 1),
                    }
                    for c in chunks
                    if (c.retrieved_count or 0) > 0
                ]

            total_retrieved = sum(i['retrieved_count'] for i in items)
            return {
                'items': items,
                'chunks': items,
                'total_retrieved': total_retrieved,
                'total_chunks': len(items),
                'total_refs': total_retrieved,
            }

        except Exception as e:
            print(f"❌ get_knowledge_chunk_stats 失败: {e}")
            import traceback
            traceback.print_exc()
            return {'items': [], 'chunks': [], 'total_retrieved': 0,
                    'total_chunks': 0, 'total_refs': 0}
    
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