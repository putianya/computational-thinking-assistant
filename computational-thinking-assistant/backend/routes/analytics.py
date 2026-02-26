# -*- coding: utf-8 -*-
"""
学习分析路由 Blueprint
包含：heartbeat, overview, trend, knowledge_mastery, weakness, heatmap, students, chunk_stats, report, pdf
"""
import json
import traceback
from datetime import datetime, timedelta
from io import BytesIO
from flask import Blueprint, request, jsonify, g, send_file
from sqlalchemy import func
from database import db
from models.user import User
from models.learning_record import LearningRecord
from models.knowledge_chunk import KnowledgeChunk
from models.chat_message import ChatMessage
from models.chat_session import ChatSession
from services.analytics.data_collector import DataCollector
from services.analytics.stats_calculator import StatsCalculator
from services.analytics.weakness_analyzer import WeaknessAnalyzer
from services.analytics.report_generator import ReportGenerator
from services.analytics.pdf_generator import PDFReportGenerator
from utils.decorators import login_required, require_permission

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/api/analytics/heartbeat', methods=['POST'])
@login_required
def analytics_heartbeat():
    """
    学习心跳接口
    前端每60秒调用一次，用于精确计算学习时长
    仅记录学生角色
    """
    try:
        data = request.get_json() or {}
        page = data.get('page', 'chat')
        session_id = data.get('session_id')

        record = DataCollector.record_heartbeat(
            user_id=g.user_id,
            session_id=session_id,
            page=page
        )

        return jsonify({
            'status': 'success',
            'recorded': record is not None
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@analytics_bp.route('/api/analytics/overview', methods=['GET'])
@login_required
@require_permission('view_analytics')
def analytics_overview():
    """
    学习概览
    教师/管理员：可查看指定学生或所有学生汇总
    """
    try:
        days = request.args.get('days', 30, type=int)
        target_user_id = request.args.get('user_id', type=int)

        if target_user_id:
            target_user = User.query.get(target_user_id)
            if not target_user or target_user.role != 'student':
                return jsonify({'status': 'error', 'message': '目标用户不是学生'}), 400

            data = StatsCalculator.get_user_overview(target_user_id, days)
        else:
            data = StatsCalculator.get_all_students_overview(days)

        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        print(f"❌ 获取学习概览失败: {e}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@analytics_bp.route('/api/analytics/trend', methods=['GET'])
@login_required
@require_permission('view_analytics')
def analytics_trend():
    """学习趋势（教师/管理员查看指定学生）"""
    try:
        days = request.args.get('days', 30, type=int)
        target_user_id = request.args.get('user_id', type=int)

        if not target_user_id:
            return jsonify({'status': 'success', 'data': []})

        data = StatsCalculator.get_learning_trend(target_user_id, days)
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@analytics_bp.route('/api/analytics/knowledge-mastery', methods=['GET'])
@login_required
@require_permission('view_analytics')
def analytics_knowledge_mastery():
    """知识点掌握度（教师/管理员查看指定学生）"""
    try:
        days = request.args.get('days', 30, type=int)
        target_user_id = request.args.get('user_id', type=int)

        if not target_user_id:
            return jsonify({'status': 'success', 'data': []})

        data = StatsCalculator.get_knowledge_mastery(target_user_id, days)
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@analytics_bp.route('/api/analytics/weakness', methods=['GET'])
@login_required
@require_permission('view_analytics')
def analytics_weakness():
    """薄弱环节分析（教师/管理员查看指定学生）"""
    try:
        days = request.args.get('days', 30, type=int)
        target_user_id = request.args.get('user_id', type=int)

        if not target_user_id:
            return jsonify({'status': 'success', 'data': {}})

        data = WeaknessAnalyzer.analyze_weaknesses(target_user_id, days)
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@analytics_bp.route('/api/analytics/activity-heatmap', methods=['GET'])
@login_required
@require_permission('view_analytics')
def analytics_activity_heatmap():
    """学习活跃热力图数据"""
    try:
        days = request.args.get('days', 30, type=int)
        user_id = request.args.get('user_id', type=int)

        print(f"📅 热力图请求: days={days}, user_id={user_id}")

        if not user_id:
            return jsonify({'status': 'success', 'data': []})

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        rows = db.session.query(
            func.date(LearningRecord.created_at).label('day'),
            func.count(LearningRecord.id).label('count')
        ).filter(
            LearningRecord.user_id == user_id,
            LearningRecord.action_type != 'heartbeat',
            LearningRecord.created_at >= cutoff_date
        ).group_by(
            func.date(LearningRecord.created_at)
        ).order_by(
            func.date(LearningRecord.created_at).asc()
        ).all()

        data = [{'date': str(row.day), 'count': row.count} for row in rows]
        print(f"✅ 热力图结果: {len(data)} 天有记录, user_id={user_id}")
        return jsonify({'status': 'success', 'data': data})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@analytics_bp.route('/api/analytics/students', methods=['GET'])
@login_required
@require_permission('view_analytics')
def analytics_students():
    """获取学生列表（供教师/管理员选择查看）"""
    try:
        students = User.query.filter_by(role='student', is_active=True)\
            .order_by(User.username.asc()).all()

        return jsonify({
            'status': 'success',
            'data': [
                {
                    'id': s.id,
                    'username': s.username,
                    'nickname': s.nickname or s.username,
                    'last_login': s.last_login.isoformat() if s.last_login else None
                }
                for s in students
            ]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@analytics_bp.route('/api/analytics/knowledge-chunk-stats', methods=['GET'])
@login_required
@require_permission('view_analytics')
def analytics_knowledge_chunk_stats():
    """知识块引用热度统计"""
    try:
        limit = request.args.get('limit', 20, type=int)
        user_id = request.args.get('user_id', type=int)

        if user_id:
            subq = db.session.query(
                ChatMessage.referenced_chunks
            ).join(
                ChatSession, ChatMessage.session_id == ChatSession.id
            ).filter(
                ChatSession.user_id == user_id,
                ChatMessage.referenced_chunks.isnot(None),
                ChatMessage.referenced_chunks != '[]',
                ChatMessage.referenced_chunks != ''
            ).all()

            chunk_count = {}
            for row in subq:
                try:
                    ids = json.loads(row[0]) if row[0] else []
                    for cid in ids:
                        chunk_count[cid] = chunk_count.get(cid, 0) + 1
                except Exception:
                    pass

            if not chunk_count:
                return jsonify({'status': 'success', 'data': {
                    'items': [], 'total_refs': 0, 'unique_chunks': 0,
                    'chunks': [], 'total_retrieved': 0, 'total_chunks': 0
                }})

            chunks = KnowledgeChunk.query.filter(
                KnowledgeChunk.id.in_(chunk_count.keys()),
                KnowledgeChunk.is_active == True
            ).all()

            max_count = max(chunk_count.values(), default=1)
            items = sorted([
                {
                    'chunk_id': c.id,
                    'source': c.source or '',
                    'chapter': c.chapter or c.source or f'知识块#{c.id}',
                    'section': c.section or '',
                    'content_preview': (c.content or '')[:80],
                    'has_code': c.has_code or False,
                    'ref_count_in_period': chunk_count.get(c.id, 0),
                    'total_retrieved_count': c.retrieved_count or 0,
                    'heat_rate': round(chunk_count.get(c.id, 0) / max_count * 100, 1),
                    'retrieved_count': chunk_count.get(c.id, 0),
                }
                for c in chunks
            ], key=lambda x: -x['ref_count_in_period'])[:limit]

        else:
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
                    'content_preview': (c.content or '')[:80],
                    'has_code': c.has_code or False,
                    'ref_count_in_period': c.retrieved_count or 0,
                    'total_retrieved_count': c.retrieved_count or 0,
                    'heat_rate': round((c.retrieved_count or 0) / max_count * 100, 1),
                    'retrieved_count': c.retrieved_count or 0,
                }
                for c in chunks
            ]

        total_refs = sum(i['ref_count_in_period'] for i in items)

        data = {
            'items': items,
            'total_refs': total_refs,
            'unique_chunks': len(items),
            'chunks': items,
            'total_retrieved': total_refs,
            'total_chunks': len(items),
        }

        print(f"✅ 知识块热度: {len(items)} 条, user_id={user_id}")
        return jsonify({'status': 'success', 'data': data})

    except Exception as e:
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@analytics_bp.route('/api/analytics/report', methods=['GET'])
@login_required
def get_learning_report():
    """生成学情报告"""
    try:
        days = request.args.get('days', 30, type=int)
        user_id = request.args.get('user_id', type=int)

        current_user = User.query.get(g.user_id)
        if user_id and user_id != g.user_id:
            if not current_user.has_any_permission(['manage_users', 'view_all_sessions']):
                return jsonify({'status': 'error', 'message': '无权限查看他人报告'}), 403
        else:
            user_id = g.user_id

        report = ReportGenerator.generate_json_report(user_id, days)

        if 'error' in report:
            return jsonify({'status': 'error', 'message': report['error']}), 400

        return jsonify({'status': 'success', 'data': report})

    except Exception as e:
        print(f"❌ 生成报告失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@analytics_bp.route('/api/analytics/report/pdf', methods=['GET'])
@login_required
def download_report_pdf():
    """下载 PDF 学情报告"""
    try:
        days = request.args.get('days', 30, type=int)
        user_id_param = request.args.get('user_id', type=int)

        current_user = User.query.get(g.user_id)
        if user_id_param and current_user.role in ['teacher', 'admin']:
            target_user_id = user_id_param
        else:
            target_user_id = g.user_id

        report_data = ReportGenerator.generate_json_report(target_user_id, days)

        if not report_data:
            return jsonify({'status': 'error', 'message': '报告数据生成失败'}), 500

        pdf_gen = PDFReportGenerator()
        pdf_bytes = pdf_gen.generate(report_data)

        user = User.query.get(target_user_id)
        username = (user.nickname or user.username) if user else "student"
        filename = f"学情报告_{username}_{datetime.now().strftime('%Y%m%d')}.pdf"

        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"❌ PDF 生成失败: {e}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'PDF 生成失败: {str(e)}'}), 500
