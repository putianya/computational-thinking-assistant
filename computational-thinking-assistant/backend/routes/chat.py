# -*- coding: utf-8 -*-
"""
聊天路由 Blueprint
包含：chat_stream, clear_context, sessions CRUD
"""
import json
import time
import traceback
from flask import Blueprint, request, jsonify, Response, g, stream_with_context
from models.chat_session import ChatSession
from services.chat_service import ChatService
from services.analytics.data_collector import DataCollector
from utils.decorators import login_required
from extensions import ServiceRegistry

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/api/chat/stream', methods=['POST'])
@login_required
def chat_stream():
    """流式聊天 API"""
    try:
        data = request.get_json()

        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')

        if not user_message:
            return jsonify({'status': 'error', 'message': '消息不能为空'}), 400

        if not session_id:
            session = ChatService.get_or_create_active_session(g.user_id)
            session_id = session.session_id

        request_start_time = time.time()
        print(f"\n{'='*60}")
        print(f"📨 收到流式请求: {user_message[:50]}...")
        print(f"📍 会话: {session_id}")
        print(f"{'='*60}")

        service = ServiceRegistry.get_llm_service()

        try:
            knowledge_topics = None
            DataCollector.record_question(
                user_id=g.user_id,
                session_id=session_id,
                question=user_message,
                knowledge_topics=knowledge_topics
            )
        except Exception as e:
            print(f"⚠️ 记录提问行为失败: {e}")

        def generate():
            chunk_count = 0
            first_chunk_time = None

            try:
                yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"

                for chunk in service.chat_stream(user_message, session_id):
                    chunk_count += 1

                    if first_chunk_time is None:
                        first_chunk_time = time.time()
                        latency = first_chunk_time - request_start_time
                        print(f"⚡ 首字节延迟（请求→首块）: {latency:.2f}秒")

                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"

                yield f"data: {json.dumps({'type': 'done'})}\n\n"

                total_time = time.time() - request_start_time
                print(f"✅ 流式响应完成: 共 {chunk_count} 个块，总耗时 {total_time:.2f}秒")

            except Exception as e:
                print(f"❌ 流式生成错误: {e}")
                traceback.print_exc()
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive',
                'Content-Type': 'text/event-stream; charset=utf-8',
            }
        )

    except Exception as e:
        print(f"❌ 处理请求错误: {e}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@chat_bp.route('/api/chat/clear-context', methods=['POST'])
@login_required
def clear_context():
    """清除会话上下文（归档当前会话，创建新会话）"""
    try:
        new_session = ChatService.archive_and_create_new(g.user_id)

        print(f"🗑️ 已归档旧会话，创建新会话: {new_session.session_id}")

        return jsonify({
            'status': 'success',
            'message': '上下文已清除',
            'session_id': new_session.session_id
        })

    except Exception as e:
        print(f"❌ 清除上下文失败: {e}")
        return jsonify({'status': 'error', 'message': f'清除上下文失败: {str(e)}'}), 500


@chat_bp.route('/api/sessions', methods=['GET'])
@login_required
def get_sessions():
    """获取当前用户的所有会话列表"""
    try:
        sessions = ChatService.get_user_sessions(g.user_id)

        return jsonify({
            'status': 'success',
            'sessions': sessions
        }), 200

    except Exception as e:
        print(f"❌ 获取会话列表失败: {e}")
        return jsonify({'status': 'error', 'message': f'获取会话列表失败: {str(e)}'}), 500


@chat_bp.route('/api/sessions/<session_id>/messages', methods=['GET'])
@login_required
def get_session_messages_route(session_id):
    """
    获取指定会话的消息

    查询参数：
    - limit: 返回数量（默认 None = 全部）
    """
    try:
        limit = request.args.get('limit', None, type=int)

        session = ChatSession.query.filter_by(
            session_id=session_id,
            user_id=g.user_id
        ).first()

        if not session:
            return jsonify({
                'status': 'error',
                'message': '会话不存在或无权访问'
            }), 404

        messages = ChatService.get_session_messages(session_id, limit=limit)

        return jsonify({
            'status': 'success',
            'messages': messages
        }), 200

    except Exception as e:
        print(f"❌ 获取会话消息失败: {e}")
        return jsonify({'status': 'error', 'message': f'获取消息失败: {str(e)}'}), 500


@chat_bp.route('/api/sessions/<session_id>/rename', methods=['PUT'])
@login_required
def rename_session(session_id):
    """重命名会话"""
    try:
        data = request.get_json()
        new_title = data.get('title', '').strip()

        if not new_title:
            return jsonify({
                'status': 'error',
                'message': '标题不能为空'
            }), 400

        if len(new_title) > 200:
            return jsonify({
                'status': 'error',
                'message': '标题长度不能超过200字符'
            }), 400

        print(f"\n{'='*60}")
        print(f"✏️ 重命名会话请求")
        print(f"   用户ID: {g.user_id}")
        print(f"   会话ID: {session_id}")
        print(f"   新标题: {new_title}")

        result = ChatService.rename_session(session_id, g.user_id, new_title)

        if result:
            print(f"✅ 重命名成功")
            print(f"{'='*60}\n")

            return jsonify({
                'status': 'success',
                'message': '重命名成功',
                'session': result.to_dict()
            })
        else:
            print(f"❌ 会话不存在")
            print(f"{'='*60}\n")

            return jsonify({
                'status': 'error',
                'message': '会话不存在或无权修改'
            }), 404

    except Exception as e:
        print(f"❌ 重命名会话失败: {str(e)}")
        traceback.print_exc()
        print(f"{'='*60}\n")

        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@chat_bp.route('/api/sessions/<session_id>/activate', methods=['POST'])
@login_required
def activate_session(session_id):
    """激活指定会话"""
    try:
        user_id = g.user_id

        print(f"\n{'='*60}")
        print(f"🔄 激活会话请求")
        print(f"   用户ID: {user_id}")
        print(f"   会话ID: {session_id}")

        result = ChatService.switch_session(user_id, session_id)

        print(f"✅ 会话激活成功")
        print(f"{'='*60}\n")

        return jsonify({
            'status': 'success',
            'session': result['session'],
            'messages': result['messages']
        }), 200

    except ValueError as e:
        print(f"❌ 会话不存在: {str(e)}")
        print(f"{'='*60}\n")

        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 404

    except Exception as e:
        print(f"❌ 激活会话失败: {str(e)}")
        traceback.print_exc()
        print(f"{'='*60}\n")

        return jsonify({
            'status': 'error',
            'message': f'激活会话失败: {str(e)}'
        }), 500


@chat_bp.route('/api/sessions/new', methods=['POST'])
@login_required
def create_new_session():
    """归档当前会话，创建新会话"""
    try:
        new_session = ChatService.archive_and_create_new(g.user_id)

        return jsonify({
            'status': 'success',
            'session': new_session
        }), 201

    except Exception as e:
        print(f"❌ 创建新会话失败: {e}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'创建新会话失败: {str(e)}'}), 500


@chat_bp.route('/api/sessions/<session_id>', methods=['DELETE'])
@login_required
def delete_session_route(session_id):
    """删除指定会话"""
    try:
        user_id = g.user_id

        print(f"\n{'='*60}")
        print(f"🗑️ 删除会话请求")
        print(f"   用户ID: {user_id}")
        print(f"   会话ID: {session_id}")

        session = ChatService.get_session_detail(session_id, user_id)
        if not session:
            print(f"❌ 会话不存在或无权访问")
            print(f"{'='*60}\n")

            return jsonify({
                'status': 'error',
                'message': '会话不存在或无权访问'
            }), 404

        print(f"   会话标题: {session.title}")
        print(f"   是否活跃: {session.is_active}")

        print(f"🗑️ 执行删除操作...")
        success = ChatService.delete_session(session_id, user_id)

        if success:
            print(f"✅ 会话删除成功")
            print(f"{'='*60}\n")

            return jsonify({
                'status': 'success',
                'message': '会话已删除'
            }), 200
        else:
            print(f"❌ 删除失败")
            print(f"{'='*60}\n")

            return jsonify({
                'status': 'error',
                'message': '删除会话失败'
            }), 500

    except Exception as e:
        print(f"❌ 删除会话异常: {str(e)}")
        traceback.print_exc()
        print(f"{'='*60}\n")

        return jsonify({
            'status': 'error',
            'message': f'删除会话时发生错误: {str(e)}'
        }), 500
