# -*- coding: utf-8 -*-
"""
Flask 应用主程序 - 后端 API 服务
"""
import sys
import io
from flask import Flask, jsonify, request, Response, stream_with_context
from flask_cors import CORS
from config import Config
from datetime import datetime
import uuid

# 设置标准输出为 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 创建 Flask 应用
app = Flask(__name__)
app.config.from_object(Config)

# 启用 CORS（允许前端跨域请求）
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# 全局服务实例
llm_service = None

def get_llm_service():
    """
    获取 LLM 服务实例（懒加载 + 单例模式）
    相当于 Qt 的 getInstance()
    """
    global llm_service
    if llm_service is None:
        from services.llm_service import LLMService
        llm_service = LLMService()
    return llm_service

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
        'streaming_enabled': Config.ENABLE_STREAMING  # ⭐ 新增
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """普通聊天 API（非流式）"""
    try:
        # 1. 获取并验证请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': '请求数据不能为空'}), 400
        
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id')  # ⭐ 新增
        
        if not user_message:
            return jsonify({'status': 'error', 'message': '消息不能为空'}), 400
        
        # 2. 检查配置
        if not Config.OPENAI_API_KEY:
            return jsonify({'status': 'error', 'message': '未配置 OpenAI API 密钥'}), 500
        
        # 3. 调用服务层（业务逻辑）
        service = get_llm_service()
        bot_reply = service.chat(user_message, session_id)
        
        # 4. 返回成功响应
        return jsonify({
            'status': 'success',
            'user_message': user_message,
            'bot_reply': bot_reply,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'model': Config.OPENAI_MODEL,
            'session_id': session_id or str(uuid.uuid4())  # ⭐ 新增
        })
        
    except Exception as e:
        # 其他错误
        print(f"❌ 处理聊天请求时出错: {str(e)}")
        import traceback
        traceback.print_exc()  # 打印完整错误堆栈
        
        return jsonify({
            'status': 'error',
            'message': f'处理请求时出错: {str(e)}'
        }), 500


# ⭐⭐⭐ 新增：流式聊天 API ⭐⭐⭐
@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """
    流式聊天 API - Server-Sent Events (SSE)
    """
    try:
        # 1. 获取并验证请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': '请求数据不能为空'}), 400
        
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id') or str(uuid.uuid4())
        
        if not user_message:
            return jsonify({'status': 'error', 'message': '消息不能为空'}), 400
        
        # 2. 检查配置
        if not Config.OPENAI_API_KEY:
            return jsonify({'status': 'error', 'message': '未配置 OpenAI API 密钥'}), 500
        
        service = get_llm_service()
        
        def generate():
            """生成器函数：逐块返回数据"""
            try:
                # ⭐ 发送会话ID
                yield f"data: {{'type': 'session', 'session_id': '{session_id}'}}\n\n"
                
                # ⭐ 逐块发送内容
                for content in service.chat_stream(user_message, session_id):
                    # SSE 格式：data: {JSON}\n\n
                    import json
                    chunk_data = json.dumps({
                        'type': 'content',
                        'content': content
                    }, ensure_ascii=False)
                    yield f"data: {chunk_data}\n\n"
                
                # ⭐ 发送完成信号
                yield f"data: {{'type': 'done'}}\n\n"
                
            except Exception as e:
                error_data = {
                    'type': 'error',
                    'message': str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
        
        # ⭐ 返回流式响应
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
        
    except Exception as e:
        # 其他错误
        print(f"❌ 处理流式请求时出错: {str(e)}")
        import traceback
        traceback.print_exc()  # 打印完整错误堆栈
        
        return jsonify({
            'status': 'error',
            'message': f'处理请求时出错: {str(e)}'
        }), 500

# ⭐ 新增：清除上下文 API
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

# ⭐ 新增：获取上下文信息 API
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

@app.errorhandler(404)
def not_found(error):
    """404 错误处理"""
    return jsonify({'status': 'error', 'message': '页面不存在'}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 错误处理"""
    return jsonify({'status': 'error', 'message': '服务器内部错误'}), 500


# ============ 应用启动 ============

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 后端 API 服务启动中...")
    print(f"📍 API 地址: http://127.0.0.1:{Config.PORT}")
    print(f"🤖 AI 模型: {Config.OPENAI_MODEL}")
    print(f"🔑 API 密钥: {'已配置 ✓' if Config.OPENAI_API_KEY else '未配置 ✗'}")
    print(f"⚡ 流式输出: {'启用 ✓' if Config.ENABLE_STREAMING else '禁用 ✗'}")
    print(f"💬 上下文长度: {Config.MAX_CONTEXT_MESSAGES} 轮对话")
    print("=" * 60)
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )