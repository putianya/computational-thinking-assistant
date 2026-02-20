# -*- coding: utf-8 -*-
"""
学情报告数据生成器
"""
from datetime import datetime


class ReportGenerator:

    @staticmethod
    def generate_json_report(user_id, days=30):
        """生成学情报告 JSON 数据"""
        try:
            from models.user import User
            from services.analytics.stats_calculator import StatsCalculator
            from services.analytics.weakness_analyzer import WeaknessAnalyzer

            user = User.query.get(user_id)
            if not user:
                return {'error': '用户不存在'}

            overview   = StatsCalculator.get_user_overview(user_id, days) or {}
            trend      = StatsCalculator.get_learning_trend(user_id, days) or {}
            knowledge  = StatsCalculator.get_knowledge_mastery(user_id, days) or {}
            code_quality = StatsCalculator.get_code_quality_trend(user_id, days) or {}
            weaknesses = WeaknessAnalyzer.analyze_weaknesses(user_id, days) or {}

            score           = ReportGenerator._calculate_report_score(overview, weaknesses)
            recommendations = ReportGenerator._generate_recommendations(
                overview, weaknesses, code_quality
            )

            return {
                'user_info': {
                    'id':       user.id,
                    'username': user.username,
                    'nickname': user.nickname or user.username,
                    'name':     user.nickname or user.username,
                },
                'overview':         overview,
                'trend':            trend,
                'knowledge_mastery': knowledge,
                'weaknesses':       weaknesses,
                'code_quality':     code_quality,
                'recommendations':  recommendations,
                'score':            score,
                'generated_at':     datetime.utcnow().isoformat(),
                'period_days':      days,
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'error': str(e)}

    @staticmethod
    def _calculate_report_score(overview, weaknesses):
        """计算综合评分"""
        try:
            days        = overview.get('period_days', 30) or 1
            total_hours = overview.get('total_duration_hours', 0) or 0
            active_days = overview.get('active_days', 0) or 0
            accuracy    = overview.get('accuracy', 0) or 0
            code_count  = overview.get('code_count', 0) or 0
            view_count  = overview.get('view_count', 0) or 0
            question_count = overview.get('question_count', 0) or 0

            # 时长得分（满25分）
            daily_hours  = total_hours / days
            time_score   = round(min(daily_hours / 1.0 * 25, 25), 1)

            # 活跃度（满25分）
            activity_rate  = active_days / days
            activity_score = round(activity_rate * 25, 1)

            # 代码质量（满30分）
            if code_count == 0:
                code_score = 0.0
            else:
                code_score = round(min(accuracy / 100 * 30, 30), 1)

            # 学习广度（满20分）
            knowledge_score = round(min(view_count * 0.5 + question_count * 1.0, 20), 1)

            total = time_score + activity_score + code_score + knowledge_score

            if total >= 90:
                grade, grade_text = 'A', '优秀'
            elif total >= 75:
                grade, grade_text = 'B', '良好'
            elif total >= 60:
                grade, grade_text = 'C', '合格'
            elif total >= 40:
                grade, grade_text = 'D', '待提升'
            else:
                grade, grade_text = 'F', '需努力'

            return {
                'total':      round(total, 1),
                'grade':      grade,
                'grade_text': grade_text,
                'breakdown':  {
                    'time':      time_score,
                    'activity':  activity_score,
                    'code':      code_score,
                    'knowledge': knowledge_score,
                }
            }
        except Exception:
            return {
                'total': 0.0, 'grade': 'F', 'grade_text': '需努力',
                'breakdown': {'time': 0, 'activity': 0, 'code': 0, 'knowledge': 0}
            }

    @staticmethod
    def _generate_recommendations(overview, weaknesses, code_quality):
        """生成学习建议"""
        recommendations = []
        days           = overview.get('period_days', 30) or 1
        total_hours    = overview.get('total_duration_hours', 0) or 0
        active_days    = overview.get('active_days', 0) or 0
        accuracy       = overview.get('accuracy', 0) or 0
        code_count     = overview.get('code_count', 0) or 0
        question_count = overview.get('question_count', 0) or 0

        daily_hours  = total_hours / days
        active_rate  = active_days / days

        # 时间建议
        if daily_hours < 0.5:
            recommendations.append({
                'type': 'time', 'priority': 'high', 'icon': '⏰',
                'title': '增加学习时长',
                'content': f'当前日均学习 {daily_hours:.1f} 小时，建议每天至少学习1小时。'
            })
        elif daily_hours >= 1.0:
            recommendations.append({
                'type': 'time', 'priority': 'low', 'icon': '⭐',
                'title': '学习时长良好',
                'content': f'日均学习 {daily_hours:.1f} 小时，保持这个节奏！'
            })

        # 活跃度建议
        if active_rate < 0.3:
            recommendations.append({
                'type': 'activity', 'priority': 'high', 'icon': '📅',
                'title': '提高学习频率',
                'content': f'过去 {days} 天仅活跃 {active_days} 天，建议保持每天学习习惯。'
            })

        # 代码建议
        if code_count == 0:
            recommendations.append({
                'type': 'code', 'priority': 'high', 'icon': '💻',
                'title': '开始代码练习',
                'content': '本周期暂无代码提交，多动手实践才能加深理解。'
            })
        elif accuracy < 50:
            recommendations.append({
                'type': 'code', 'priority': 'high', 'icon': '🔧',
                'title': '提升代码正确率',
                'content': f'当前代码正确率 {accuracy}%，可从基础语法开始复习。'
            })
        elif accuracy >= 80:
            recommendations.append({
                'type': 'code', 'priority': 'low', 'icon': '🎯',
                'title': '代码质量优秀',
                'content': f'代码正确率达 {accuracy}%，可尝试更复杂的算法挑战。'
            })

        # 薄弱点建议
        weak_topics = (weaknesses or {}).get('weak_topics', [])
        if weak_topics:
            topic_names = '、'.join([t.get('topic', '') for t in weak_topics[:3]])
            recommendations.append({
                'type': 'knowledge', 'priority': 'high', 'icon': '📚',
                'title': '加强薄弱知识点',
                'content': f'以下知识点需要重点复习：{topic_names}。'
            })

        # 高频错误建议
        frequent_errors = (weaknesses or {}).get('frequent_errors', [])
        if frequent_errors:
            recommendations.append({
                'type': 'error', 'priority': 'medium', 'icon': '⚠️',
                'title': '注意常见错误',
                'content': f'有 {len(frequent_errors)} 类错误反复出现，建议专项练习。'
            })

        # 提问建议
        if question_count == 0:
            recommendations.append({
                'type': 'question', 'priority': 'medium', 'icon': '💬',
                'title': '多向助手提问',
                'content': '遇到不懂的概念可以随时提问，AI助手会为你解答。'
            })

        # 全部良好
        if not recommendations:
            recommendations.append({
                'type': 'praise', 'priority': 'low', 'icon': '🏆',
                'title': '表现优秀！',
                'content': '各项指标均表现良好，继续保持这种学习状态！'
            })

        return recommendations