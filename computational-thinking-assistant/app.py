# -*- coding: utf-8 -*-
"""
Flask 应用主程序
职责: 路由定义、请求处理、响应返回
相当于 Qt 的 HTTP 服务器
"""
import sys
import io
from flask import Flask, render_template, request, jsonify
from config import Config
from datetime import datetime

# 设置标准输出为 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 创建 Flask 应用
app = Flask(__name__)
app.config.from_object(Config)

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

# ============ 路由定义 ============

@app.route('/')
def home():
    """
    主页路由
    渲染 index.html 模板
    """
    return render_template('index.html')


@app.route('/api/test', methods=['GET'])
def test_api():
    """
    测试 API 路由
    返回系统状态信息
    """
    return jsonify({
        'status': 'success',
        'message': '欢迎来到计算思维助手系统！',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'version': '1.0.0',
        'python_version': '3.12',
        'openai_configured': bool(Config.OPENAI_API_KEY)
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    聊天 API 路由
    职责: 接收请求 → 调用服务层 → 返回响应
    
    预期请求格式:
    {
        "message": "用户的问题"
    }
    """
    try:
        # 1. 获取并验证请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': '请求数据不能为空'
            }), 400
        
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'status': 'error',
                'message': '消息不能为空'
            }), 400
        
        # 2. 检查配置
        if not Config.OPENAI_API_KEY:
            return jsonify({
                'status': 'error',
                'message': '未配置 OpenAI API 密钥，请在 .env 文件中设置 OPENAI_API_KEY'
            }), 500
        
        # 3. 调用服务层（业务逻辑）
        service = get_llm_service()
        bot_reply = service.chat(user_message)
        
        # 4. 返回成功响应
        return jsonify({
            'status': 'success',
            'user_message': user_message,
            'bot_reply': bot_reply,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'model': Config.OPENAI_MODEL
        })
        
    except ValueError as e:
        # 验证错误
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        # 其他错误
        print(f"❌ 处理聊天请求时出错: {str(e)}")
        import traceback
        traceback.print_exc()  # 打印完整错误堆栈
        
        return jsonify({
            'status': 'error',
            'message': f'处理请求时出错: {str(e)}'
        }), 500


@app.route('/api/echo', methods=['POST'])
def echo():
    """
    回声 API（用于测试）
    简单返回用户发送的消息
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': '请求数据不能为空'
            }), 400
        
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({
                'status': 'error',
                'message': '消息不能为空'
            }), 400
        
        return jsonify({
            'status': 'success',
            'user_message': user_message,
            'bot_reply': f'你说：{user_message}',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'处理请求时出错: {str(e)}'
        }), 500


# ============ 错误处理 ============

@app.errorhandler(404)
def not_found(error):
    """处理 404 错误"""
    return jsonify({
        'status': 'error',
        'message': '页面不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """处理 500 错误"""
    return jsonify({
        'status': 'error',
        'message': '服务器内部错误'
    }), 500


# ============ 应用启动 ============

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 计算思维课程助手系统启动中...")
    print(f"📍 访问地址: http://127.0.0.1:{Config.PORT}")
    print(f"🤖 AI 模型: {Config.OPENAI_MODEL}")
    print(f"🔑 API 密钥: {'已配置 ✓' if Config.OPENAI_API_KEY else '未配置 ✗'}")
    print("=" * 60)
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )