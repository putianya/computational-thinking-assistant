# Flask 应用初始化
# 路由和视图函数
# 请求处理（request. get_json()）
# 错误处理（try-except）
# 模块导入


# app.py
from flask import Flask, render_template, request, jsonify
from config import Config
from datetime import datetime

# 创建 Flask 应用
app = Flask(__name__)
app.config.from_object(Config)

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
        'timestamp': datetime. now().strftime('%Y-%m-%d %H:%M:%S'),
        'version': '1.0.0',
        'python_version': '3.12',
        'openai_configured': bool(Config.OPENAI_API_KEY)
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    聊天 API 路由
    接收用户消息，返回 AI 回复
    
    预期请求格式：
    {
        "message": "用户的问题"
    }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        user_message = data. get('message', '').strip()
        
        # 验证输入
        if not user_message:
            return jsonify({
                'status': 'error',
                'message': '消息不能为空'
            }), 400
        
        # 检查 API 密钥
        if not Config. OPENAI_API_KEY: 
            return jsonify({
                'status': 'error',
                'message': '未配置 OpenAI API 密钥，请在 . env 文件中设置'
            }), 500
        
        # 导入 OpenAI（延迟导入，避免启动时报错）
        from openai import OpenAI
        
        # 初始化 OpenAI 客户端
        client = OpenAI(
            api_key=Config. OPENAI_API_KEY,
            base_url="https://models.inference.ai.azure.com" 
            )
        
        # 调用 GPT 模型
        response = client.chat.completions.create(
            model=Config.OPENAI_MODEL,
            messages=[
                {"role":  "system", "content": Config. SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=Config.OPENAI_TEMPERATURE,
            max_tokens=Config.OPENAI_MAX_TOKENS
        )
        
        # 提取回复内容
        bot_reply = response.choices[0].message.content
        
        # 返回成功响应
        return jsonify({
            'status': 'success',
            'user_message': user_message,
            'bot_reply': bot_reply,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'model': Config.OPENAI_MODEL
        })
        
    except Exception as e:
        # 错误处理
        return jsonify({
            'status': 'error',
            'message':  f'处理请求时出错: {str(e)}'
        }), 500


@app.route('/api/echo', methods=['POST'])
def echo():
    """
    回声 API（用于测试）
    简单返回用户发送的消息
    """
    data = request.get_json()
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({
            'status': 'error',
            'message':  '消息不能为空'
        }), 400
    
    return jsonify({
        'status':  'success',
        'user_message': user_message,
        'bot_reply': f'你说：{user_message}',
        'timestamp': datetime. now().strftime('%Y-%m-%d %H:%M:%S')
    })


# ============ 错误处理 ============

@app.errorhandler(404)
def not_found(error):
    """处理 404 错误"""
    return jsonify({
        'status':  'error',
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