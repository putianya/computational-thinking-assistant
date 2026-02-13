# -*- coding: utf-8 -*-
"""
薄弱环节分析器
识别用户学习中的薄弱点并提供改进建议
"""

from datetime import datetime, timedelta
from database import db
from models.learning_record import LearningRecord
from models.error_pattern import ErrorPattern
import json


class WeaknessAnalyzer:
    """薄弱环节分析器"""
    
    @staticmethod
    def analyze_weaknesses(user_id, days=30):
        """
        综合分析用户的薄弱环节
        
        Args:
            user_id: 用户ID
            days: 分析时间范围（天）
        
        Returns:
            dict: 薄弱环节分析结果
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        analysis = {
            'weak_topics': WeaknessAnalyzer._analyze_weak_topics(user_id, cutoff_date),
            'frequent_errors': WeaknessAnalyzer._analyze_frequent_errors(user_id),
            'low_performance_areas': WeaknessAnalyzer._analyze_low_performance(user_id, cutoff_date),
            'suggestions': []
        }
        
        # 生成改进建议
        analysis['suggestions'] = WeaknessAnalyzer._generate_suggestions(analysis)
        
        return analysis
    
    @staticmethod
    def _analyze_weak_topics(user_id, cutoff_date):
        """
        分析薄弱知识点（正确率低于60%）
        
        Args:
            user_id: 用户ID
            cutoff_date: 截止日期
        
        Returns:
            list: 薄弱知识点列表
        """
        # 获取代码提交记录
        records = LearningRecord.query.filter_by(
            user_id=user_id,
            action_type='code_submit'
        ).filter(
            LearningRecord.created_at >= cutoff_date,
            LearningRecord.knowledge_topics.isnot(None)
        ).all()
        
        # 统计每个知识点的表现
        topic_performance = {}
        
        for record in records:
            topics = record.knowledge_topics.split(',') if record.knowledge_topics else []
            
            for topic in topics:
                topic = topic.strip()
                if not topic:
                    continue
                
                if topic not in topic_performance:
                    topic_performance[topic] = {
                        'topic': topic,
                        'total': 0,
                        'correct': 0,
                        'incorrect': 0
                    }
                
                topic_performance[topic]['total'] += 1
                
                if record.is_correct:
                    topic_performance[topic]['correct'] += 1
                else:
                    topic_performance[topic]['incorrect'] += 1
        
        # 计算正确率并筛选薄弱点
        weak_topics = []
        
        for topic, stats in topic_performance.items():
            if stats['total'] < 3:  # 至少3次记录才有参考价值
                continue
            
            accuracy = (stats['correct'] / stats['total']) * 100
            
            if accuracy < 60:  # 正确率低于60%视为薄弱
                weak_topics.append({
                    'topic': topic,
                    'accuracy': round(accuracy, 1),
                    'total_attempts': stats['total'],
                    'correct_count': stats['correct'],
                    'severity': 'high' if accuracy < 40 else 'medium'
                })
        
        # 按正确率排序（最低的在前）
        weak_topics.sort(key=lambda x: x['accuracy'])
        
        return weak_topics
    
    @staticmethod
    def _analyze_frequent_errors(user_id):
        """
        分析高频错误模式（出现3次以上）
        
        Args:
            user_id: 用户ID
        
        Returns:
            list: 高频错误列表
        """
        patterns = ErrorPattern.query.filter(
            ErrorPattern.user_id == user_id,
            ErrorPattern.occurrence_count >= 3
        ).order_by(
            ErrorPattern.occurrence_count.desc()
        ).limit(10).all()
        
        frequent_errors = []
        
        for pattern in patterns:
            # 计算最近出现时间
            days_since_last = None
            if pattern.last_seen:
                days_since_last = (datetime.utcnow() - pattern.last_seen).days
            
            frequent_errors.append({
                'error_type': pattern.error_type,
                'description': pattern.error_description,
                'occurrence_count': pattern.occurrence_count,
                'related_topic': pattern.related_topic,
                'days_since_last': days_since_last,
                'is_recent': days_since_last is not None and days_since_last <= 7
            })
        
        return frequent_errors
    
    @staticmethod
    def _analyze_low_performance(user_id, cutoff_date):
        """
        分析低分数提交（评分 < 60）
        
        Args:
            user_id: 用户ID
            cutoff_date: 截止日期
        
        Returns:
            dict: 低分数提交分析
        """
        records = LearningRecord.query.filter_by(
            user_id=user_id,
            action_type='code_submit'
        ).filter(
            LearningRecord.created_at >= cutoff_date
        ).all()
        
        low_scores = []
        score_distribution = {'F': 0, 'D': 0, 'C': 0, 'B': 0, 'A': 0}
        
        for record in records:
            try:
                content = json.loads(record.content) if record.content else {}
                score = content.get('score', 0)
                level = content.get('level', 'F')
                
                # 统计评级分布
                if level in score_distribution:
                    score_distribution[level] += 1
                
                # 记录低分提交
                if score < 60:
                    low_scores.append({
                        'score': score,
                        'level': level,
                        'date': record.created_at.isoformat(),
                        'topics': record.knowledge_topics.split(',') if record.knowledge_topics else []
                    })
            except:
                continue
        
        total_submissions = len(records)
        low_score_count = len(low_scores)
        low_score_rate = (low_score_count / total_submissions * 100) if total_submissions > 0 else 0
        
        return {
            'total_submissions': total_submissions,
            'low_score_count': low_score_count,
            'low_score_rate': round(low_score_rate, 1),
            'score_distribution': score_distribution,
            'recent_low_scores': low_scores[-5:]  # 最近5次低分
        }
    
    @staticmethod
    def _generate_suggestions(analysis):
        """
        根据分析结果生成改进建议
        
        Args:
            analysis: 分析结果字典
        
        Returns:
            list: 改进建议列表
        """
        suggestions = []
        
        # 1. 针对薄弱知识点的建议
        weak_topics = analysis.get('weak_topics', [])
        if weak_topics:
            top_weak = weak_topics[0]
            suggestions.append({
                'type': 'weak_topic',
                'priority': 'high',
                'title': f'重点复习：{top_weak["topic"]}',
                'description': f'该知识点正确率仅 {top_weak["accuracy"]}%，建议重点复习相关内容',
                'action': '查看知识库相关章节'
            })
        
        # 2. 针对高频错误的建议
        frequent_errors = analysis.get('frequent_errors', [])
        if frequent_errors:
            top_error = frequent_errors[0]
            
            # 检查是否是最近错误
            if top_error.get('is_recent'):
                priority = 'high'
                title = f'注意：{top_error["error_type"]}类错误'
            else:
                priority = 'medium'
                title = f'历史问题：{top_error["error_type"]}类错误'
            
            suggestions.append({
                'type': 'frequent_error',
                'priority': priority,
                'title': title,
                'description': f'"{top_error["description"]}" 已出现 {top_error["occurrence_count"]} 次',
                'action': '练习相关题目以加强理解'
            })
        
        # 3. 针对低分率的建议
        low_perf = analysis.get('low_performance_areas', {})
        low_score_rate = low_perf.get('low_score_rate', 0)
        
        if low_score_rate > 50:
            suggestions.append({
                'type': 'low_performance',
                'priority': 'high',
                'title': '代码质量需要提升',
                'description': f'近期 {low_score_rate:.1f}% 的代码提交评分低于60分',
                'action': '建议从基础知识开始系统复习'
            })
        elif low_score_rate > 30:
            suggestions.append({
                'type': 'low_performance',
                'priority': 'medium',
                'title': '代码质量有待提高',
                'description': f'近期 {low_score_rate:.1f}% 的代码提交评分偏低',
                'action': '多做练习，注意代码规范'
            })
        
        # 4. 鼓励性建议（如果表现不错）
        if not suggestions:
            suggestions.append({
                'type': 'encouragement',
                'priority': 'low',
                'title': '保持良好状态',
                'description': '近期学习状态良好，继续保持！',
                'action': '可以尝试更有挑战性的题目'
            })
        
        return suggestions
    
    @staticmethod
    def get_improvement_plan(user_id, days=30):
        """
        生成个性化改进计划
        
        Args:
            user_id: 用户ID
            days: 分析时间范围
        
        Returns:
            dict: 改进计划
        """
        # 获取薄弱环节分析
        weaknesses = WeaknessAnalyzer.analyze_weaknesses(user_id, days)
        
        # 生成分阶段计划
        plan = {
            'stage1': {
                'title': '第一阶段：夯实基础（1-2周）',
                'focus': [],
                'resources': []
            },
            'stage2': {
                'title': '第二阶段：强化练习（2-3周）',
                'focus': [],
                'resources': []
            },
            'stage3': {
                'title': '第三阶段：综合提升（持续）',
                'focus': [],
                'resources': []
            }
        }
        
        # 填充第一阶段：针对最薄弱的知识点
        weak_topics = weaknesses.get('weak_topics', [])
        if weak_topics:
            for topic in weak_topics[:3]:  # 最多3个
                plan['stage1']['focus'].append(topic['topic'])
                plan['stage1']['resources'].append(f'复习 {topic["topic"]} 相关章节')
        
        # 填充第二阶段：针对高频错误
        frequent_errors = weaknesses.get('frequent_errors', [])
        if frequent_errors:
            error_types = set(e['error_type'] for e in frequent_errors[:3])
            plan['stage2']['focus'] = list(error_types)
            plan['stage2']['resources'].append('多做代码练习，注意避免常见错误')
        
        # 填充第三阶段：综合提升
        plan['stage3']['focus'].append('代码规范')
        plan['stage3']['focus'].append('算法复杂度')
        plan['stage3']['resources'].append('参与代码评审，学习最佳实践')
        
        return plan