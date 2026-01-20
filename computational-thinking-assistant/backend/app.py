# -*- coding: utf-8 -*-
"""
Flask 应用主程序 - 后端 API 服务
"""
import sys
import io
import uuid
import json
import os
from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS
from config import Config
from datetime import datetime
from database import db, init_db
from services.auth_service import AuthService
from utils.decorators import login_required
from flask import g

# 设置标准输出为 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 创建 Flask 应用
app = Flask(__name__)
app.config.from_object(Config)

# ⭐ 初始化数据库
init_db(app)

# 启用 CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# 全局服务实例
llm_service = None

def get_llm_service():
    """懒加载 LLM 服务"""
    global llm_service
    if llm_service is None:
        from services.llm_service import LLMService
        llm_service = LLMService()
    return llm_service

# ⭐ 应用启动信息
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    print("=" * 60)
    print("🚀 后端 API 服务启动中...")
    print(f"📍 API 地址: http://127.0.0.1:{Config.PORT}")
    print(f"🤖 AI 模型: {Config.OPENAI_MODEL}")
    print(f"🔗 Base URL: {Config.OPENAI_BASE_URL}")
    print(f"🔑 API 密钥: {'已配置 ✓' if Config.OPENAI_API_KEY else '未配置 ✗'}")
    print(f"⚡ 流式输出: {'启用 ✓' if Config.ENABLE_STREAMING else '禁用 ✗'}")
    print(f"💬 默认上下文长度: {Config.MAX_CONTEXT_FOR_AI} 轮对话")
    print(f"📏 上下文范围: {Config.MIN_CONTEXT_LENGTH}-{Config.MAX_CONTEXT_LENGTH}")
    print(f"💾 每会话最大消息数: {Config.MAX_MESSAGES_PER_SESSION}")
    print("=" * 60)

# ============ API 路由 ============

@app.route('/api/test', methods=['GET'])
def test_api():
    """测试 API"""
    return jsonify({
        'status': 'success',
        'message': '欢迎来到计算思维助手系统！',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'version': '1.0.0',
        'python_version': '3.12',
        'openai_configured': bool(Config.OPENAI_API_KEY),
        'streaming_enabled': Config.ENABLE_STREAMING
    })

# ========== 聊天相关路由 ==========

