# -*- coding: utf-8 -*-
"""
Flask 应用主程序 - 后端 API 服务
"""
import os
import sys
import io
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from database import db, init_db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)

    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
            "methods": ["GET", "POST", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # 注册 Blueprint
    from routes.auth import auth_bp
    from routes.chat import chat_bp
    from routes.knowledge import knowledge_bp
    from routes.code import code_bp
    from routes.analytics import analytics_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(knowledge_bp)
    app.register_blueprint(code_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(admin_bp)

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

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'status': 'error', 'message': '页面不存在'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'status': 'error', 'message': '服务器内部错误'}), 500

    return app


# 设置标准输出为 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = create_app()

# 应用启动信息
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
    print("=" * 60)
    print("🚀 后端 API 服务启动中...")
    print(f"📍 API 地址: http://127.0.0.1:{Config.PORT}")
    print(f"🤖 AI 模型: {Config.OPENAI_MODEL}")
    print(f"🔗 Base URL: {Config.OPENAI_BASE_URL}")
    print(f"🔑 API 密钥: {'已配置 ✓' if Config.OPENAI_API_KEY else '未配置 ✗'}")
    print(f"⚡ 流式输出: {'启用 ✓' if Config.ENABLE_STREAMING else '禁用 ✗'}")
    print(f"💬 上下文管理: 全部消息（无限制）")
    print(f"💾 会话消息限制: {'无限制' if Config.MAX_MESSAGES_PER_SESSION is None else Config.MAX_MESSAGES_PER_SESSION}")
    print("=" * 60)

    # ⬇️ 新增：启动时自动同步知识库目录
    import threading
    def _startup_sync():
        import time
        time.sleep(1)  # 等服务器完全就绪
        with app.app_context():
            try:
                from routes.knowledge import sync_knowledge_directory
                r = sync_knowledge_directory()
                imported = len(r['imported'])
                deleted = len(r['deleted'])
                if imported or deleted:
                    print(f"🔄 启动同步：新增 {imported} 个文档，清理 {deleted} 条孤立记录")
                else:
                    print("🔄 启动同步：知识库已是最新，无变更")
            except Exception as e:
                print(f"⚠️ 启动同步失败（不影响服务运行）: {e}")

    threading.Thread(target=_startup_sync, daemon=True).start()

if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
