# -*- coding: utf-8 -*-
"""
学习数据采集服务
只采集学生角色的用户行为，忽略教师和管理员
"""
import json
from datetime import datetime
from database import db
from models.learning_record import LearningRecord
from models.error_pattern import ErrorPattern
from models.user import User


class DataCollector:
    """
    学习数据采集服务
    
    ⭐⭐⭐ 核心规则：只记录学生(student)的学习行为 ⭐⭐⭐
    
    功能：
    1. 记录用户提问行为
    2. 记录代码提交和分析结果
    3. 记录错误模式
    4. 记录知识点查看行为
    5. 记录学习时长心跳
    """
    
    @staticmethod
    def _is_student(user_id):
        """
        检查用户是否为学生角色
        
        Args:
            user_id: 用户ID
        
        Returns:
            bool: 是否为学生
        """
        try:
            user = User.query.get(user_id)
            if not user:
                print(f"⚠️ 用户 {user_id} 不存在，跳过记录")
                return False
            if user.role != 'student':
                print(f"⏭️ 用户 {user.username}({user.role}) 非学生，跳过记录")
                return False
            return True
        except Exception as e:
            print(f"❌ 检查用户角色失败: {e}")
            return False
    
    @staticmethod
    def record_question(user_id, session_id, question, knowledge_topics=None):
        """
        记录提问行为（仅学生）
        """
        try:
            # ⭐ 只记录学生
            if not DataCollector._is_student(user_id):
                return None
            
            content = json.dumps({
                'question': question,
                'question_length': len(question)
            }, ensure_ascii=False)
            
            topics_str = None
            if knowledge_topics and isinstance(knowledge_topics, list):
                topics_str = ','.join(knowledge_topics)
            
            record = LearningRecord(
                user_id=user_id,
                session_id=session_id,
                action_type='ask',
                content=content,
                knowledge_topics=topics_str,
                created_at=datetime.utcnow()
            )
            
            db.session.add(record)
            db.session.commit()
            
            print(f"✅ 记录提问行为: User {user_id}, Session {session_id}")
            return record
            
        except Exception as e:
            print(f"❌ 记录提问行为失败: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def record_code_submission(user_id, session_id, code, result, knowledge_topics=None):
        """
        记录代码提交行为（仅学生）
        """
        try:
            # ⭐ 只记录学生
            if not DataCollector._is_student(user_id):
                return None
            
            # 1. 提取错误模式
            if result.get('syntax_check') and not result['syntax_check'].get('valid', True):
                errors = result['syntax_check'].get('errors', [])
                for error in errors:
                    DataCollector._record_error_pattern(
                        user_id, 'syntax',
                        error.get('message', '未知语法错误'),
                        error.get('related_topic')
                    )
            
            # 2. 提取AI分析中的问题
            if result.get('ai_analysis') and result['ai_analysis'].get('problems'):
                for problem in result['ai_analysis']['problems']:
                    if problem.get('severity') in ['error', 'warning']:
                        DataCollector._record_error_pattern(
                            user_id, 'logic',
                            problem.get('description', '未知问题'),
                            problem.get('related_topic')
                        )
            
            # 3. 构建学习记录
            score = result.get('score', 0)
            content = json.dumps({
                'code_length': len(code),
                'score': score,
                'level': result.get('level', 'F'),
                'has_errors': not result.get('syntax_check', {}).get('valid', True),
                'problem_count': len(result.get('ai_analysis', {}).get('problems', []))
            }, ensure_ascii=False)
            
            # 4. 处理知识点
            topics_str = None
            if knowledge_topics and isinstance(knowledge_topics, list):
                topics_str = ','.join(knowledge_topics)
            elif result.get('features', {}).get('functions'):
                topics_str = ','.join(result['features']['functions'][:5])
            
            # 5. 创建学习记录
            record = LearningRecord(
                user_id=user_id,
                session_id=session_id,
                action_type='code_submit',
                content=content,
                knowledge_topics=topics_str,
                is_correct=score >= 60,
                created_at=datetime.utcnow()
            )
            
            db.session.add(record)
            db.session.commit()
            
            print(f"✅ 记录代码提交: User {user_id}, Score {score}")
            return record
            
        except Exception as e:
            print(f"❌ 记录代码提交失败: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def record_knowledge_view(user_id, session_id, knowledge_title, duration_seconds=None):
        """
        记录知识点查看行为（仅学生）
        """
        try:
            if not DataCollector._is_student(user_id):
                return None
            
            content = json.dumps({
                'title': knowledge_title,
                'duration_seconds': duration_seconds
            }, ensure_ascii=False)
            
            record = LearningRecord(
                user_id=user_id,
                session_id=session_id,
                action_type='view_knowledge',
                content=content,
                duration_seconds=duration_seconds,
                created_at=datetime.utcnow()
            )
            
            db.session.add(record)
            db.session.commit()
            
            print(f"✅ 记录知识查看: User {user_id}, {knowledge_title}")
            return record
            
        except Exception as e:
            print(f"❌ 记录知识查看失败: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def record_heartbeat(user_id, session_id, page='chat'):
        """
        ⭐⭐⭐ 新增：记录心跳（用于精确计算学习时长）⭐⭐⭐
        
        前端每60秒发送一次心跳，每次心跳代表1分钟的学习时长。
        
        Args:
            user_id: 用户ID
            session_id: 当前会话ID（可为空）
            page: 当前页面 ('chat', 'code', 'knowledge')
        
        Returns:
            LearningRecord 或 None
        """
        try:
            if not DataCollector._is_student(user_id):
                return None
            
            content = json.dumps({
                'page': page,
                'interval_seconds': 60
            }, ensure_ascii=False)
            
            record = LearningRecord(
                user_id=user_id,
                session_id=session_id,
                action_type='heartbeat',
                content=content,
                duration_seconds=60,  # 每次心跳代表60秒
                created_at=datetime.utcnow()
            )
            
            db.session.add(record)
            db.session.commit()
            
            # 心跳日志太频繁，只在debug级别打印
            return record
            
        except Exception as e:
            print(f"❌ 记录心跳失败: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def _record_error_pattern(user_id, error_type, description, related_topic=None):
        """
        记录错误模式（内部方法，不需要重复检查角色）
        """
        try:
            existing = ErrorPattern.query.filter_by(
                user_id=user_id,
                error_type=error_type,
                error_description=description
            ).first()
            
            if existing:
                existing.occurrence_count += 1
                existing.last_seen = datetime.utcnow()
                db.session.commit()
                return existing
            else:
                pattern = ErrorPattern(
                    user_id=user_id,
                    error_type=error_type,
                    error_description=description,
                    related_topic=related_topic,
                    occurrence_count=1,
                    first_seen=datetime.utcnow(),
                    last_seen=datetime.utcnow()
                )
                db.session.add(pattern)
                db.session.commit()
                return pattern
                
        except Exception as e:
            print(f"❌ 记录错误模式失败: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def record_chat_with_knowledge(user_id, session_id, message, knowledge_used):
        """记录使用知识库的对话（仅学生）"""
        try:
            if not DataCollector._is_student(user_id):
                return None
            
            content = json.dumps({
                'message_preview': message[:100],
                'knowledge_count': len(knowledge_used) if knowledge_used else 0,
                'knowledge_titles': [k.get('title', '') for k in (knowledge_used or [])][:5]
            }, ensure_ascii=False)
            
            record = LearningRecord(
                user_id=user_id,
                session_id=session_id,
                action_type='chat_with_knowledge',
                content=content,
                created_at=datetime.utcnow()
            )
            
            db.session.add(record)
            db.session.commit()
            return record
            
        except Exception as e:
            print(f"❌ 记录知识库对话失败: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_user_activity_summary(user_id, days=7):
        """获取用户最近的活动摘要"""
        try:
            from datetime import timedelta
            from sqlalchemy import func
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # 按类型统计
            stats = db.session.query(
                LearningRecord.action_type,
                func.count(LearningRecord.id)
            ).filter(
                LearningRecord.user_id == user_id,
                LearningRecord.created_at >= cutoff_date
            ).group_by(LearningRecord.action_type).all()
            
            result = {
                'total': 0,
                'ask': 0,
                'code_submit': 0,
                'view_knowledge': 0,
                'heartbeat': 0,
                'chat_with_knowledge': 0
            }
            
            for action_type, count in stats:
                result[action_type] = count
                if action_type != 'heartbeat':  # 心跳不计入总数
                    result['total'] += count
            
            # 计算学习时长（心跳数 × 60秒）
            result['study_duration_minutes'] = result['heartbeat']
            result['study_duration_hours'] = round(result['heartbeat'] / 60, 1)
            
            return result
            
        except Exception as e:
            print(f"❌ 获取活动摘要失败: {e}")
            return {'total': 0, 'study_duration_hours': 0}
    
    @staticmethod
    def cleanup_old_records(days=90):
        """清理旧的学习记录"""
        try:
            from datetime import timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            deleted = LearningRecord.query.filter(
                LearningRecord.created_at < cutoff_date
            ).delete()
            
            db.session.commit()
            print(f"🗑️ 清理了 {deleted} 条旧学习记录")
            return deleted
            
        except Exception as e:
            print(f"❌ 清理学习记录失败: {e}")
            db.session.rollback()
            return 0
