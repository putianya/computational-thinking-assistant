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
from services.chat_service import ChatService
from services.llm_service import LLMService
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
    print(f"💬 上下文管理: 全部消息（无限制）")  # ⭐ 新增
    print(f"💾 会话消息限制: {'无限制' if Config.MAX_MESSAGES_PER_SESSION is None else Config.MAX_MESSAGES_PER_SESSION}")  # ⭐ 新增
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
        
        # ⭐⭐⭐ 修复：移除 max_context（已不需要） ⭐⭐⭐
        # ❌ 删除这行：max_context = data.get('max_context', Config.MAX_CONTEXT_FOR_AI)
        
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
        # ⭐ 修改日志输出
        print(f"📨 收到流式请求: {user_message[:50]}... (会话: {session_id})")
        
        service = get_llm_service()
        
        def generate():
            try:
                # ⭐ 先发送 session_id
                yield f"data: {json.dumps({'type': 'session', 'session_id': session_id}, ensure_ascii=False)}\n\n"
                
                first_chunk_time = None
                chunk_count = 0
                
                # ⭐⭐⭐ 修复：移除 max_context 参数 ⭐⭐⭐
                # ❌ 旧代码：for content in service.chat_stream(user_message, session_id, max_context):
                # ✅ 新代码：不传 max_context，LLMService 会自动读取全部消息
                for content in service.chat_stream(user_message, session_id):
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
                import traceback
                traceback.print_exc()
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

# ⭐⭐⭐ 删除：/api/chat/context-info 接口（已不需要） ⭐⭐⭐
# ❌ 删除以下整个路由函数：
# @app.route('/api/chat/context-info/<session_id>', methods=['GET'])
# @login_required
# def get_context_info(session_id):
#     ...

# ========== ⭐⭐⭐ 会话管理 API ⭐⭐⭐ ==========

@app.route('/api/sessions', methods=['GET'])
@login_required
def get_sessions():
    """
    获取当前用户的所有会话列表
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
    - limit: 返回数量（默认 None = 全部）
    """
    try:
        from services.chat_service import ChatService
        
        # ⭐ 修改：默认返回全部消息（limit=None）
        limit = request.args.get('limit', None, type=int)
        
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
        
        # 获取消息（全部）
        messages = ChatService.get_session_messages(session_id, limit=limit)
        
        return jsonify({
            'status': 'success',
            'messages': messages
        }), 200
        
    except Exception as e:
        print(f"❌ 获取会话消息失败: {e}")
        return jsonify({'status': 'error', 'message': f'获取消息失败: {str(e)}'}), 500
    

# ========== ⭐⭐⭐ 会话管理 API ⭐⭐⭐ ==========

# ⭐ 新增：重命名会话 API
@app.route('/api/sessions/<session_id>/rename', methods=['PUT'])
@login_required
def rename_session(session_id):
    """
    重命名会话
    """
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
        
        # 调用服务层
        from services.chat_service import ChatService
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
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500



@app.route('/api/sessions/<session_id>/activate', methods=['POST'])
@login_required
def activate_session(session_id):
    """激活指定会话"""
    try:
        user_id = g.user_id
        
        print(f"\n{'='*60}")
        print(f"🔄 激活会话请求")
        print(f"   用户ID: {user_id}")
        print(f"   会话ID: {session_id}")
        
        # 调用服务层
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
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        
        return jsonify({
            'status': 'error',
            'message': f'激活会话失败: {str(e)}'
        }), 500

@app.route('/api/sessions/new', methods=['POST'])
@login_required
def create_new_session():
    """
    归档当前会话，创建新会话
    """
    try:
        from services.chat_service import ChatService
        
        new_session = ChatService.archive_and_create_new(g.user_id)
        
        return jsonify({
            'status': 'success',
            'session': new_session
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
    删除指定会话
    """
    try:
        user_id = g.user_id
        
        print(f"\n{'='*60}")
        print(f"🗑️ 删除会话请求")
        print(f"   用户ID: {user_id}")
        print(f"   会话ID: {session_id}")
        
        # 1. 验证会话所有权
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
        
        # 2. 直接删除会话
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
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        
        return jsonify({
            'status': 'error',
            'message': f'删除会话时发生错误: {str(e)}'
        }), 500

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