@app.route('/api/chat/stream', methods=['POST'])
@login_required
def chat_stream():
    """流式聊天 API"""
    try:
        data = request.get_json()
        
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')
        max_context = data.get('max_context', Config.MAX_CONTEXT_FOR_AI)
        
        if not user_message:
            return jsonify({'status': 'error', 'message': '消息不能为空'}), 400
        
        # ⭐ 如果没有 session_id，创建新会话
        if not session_id:
            from services.chat_service import ChatService
            session = ChatService.get_or_create_active_session(g.user_id)
            session_id = session.session_id
            print(f"✅ 创建新会话: {session_id}")
        
        import time
        start_time = time.time()
        print(f"📨 收到流式请求: {user_message[:50]}... (上下文: {max_context} 轮)")
        
        service = get_llm_service()
        
        def generate():
            try:
                # ⭐ 先发送 session_id
                yield f"data: {json.dumps({'type': 'session', 'session_id': session_id}, ensure_ascii=False)}\n\n"
                
                first_chunk_time = None
                chunk_count = 0
                
                # ⭐ 调用 LLMService（它会自动保存消息）
                for content in service.chat_stream(user_message, session_id, max_context):
                    if chunk_count == 0:
                        first_chunk_time = time.time()
                        print(f"⚡ 首字节延迟: {first_chunk_time - start_time:.2f}秒")
                    
                    chunk_count += 1
                    chunk_data = json.dumps({'type': 'content', 'content': content}, ensure_ascii=False)
                    yield f"data: {chunk_data}\n\n"
                
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
                
                total_time = time.time() - start_time
                print(f"✅ 流式响应完成: 共 {chunk_count} 个块，总耗时 {total_time:.2f}秒")
                
            except Exception as e:
                print(f"❌ 流式生成错误: {str(e)}")
                error_data = json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)
                yield f"data: {error_data}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
        
    except Exception as e:
        print(f"❌ 处理流式请求时出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'处理请求时出错: {str(e)}'}), 500

@app.route('/api/chat/clear-context', methods=['POST'])
@login_required
def clear_context():
    """清除会话上下文（归档当前会话，创建新会话）"""
    try:
        from services.chat_service import ChatService
        
        # ⭐ 归档当前会话，创建新会话
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

@app.route('/api/chat/context-info/<session_id>', methods=['GET'])
@login_required
def get_context_info(session_id):
    """获取当前上下文信息"""
    try:
        from services.chat_service import ChatService
        
        # ⭐ 从数据库获取会话详情
        session_detail = ChatService.get_session_detail(session_id)
        
        if not session_detail:
            return jsonify({'status': 'error', 'message': '会话不存在'}), 404
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'history_length': session_detail['message_count'] // 2,  # 对话轮数
            'max_context': Config.MAX_CONTEXT_FOR_AI,
            'title': session_detail['title']
        })
        
    except Exception as e:
        print(f"❌ 获取上下文信息失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ========== ⭐⭐⭐ 会话管理 API ⭐⭐⭐ ==========

@app.route('/api/sessions', methods=['GET'])
@login_required
def get_sessions():
    """
    获取当前用户的所有会话列表
    
    响应：
    {
        "status": "success",
        "sessions": [
            {"id": 1, "title": "...", "is_active": true, "updated_at": "..."},
            {"id": 2, "title": "...", "is_active": false, "updated_at": "...}
        ]
    }
    """
    try:
        from services.chat_service import ChatService
        
        sessions = ChatService.get_user_sessions(g.user_id)
        
        return jsonify({
            'status': 'success',
            'sessions': sessions
        }), 200
        
    except Exception as e:
        print(f"❌ 获取会话列表失败: {e}")
        return jsonify({'status': 'error', 'message': f'获取会话列表失败: {str(e)}'}), 500

@app.route('/api/sessions/<session_id>/messages', methods=['GET'])
@login_required
def get_session_messages_route(session_id):
    """
    获取指定会话的消息
    
    查询参数：
    - limit: 返回数量（默认50）
    
    响应：
    {
        "status": "success",
        "messages": [
            {"id": 1, "role": "user", "content": "...", "created_at": "..."},
            {"id": 2, "role": "assistant", "content": "...", "created_at": "...}
        ]
    }
    """
    try:
        from services.chat_service import ChatService
        
        # 获取查询参数
        limit = request.args.get('limit', 50, type=int)
        
        # 验证 session_id 是否属于当前用户
        from models.chat_session import ChatSession
        session = ChatSession.query.filter_by(
            session_id=session_id,
            user_id=g.user_id
        ).first()
        
        if not session:
            return jsonify({
                'status': 'error',
                'message': '会话不存在或无权访问'
            }), 404
        
        # 获取消息
        messages = ChatService.get_session_messages(session_id, limit=limit)
        
        return jsonify({
            'status': 'success',
            'messages': messages
        }), 200
        
    except Exception as e:
        print(f"❌ 获取会话消息失败: {e}")
        return jsonify({'status': 'error', 'message': f'获取消息失败: {str(e)}'}), 500

@app.route('/api/sessions/<session_id>/activate', methods=['POST'])
@login_required
def activate_session(session_id):
    """
    切换到指定会话
    
    响应：
    {
        "status": "success",
        "session": {...},
        "messages": [...]
    }
    """
    try:
        from services.chat_service import ChatService
        
        result = ChatService.switch_session(g.user_id, session_id)
        
        return jsonify({
            'status': 'success',
            **result  # 包含 session 和 messages
        }), 200
        
    except ValueError as e:
        # 会话不存在或无权访问
        return jsonify({'status': 'error', 'message': str(e)}), 404
    except Exception as e:
        print(f"❌ 切换会话失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'切换会话失败: {str(e)}'}), 500

@app.route('/api/sessions/new', methods=['POST'])
@login_required
def create_new_session():
    """
    归档当前会话，创建新会话
    
    响应：
    {
        "status": "success",
        "session": {"id": 3, "session_id": "...", "title": "新对话", "is_active": true}
    }
    """
    try:
        from services.chat_service import ChatService
        
        new_session = ChatService.archive_and_create_new(g.user_id)
        
        return jsonify({
            'status': 'success',
            'session': new_session.to_dict(include_messages=False)
        }), 201
        
    except Exception as e:
        print(f"❌ 创建新会话失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'创建新会话失败: {str(e)}'}), 500

@app.route('/api/sessions/<session_id>', methods=['DELETE'])
@login_required
def delete_session_route(session_id):
    """
    删除指定会话及其所有消息
    
    注意：不能删除当前活跃会话
    
    响应：
    {
        "status": "success",
        "message": "会话已删除"
    }
    """
    try:
        from services.chat_service import ChatService
        from models.chat_session import ChatSession
        
        # 检查是否为活跃会话
        session = ChatSession.query.filter_by(
            session_id=session_id,
            user_id=g.user_id
        ).first()
        
        if not session:
            return jsonify({
                'status': 'error',
                'message': '会话不存在或无权访问'
            }), 404
        
        if session.is_active:
            return jsonify({
                'status': 'error',
                'message': '不能删除当前活跃会话，请先切换到其他会话'
            }), 400
        
        # 删除会话
        success = ChatService.delete_session(g.user_id, session_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': '会话已删除'
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': '删除失败'
            }), 500
        
    except Exception as e:
        print(f"❌ 删除会话失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'删除会话失败: {str(e)}'}), 500

# ========== 认证相关路由 ==========

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        nickname = data.get('nickname')
        
        if not username or not password:
            return jsonify({'status': 'error', 'message': '用户名和密码不能为空'}), 400
        
        result = AuthService.register(username, password, email, nickname)
        
        if result['success']:
            return jsonify({
                'status': 'success',
                'message': result['message'],
                'user': result['user']
            }), 201
        else:
            return jsonify({'status': 'error', 'message': result['message']}), 400
            
    except Exception as e:
        print(f"❌ 注册错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'注册失败: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        print("\n" + "=" * 60)
        print("🔍 收到登录请求")
        
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            print("❌ 用户名或密码为空")
            return jsonify({'status': 'error', 'message': '用户名和密码不能为空'}), 400
        
        print(f"👤 尝试登录用户: {username}")
        result = AuthService.login(username, password)
        
        if result['success']:
            print(f"✅ 登录成功: {username}")
            return jsonify({
                'status': 'success',
                'message': result['message'],
                'token': result['token'],
                'user': result['user']
            }), 200
        else:
            print(f"❌ 登录失败: {result['message']}")
            return jsonify({'status': 'error', 'message': result['message']}), 401
            
    except Exception as e:
        print(f"💥 登录异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'登录失败: {str(e)}'}), 500

@app.route('/api/auth/verify', methods=['POST'])
def verify_token():
    """验证 Token"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'status': 'error', 'message': 'Token 不能为空'}), 400
        
        result = AuthService.verify_token(token)
        
        if result['valid']:
            return jsonify({
                'status': 'success',
                'message': result['message'],
                'user_id': result['user_id'],
                'username': result['username']
            }), 200
        else:
            return jsonify({'status': 'error', 'message': result['message']}), 401
            
    except Exception as e:
        print(f"❌ Token 验证错误: {e}")
        return jsonify({'status': 'error', 'message': f'验证失败: {str(e)}'}), 500

@app.route('/api/user/profile', methods=['GET'])
@login_required
def get_user_profile():
    """获取用户信息（需要登录）"""
    try:
        from models.user import User
        user = User.query.get(g.user_id)
        
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        
        return jsonify({'status': 'success', 'user': user.to_dict()}), 200
        
    except Exception as e:
        print(f"❌ 获取用户信息错误: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': '页面不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'status': 'error', 'message': '服务器内部错误'}), 500

if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)