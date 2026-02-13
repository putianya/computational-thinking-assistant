# -*- coding: utf-8 -*-
"""
学习数据采集服务
自动收集和记录用户的学习行为，用于后续分析和报告生成
"""

import json
from datetime import datetime
from database import db
from models.learning_record import LearningRecord
from models.error_pattern import ErrorPattern


class DataCollector:
    """
    学习数据采集服务
    
    功能：
    1. 记录用户提问行为
    2. 记录代码提交和分析结果
    3. 记录错误模式
    4. 记录知识点查看行为
    """
    
    @staticmethod
    def record_question(user_id, session_id, question, knowledge_topics=None):
        """
        记录提问行为
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            question: 问题内容
            knowledge_topics: 涉及的知识点列表
        
        Returns:
            LearningRecord: 创建的学习记录
        """
        try:
            # 构建内容JSON
            content = json.dumps({
                'question': question,
                'question_length': len(question)
            }, ensure_ascii=False)
            
            # 处理知识点
            topics_str = None
            if knowledge_topics and isinstance(knowledge_topics, list):
                topics_str = ','.join(knowledge_topics)
            
            # 创建学习记录
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
        记录代码提交行为
        
        Args:
            user_id: 用户ID
            session_id: 会话ID（可为空）
            code: 提交的代码
            result: 代码分析结果字典
            knowledge_topics: 涉及的知识点列表
        
        Returns:
            LearningRecord: 创建的学习记录
        """
        try:
            # 1. 提取错误模式（如果有错误）
            if result.get('syntax_check') and not result['syntax_check'].get('valid', True):
                errors = result['syntax_check'].get('errors', [])
                for error in errors:
                    DataCollector._record_error_pattern(
                        user_id=user_id,
                        error_type='syntax',
                        description=error.get('message', '语法错误'),
                        related_topic=error.get('related_topic')
                    )
            
            # 2. 提取AI分析中的问题（如果有）
            if result.get('ai_analysis') and result['ai_analysis'].get('problems'):
                problems = result['ai_analysis']['problems']
                for problem in problems:
                    severity = problem.get('severity', 'warning')
                    if severity == 'error':
                        error_type = 'logic'
                    else:
                        error_type = 'concept'
                    
                    DataCollector._record_error_pattern(
                        user_id=user_id,
                        error_type=error_type,
                        description=problem.get('description', '未知问题'),
                        related_topic=problem.get('related_topic')
                    )
            
            # 3. 构建学习记录内容
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
                # 如果没有显式指定知识点，从代码特征中提取
                functions = result['features']['functions']
                if functions:
                    topics_str = ','.join(functions[:5])  # 最多取5个函数名
            
            # 5. 创建学习记录
            record = LearningRecord(
                user_id=user_id,
                session_id=session_id,
                action_type='code_submit',
                content=content,
                knowledge_topics=topics_str,
                is_correct=score >= 60,  # 60分以上视为正确
                created_at=datetime.utcnow()
            )
            
            db.session.add(record)
            db.session.commit()
            
            print(f"✅ 记录代码提交: User {user_id}, Score {score}")
            return record
            
        except Exception as e:
            print(f"❌ 记录代码提交失败: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return None
    
    @staticmethod
    def record_knowledge_view(user_id, session_id, knowledge_title, duration_seconds=None):
        """
        记录知识点查看行为
        
        Args:
            user_id: 用户ID
            session_id: 会话ID（可为空）
            knowledge_title: 知识点标题
            duration_seconds: 查看时长（秒）
        
        Returns:
            LearningRecord: 创建的学习记录
        """
        try:
            content = json.dumps({
                'knowledge_title': knowledge_title
            }, ensure_ascii=False)
            
            record = LearningRecord(
                user_id=user_id,
                session_id=session_id,
                action_type='view_knowledge',
                content=content,
                knowledge_topics=knowledge_title,
                duration_seconds=duration_seconds,
                created_at=datetime.utcnow()
            )
            
            db.session.add(record)
            db.session.commit()
            
            print(f"✅ 记录知识查看: User {user_id}, Topic {knowledge_title}")
            return record
            
        except Exception as e:
            print(f"❌ 记录知识查看失败: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def _record_error_pattern(user_id, error_type, description, related_topic=None):
        """
        记录错误模式（内部方法）
        自动累加计数，如果相同错误已存在
        
        Args:
            user_id: 用户ID
            error_type: 错误类型 ('syntax', 'logic', 'concept')
            description: 错误描述
            related_topic: 相关知识点
        
        Returns:
            ErrorPattern: 错误模式对象
        """
        try:
            # 查找是否已有相同错误模式
            existing = ErrorPattern.query.filter_by(
                user_id=user_id,
                error_type=error_type,
                error_description=description
            ).first()
            
            if existing:
                # 更新现有模式
                existing.occurrence_count += 1
                existing.last_seen = datetime.utcnow()
                
                # 更新相关知识点（如果提供了新的）
                if related_topic and not existing.related_topic:
                    existing.related_topic = related_topic
                
                print(f"📊 更新错误模式: {error_type}, 出现 {existing.occurrence_count} 次")
            else:
                # 创建新的错误模式
                new_pattern = ErrorPattern(
                    user_id=user_id,
                    error_type=error_type,
                    error_description=description,
                    related_topic=related_topic,
                    occurrence_count=1,
                    first_seen=datetime.utcnow(),
                    last_seen=datetime.utcnow()
                )
                db.session.add(new_pattern)
                
                print(f"📝 创建新错误模式: {error_type} - {description}")
                existing = new_pattern
            
            db.session.commit()
            return existing
            
        except Exception as e:
            print(f"❌ 记录错误模式失败: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return None
    
    @staticmethod
    def record_chat_with_knowledge(user_id, session_id, message, knowledge_used):
        """
        记录使用知识库的对话
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            message: 用户消息
            knowledge_used: 使用的知识库文章列表
        
        Returns:
            LearningRecord: 创建的学习记录
        """
        try:
            # 提取知识点标题
            topics = [k.get('title', '') for k in knowledge_used if k.get('title')]
            topics_str = ','.join(topics) if topics else None
            
            content = json.dumps({
                'message': message,
                'knowledge_count': len(knowledge_used),
                'knowledge_titles': topics
            }, ensure_ascii=False)
            
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
            
            print(f"✅ 记录知识库对话: User {user_id}, 使用 {len(knowledge_used)} 个知识点")
            return record
            
        except Exception as e:
            print(f"❌ 记录知识库对话失败: {e}")
            db.session.rollback()
            return None
    
    @staticmethod
    def get_user_activity_summary(user_id, days=7):
        """
        获取用户最近的活动摘要
        
        Args:
            user_id: 用户ID
            days: 统计天数
        
        Returns:
            dict: 活动摘要
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            records = LearningRecord.query.filter(
                LearningRecord.user_id == user_id,
                LearningRecord.created_at >= cutoff_date
            ).all()
            
            summary = {
                'total_actions': len(records),
                'ask_count': sum(1 for r in records if r.action_type == 'ask'),
                'code_submit_count': sum(1 for r in records if r.action_type == 'code_submit'),
                'view_knowledge_count': sum(1 for r in records if r.action_type == 'view_knowledge'),
                'days': days
            }
            
            return summary
            
        except Exception as e:
            print(f"❌ 获取活动摘要失败: {e}")
            return None
    
    @staticmethod
    def cleanup_old_records(days=90):
        """
        清理旧的学习记录（保留指定天数内的记录）
        
        Args:
            days: 保留天数
        
        Returns:
            int: 删除的记录数
        """
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # 删除旧记录
            deleted_count = LearningRecord.query.filter(
                LearningRecord.created_at < cutoff_date
            ).delete()
            
            db.session.commit()
            
            print(f"🗑️ 清理了 {deleted_count} 条旧学习记录")
            return deleted_count
            
        except Exception as e:
            print(f"❌ 清理旧记录失败: {e}")
            db.session.rollback()
            return 0
