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

# 启用 CORS（允许前端跨域请求）
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]  # ⭐ 添加 Authorization
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

# ⭐ 在应用启动时打印信息（只在主进程打印）
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    print("=" * 60)
    print("🚀 后端 API 服务启动中...")
    print(f"📍 API 地址: http://127.0.0.1:{Config.PORT}")
    print(f"🤖 AI 模型: {Config.OPENAI_MODEL}")
    print(f"🔗 Base URL: {Config.OPENAI_BASE_URL}")
    print(f"🔑 API 密钥: {'已配置 ✓' if Config.OPENAI_API_KEY else '未配置 ✗'}")
    print(f"⚡ 流式输出: {'启用 ✓' if Config.ENABLE_STREAMING else '禁用 ✗'}")
    print(f"💬 上下文长度: {Config.MAX_CONTEXT_MESSAGES} 轮对话")
    print("=" * 60)

# ============ API 路由 ============

@app.route('/api/test', methods=['GET'])
def test_api():
    """测试 API 连接和系统状态"""
    return jsonify({
        'status': 'success',
        'message': '欢迎来到计算思维助手系统！',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'version': '1.0.0',
        'python_version': '3.12',
        'openai_configured': bool(Config.OPENAI_API_KEY),
        'streaming_enabled': Config.ENABLE_STREAMING
    })

# ⭐⭐⭐ 流式聊天 API ⭐⭐⭐
@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """
    流式聊天 API - Server-Sent Events (SSE)
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': '请求数据不能为空'}), 400
        
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id') or str(uuid.uuid4())
        
        if not user_message:
            return jsonify({'status': 'error', 'message': '消息不能为空'}), 400
        
        if not Config.OPENAI_API_KEY:
            return jsonify({'status': 'error', 'message': '未配置 OpenAI API 密钥'}), 500
        
        # ⭐ 打印请求日志
        print(f"📨 收到流式请求: {user_message[:50]}...")
        
        service = get_llm_service()
        
        def generate():
            """生成器函数：逐块返回数据"""
            try:
                # ⭐ 发送会话ID
                yield f"data: {json.dumps({'type': 'session', 'session_id': session_id}, ensure_ascii=False)}\n\n"
                
                # ⭐ 逐块发送内容
                chunk_count = 0
                for content in service.chat_stream(user_message, session_id):
                    chunk_count += 1
                    chunk_data = json.dumps({
                        'type': 'content',
                        'content': content
                    }, ensure_ascii=False)
                    yield f"data: {chunk_data}\n\n"
                
                # ⭐ 发送完成信号
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
                
                # ⭐ 打印完成日志
                print(f"✅ 流式响应完成: 共 {chunk_count} 个块")
                
            except Exception as e:
                print(f"❌ 流式生成错误: {str(e)}")
                error_data = json.dumps({
                    'type': 'error',
                    'message': str(e)
                }, ensure_ascii=False)
                yield f"data: {error_data}\n\n"
        
        # ⭐ 返回流式响应
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
        
        return jsonify({
            'status': 'error',
            'message': f'处理请求时出错: {str(e)}'
        }), 500

# ⭐ 清除上下文 API
@app.route('/api/chat/clear-context', methods=['POST'])
def clear_context():
    """清除会话上下文"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'status': 'error', 'message': '缺少 session_id'}), 400
        
        service = get_llm_service()
        success = service.clear_history(session_id)
        
        if success:
            print(f"🗑️ 已清除会话上下文: {session_id}")
            return jsonify({
                'status': 'success',
                'message': '上下文已清除'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': '会话不存在'
            }), 404
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'清除上下文失败: {str(e)}'
        }), 500

# ⭐ 获取上下文信息 API
@app.route('/api/chat/context-info/<session_id>', methods=['GET'])
def get_context_info(session_id):
    """获取当前上下文信息"""
    try:
        service = get_llm_service()
        history_length = service.get_history_length(session_id)
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'history_length': history_length,
            'max_context': Config.MAX_CONTEXT_MESSAGES
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ========== 认证相关路由 ==========

@app.route('/api/auth/register', methods=['POST'])
def register():
    """
    用户注册接口
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        nickname = data.get('nickname')
        
        if not username or not password:
            return jsonify({
                'status': 'error',
                'message': '用户名和密码不能为空'
            }), 400
        
        result = AuthService.register(username, password, email, nickname)
        
        if result['success']:
            return jsonify({
                'status': 'success',
                'message': result['message'],
                'user': result['user']
            }), 201
        else:
            return jsonify({
                'status': 'error',
                'message': result['message']
            }), 400
            
    except Exception as e:
        print(f"❌ 注册错误: {e}")
        return jsonify({
            'status': 'error',
            'message': f'注册失败: {str(e)}'
        }), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """
    用户登录接口
    """
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'status': 'error',
                'message': '用户名和密码不能为空'
            }), 400
        
        result = AuthService.login(username, password)
        
        if result['success']:
            return jsonify({
                'status': 'success',
                'message': result['message'],
                'token': result['token'],
                'user': result['user']
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': result['message']
            }), 401
            
    except Exception as e:
        print(f"❌ 登录错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'登录失败: {str(e)}'
        }), 500


@app.route('/api/auth/verify', methods=['POST'])
def verify_token():
    """
    验证 Token 接口
    """
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({
                'status': 'error',
                'message': 'Token 不能为空'
            }), 400
        
        result = AuthService.verify_token(token)
        
        if result['valid']:
            return jsonify({
                'status': 'success',
                'message': result['message'],
                'user_id': result['user_id'],
                'username': result['username']
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': result['message']
            }), 401
            
    except Exception as e:
        print(f"❌ Token 验证错误: {e}")
        return jsonify({
            'status': 'error',
            'message': f'验证失败: {str(e)}'
        }), 500


# ⭐ 示例：需要登录的接口
@app.route('/api/user/profile', methods=['GET'])
@login_required
def get_user_profile():
    """
    获取用户信息（需要登录）
    """
    try:
        from models.user import User
        user = User.query.get(g.user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': '用户不存在'
            }), 404
        
        return jsonify({
            'status': 'success',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        print(f"❌ 获取用户信息错误: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404 错误处理"""
    return jsonify({'status': 'error', 'message': '页面不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    """500 错误处理"""
    return jsonify({'status': 'error', 'message': '服务器内部错误'}), 500

if __name__ == '__main__':
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )