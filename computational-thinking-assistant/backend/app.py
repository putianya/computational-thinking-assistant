# -*- coding: utf-8 -*-
"""
Flask 应用主程序 - 后端 API 服务
"""
import os
import sys
import io
import time
import uuid
import traceback
from datetime import datetime
from pathlib import Path
from functools import wraps
import json
from flask import Flask, request, jsonify, Response, g,stream_with_context
from flask_cors import CORS
from werkzeug.utils import secure_filename
from sqlalchemy import or_
from io import BytesIO
# ⭐⭐⭐ 添加缺失的导入 ⭐⭐⭐
from config import Config  # ← 这行必须存在！
from database import db, init_db
from models.user import User
from models.chat_session import ChatSession
from models.chat_message import ChatMessage
from models.knowledge_chunk import KnowledgeChunk
from services.auth_service import AuthService
from services.chat_service import ChatService
from services.analytics.data_collector import DataCollector
from utils.decorators import login_required, require_permission, require_role
# ⭐⭐⭐ 在文件顶部添加导入 ⭐⭐⭐
from services.analytics.stats_calculator import StatsCalculator
from services.analytics.weakness_analyzer import WeaknessAnalyzer
from services.analytics.chart_generator import ChartGenerator
# 设置标准输出为 UTF-8 编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ⭐⭐⭐ 定义 BASE_DIR ⭐⭐⭐
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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
code_service = None  # ⭐ 添加代码服务全局变量

def get_llm_service():
    """懒加载 LLM 服务"""
    global llm_service
    if llm_service is None:
        from services.llm_service import LLMService
        llm_service = LLMService()
    return llm_service

# ⭐ 添加：懒加载代码服务
def get_code_service():
    """懒加载代码分析服务"""
    global code_service
    if code_service is None:
        from services.code_service import CodeService
        from services.vector_service import get_vector_service
        
        llm = get_llm_service()
        vector = get_vector_service()
        code_service = CodeService(llm, vector)
    return code_service

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
        
        if not user_message:
            return jsonify({'status': 'error', 'message': '消息不能为空'}), 400
        
        if not session_id:
            session = ChatService.get_or_create_active_session(g.user_id)
            session_id = session.session_id
        
        # ⭐ 在外部记录开始时间
        request_start_time = time.time()
        print(f"\n{'='*60}")
        print(f"📨 收到流式请求: {user_message[:50]}...")
        print(f"📍 会话: {session_id}")
        print(f"{'='*60}")
        
        service = get_llm_service()
        
        # ⭐⭐⭐ 在处理前记录提问行为（异步，不阻塞） ⭐⭐⭐
        try:
            # 获取知识点（如果使用了知识库）
            knowledge_topics = None
            # 可以从 service 的上下文中提取知识点，暂时设为 None
            
            DataCollector.record_question(
                user_id=g.user_id,
                session_id=session_id,
                question=user_message,
                knowledge_topics=knowledge_topics
            )
        except Exception as e:
            print(f"⚠️ 记录提问行为失败: {e}")
            # 不影响主流程，继续执行
        
        def generate():
            chunk_count = 0
            first_chunk_time = None
            
            try:
                # 发送会话 ID
                yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
                
                # 流式输出内容
                for chunk in service.chat_stream(user_message, session_id):
                    chunk_count += 1
                    
                    # ⭐⭐⭐ 在第一个内容块时记录时间 ⭐⭐⭐
                    if first_chunk_time is None:
                        first_chunk_time = time.time()
                        latency = first_chunk_time - request_start_time
                        print(f"⚡ 首字节延迟（请求→首块）: {latency:.2f}秒")
                    
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                
                # 完成信号
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
                'X-Accel-Buffering': 'no',  # ⭐ 禁用 Nginx 缓冲
                'Connection': 'keep-alive',
                'Content-Type': 'text/event-stream; charset=utf-8',
            }
        )
        
    except Exception as e:
        print(f"❌ 处理请求错误: {e}")
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500

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


@app.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    """
    用户退出登录
    
    说明：
    - 目前采用 JWT 无状态认证，Token 存储在前端
    - 后端无需维护 Token 黑名单（除非需要强制失效）
    - 前端清除 localStorage 即可完成登出
    - 此接口主要用于记录登出日志和数据统计
    
    返回格式：
    {
        "status": "success",
        "message": "退出成功"
    }
    """
    try:
        user_id = g.user_id
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': '用户不存在'
            }), 404
        
        username = user.username
        
        print("\n" + "=" * 60)
        print(f"👋 用户退出登录")
        print(f"   用户ID: {user_id}")
        print(f"   用户名: {username}")
        print(f"   角色: {user.get_role_display()}")
        print("=" * 60 + "\n")
        
        # ⭐ 可选：记录登出时间（如果需要统计在线时长）
        # user.last_logout = datetime.now()
        # db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': '退出成功'
        }), 200
        
    except Exception as e:
        print(f"❌ 退出登录失败: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'status': 'error',
            'message': f'退出失败: {str(e)}'
        }), 500


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



# ========== ⭐⭐⭐ 知识库管理 API（重构版）⭐⭐⭐ ==========

@app.route('/api/knowledge/documents', methods=['GET'])
@login_required
def get_knowledge_documents():
    """
    获取知识库文档列表（包含引用统计）
    """
    try:
        print("📂 获取文档列表...")
        
        knowledge_dir = Path(BASE_DIR) / 'data' / 'knowledge'
        
        if not knowledge_dir.exists():
            return jsonify({
                'status': 'success',
                'data': {'documents': []}
            })
        
        documents = []
        
        for md_file in knowledge_dir.glob('*.md'):
            filename = md_file.name
            
            # ⭐⭐⭐ 修复：准确统计每个文档的知识块数量 ⭐⭐⭐
            chunks = KnowledgeChunk.query.filter_by(
                source=filename,
                is_active=True  # ⭐ 只统计活跃的
            ).all()
            
            chunks_count = len(chunks)
            total_retrieved = sum(chunk.retrieved_count for chunk in chunks)
            
            print(f"   {filename}: {chunks_count} 个知识块, {total_retrieved} 次引用")
            
            documents.append({
                'name': filename,
                'size': md_file.stat().st_size,
                'modified_at': datetime.fromtimestamp(
                    md_file.stat().st_mtime
                ).isoformat(),
                'chunks_count': chunks_count,  # ⭐ 准确的知识块数量
                'total_retrieved': total_retrieved
            })
        
        documents.sort(key=lambda x: x['modified_at'], reverse=True)
        
        print(f"✅ 返回 {len(documents)} 个文档")
        
        return jsonify({
            'status': 'success',
            'data': {'documents': documents}
        })
        
    except Exception as e:
        print(f"❌ 获取文档列表失败: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'status': 'error',
            'message': f'获取文档列表失败: {str(e)}'
        }), 500


@app.route('/api/knowledge/documents/<filename>', methods=['GET'])
@login_required
def get_document_chunks(filename):
    """
    获取指定文档的知识块列表（包含引用统计）
    """
    try:
        print(f"\n📡 收到请求: GET /api/knowledge/documents/{filename}")
        
        # 1. 查询该文档的所有知识块
        chunks = KnowledgeChunk.query.filter_by(
            source=filename,
            is_active=True
        ).order_by(KnowledgeChunk.id.asc()).all()
        
        print(f"📊 查询到 {len(chunks)} 个知识块")
        
        if not chunks:
            return jsonify({
                'status': 'success',
                'message': '该文档暂无知识块',
                'data': {
                    'filename': filename,
                    'chunks': []
                }
            }), 200
        
        # ⭐⭐⭐ 关键修复：确保返回完整的知识块数据 ⭐⭐⭐
        chunks_data = []
        for chunk in chunks:
            chunk_dict = {
                'id': chunk.id,
                'content': chunk.content,
                'chapter': chunk.chapter,
                'section': chunk.section,
                'keywords': chunk.keywords,
                'level': chunk.level,
                'char_count': chunk.char_count,
                'word_count': chunk.word_count,
                'retrieved_count': chunk.retrieved_count or 0,  # ⭐ 默认0
                'last_retrieved_at': chunk.last_retrieved_at.isoformat() if chunk.last_retrieved_at else None,
                'created_at': chunk.created_at.isoformat() if chunk.created_at else None,
            }
            chunks_data.append(chunk_dict)
            
            # 调试：打印每个知识块
            print(f"   知识块 {chunk.id}: {chunk.chapter}, 引用 {chunk.retrieved_count} 次")
        
        # ⭐⭐⭐ 返回格式必须匹配前端期望 ⭐⭐⭐
        return jsonify({
            'status': 'success',
            'message': f'成功获取 {len(chunks_data)} 个知识块',
            'data': {
                'filename': filename,
                'chunks': chunks_data  # ⭐ 确保 chunks 字段存在
            }
        }), 200
        
    except Exception as e:
        print(f"❌ 获取知识块失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取知识块失败: {str(e)}'
        }), 500


@app.route('/api/knowledge/upload', methods=['POST'])
@login_required
@require_permission('upload_doc')
def upload_document():
    """
    上传 Markdown 文档到 /data/knowledge 目录
    """
    try:
        # 1. 检查文件
        if 'file' not in request.files:
            return jsonify({
                'status': 'error',
                'message': '未选择文件'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'status': 'error',
                'message': '未选择文件'
            }), 400
        
        if not file.filename.endswith('.md'):
            return jsonify({
                'status': 'error',
                'message': '只支持 .md 格式的文件'
            }), 400
        
        filename = file.filename
        
        # 3. 保存文件到 /data/knowledge 目录
        knowledge_dir = Path(BASE_DIR) / 'data' / 'knowledge'
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = knowledge_dir / filename
        
        # 检查是否覆盖现有文件
        is_overwrite = file_path.exists()
        
        file.save(str(file_path))
        print(f"✅ 文件已保存: {file_path}")
        
        # 4. 如果是覆盖，先删除旧的知识块
        if is_overwrite:
            old_chunks = KnowledgeChunk.query.filter_by(source=filename).all()
            for chunk in old_chunks:
                db.session.delete(chunk)
            db.session.commit()
            print(f"🗑️ 已删除旧知识块: {len(old_chunks)} 个")
        
        # 5. 调用 import_single_file 导入知识库
        from scripts.import_knowledge import import_single_file
        
        vector_result = import_single_file(Path(file_path))
        
        # 6. 统计导入后的知识块数量
        chunks_count = KnowledgeChunk.query.filter_by(
            source=filename,
            is_active=True
        ).count()
        
        print(f"✅ 文档上传成功: {filename}")
        print(f"   知识块数: {chunks_count}")
        
        return jsonify({
            'status': 'success',
            'message': '覆盖上传成功' if is_overwrite else '上传成功',
            'data': {
                'file_name': filename,
                'chunks_count': chunks_count,
                'is_overwrite': is_overwrite
            }
        })
        
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'上传失败: {str(e)}'
        }), 500


@app.route('/api/knowledge/documents/<filename>', methods=['DELETE'])
@login_required
@require_permission('delete_knowledge')
def delete_document(filename):
    """
    删除文档（同时删除文件、向量、数据库记录）
    """
    try:
        # 1. 安全检查文件名
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({
                'status': 'error',
                'message': '无效的文件名'
            }), 400
        
        knowledge_dir = Path(BASE_DIR) / 'data' / 'knowledge'
        file_path = knowledge_dir / filename
        
        # 2. 检查文件是否存在
        if not file_path.exists():
            return jsonify({
                'status': 'error',
                'message': '文件不存在'
            }), 404
        
        # 3. 删除向量数据库中的数据
        from services.vector_service import get_vector_service
        vector_service = get_vector_service()
        
        # 获取该文档的所有知识块 ID
        chunks = KnowledgeChunk.query.filter_by(source=filename).all()
        vector_ids = [chunk.vector_id for chunk in chunks if chunk.vector_id]
        
        if vector_ids:
            try:
                vector_service.delete_documents(vector_ids)
                print(f"🗑️ 已删除向量: {len(vector_ids)} 个")
            except Exception as ve:
                print(f"⚠️ 删除向量时出错: {ve}")
        
        # 4. 删除数据库记录
        deleted_count = KnowledgeChunk.query.filter_by(source=filename).delete()
        db.session.commit()
        print(f"🗑️ 已删除数据库记录: {deleted_count} 条")
        
        # 5. 删除物理文件
        file_path.unlink()
        print(f"🗑️ 已删除文件: {file_path}")
        
        return jsonify({
            'status': 'success',
            'message': f'文档 {filename} 已删除',
            'data': {
                'filename': filename,
                'chunks_deleted': deleted_count
            }
        })
        
    except Exception as e:
        print(f"❌ 删除文档失败: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'删除失败: {str(e)}'
        }), 500


@app.route('/api/knowledge/stats', methods=['GET'])
@login_required
def get_knowledge_stats():
    """
    获取知识库统计信息
    """
    try:
        print("📊 计算知识库统计...")
        
        # ⭐⭐⭐ 修复：准确计算知识块数量 ⭐⭐⭐
        
        # 1. 按文档分组统计
        from sqlalchemy import func
        
        doc_stats = db.session.query(
            KnowledgeChunk.source,
            func.count(KnowledgeChunk.id).label('chunk_count'),
            func.sum(KnowledgeChunk.char_count).label('total_chars'),
            func.sum(KnowledgeChunk.retrieved_count).label('total_retrieved')
        ).filter(
            KnowledgeChunk.is_active == True  # 只统计活跃的
        ).group_by(
            KnowledgeChunk.source
        ).all()
        
        # 2. 计算总数
        total_chunks = sum(stat.chunk_count for stat in doc_stats)
        total_chars = sum(stat.total_chars or 0 for stat in doc_stats)
        total_retrieved = sum(stat.total_retrieved or 0 for stat in doc_stats)
        
        # 3. 文档数（去重）
        total_docs = len(set(stat.source for stat in doc_stats))
        
        print(f"✅ 统计完成:")
        print(f"   文档数: {total_docs}")
        print(f"   知识块数: {total_chunks}")
        print(f"   总字符数: {total_chars}")
        print(f"   总引用次数: {total_retrieved}")
        
        # 4. 验证向量数据库
        from services.vector_service import get_vector_service
        vector_service = get_vector_service()
        vector_info = vector_service.get_collection_info()
        vector_count = vector_info.get('count', 0)
        
        print(f"   向量数据库文档数: {vector_count}")
        
        # ⭐ 如果不一致，发出警告
        if total_chunks != vector_count:
            print(f"⚠️  警告：数据库知识块数 ({total_chunks}) 与向量数据库 ({vector_count}) 不一致！")
        
        return jsonify({
            'status': 'success',
            'data': {
                'document_count': total_docs,
                'chunk_count': total_chunks,  # ⭐ 准确的知识块数量
                'total_chars': total_chars,
                'total_retrieved': total_retrieved,
                'vector_count': vector_count,  # ⭐ 新增：向量数据库数量
                'is_synced': total_chunks == vector_count  # ⭐ 是否同步
            }
        })
        
    except Exception as e:
        print(f"❌ 获取统计失败: {e}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'status': 'error',
            'message': f'获取统计失败: {str(e)}'
        }), 500

@app.route('/api/knowledge/chunks/<int:chunk_id>', methods=['DELETE'])
@login_required
@require_permission('delete_knowledge')
def delete_knowledge_chunk(chunk_id):
    """
    删除指定知识块
    
    权限检查：
    - 只有教师和管理员可以删除
    
    流程：
    1. 查询知识块
    2. 从 ChromaDB 删除向量
    3. 从数据库删除记录
    4. 返回结果
    
    返回格式：
    {
        "status": "success",
        "message": "知识块删除成功"
    }
    """
    try:
        # ========== 1. 权限检查 ==========
        from models.user import User
        user = User.query.get(g.user_id)
        
        if not user or not user.has_permission('delete_knowledge'):
            print(f"❌ 无权限删除知识块: 用户 {g.user_id}")
            return jsonify({
                'status': 'error',
                'message': '无权限执行此操作，需要教师或管理员权限'
            }), 403
        
        print(f"\n{'='*60}")
        print(f"🗑️ 删除知识块请求")
        print(f"   操作用户: {user.username} ({user.get_role_display()})")
        print(f"   知识块ID: {chunk_id}")
        print(f"{'='*60}")
        
        # ========== 2. 查询知识块 ==========
        chunk = KnowledgeChunk.query.get(chunk_id)
        
        if not chunk:
            print(f"❌ 知识块不存在: {chunk_id}")
            print(f"{'='*60}\n")
            return jsonify({
                'status': 'error',
                'message': '知识块不存在'
            }), 404
        
        print(f"📄 找到知识块:")
        print(f"   来源: {chunk.source}")
        print(f"   章节: {chunk.chapter}")
        print(f"   向量ID: {chunk.vector_id}")
        
        # ========== 3. 从 ChromaDB 删除向量 ==========
        if chunk.vector_id:
            try:
                from services.vector_service import get_vector_service
                vector_service = get_vector_service()
                
                print(f"🔄 删除向量: {chunk.vector_id}")
                vector_service.delete_documents([chunk.vector_id])
                print(f"✅ 向量已删除")
                
            except Exception as ve:
                print(f"⚠️ 删除向量失败: {ve}")
                # 向量删除失败不影响数据库记录删除
        else:
            print(f"⚠️ 知识块没有关联的向量ID")
        
        # ========== 4. 从数据库删除记录 ==========
        db.session.delete(chunk)
        db.session.commit()
        
        print(f"✅ 数据库记录已删除")
        print(f"{'='*60}\n")
        
        return jsonify({
            'status': 'success',
            'message': '知识块删除成功'
        }), 200
        
    except Exception as e:
        print(f"❌ 删除知识块失败: {e}")
        traceback.print_exc()
        print(f"{'='*60}\n")
        
        db.session.rollback()
        
        return jsonify({
            'status': 'error',
            'message': f'删除知识块失败: {str(e)}'
        }), 500

@app.route('/api/knowledge/chunks/<int:chunk_id>', methods=['PUT'])
@login_required
@require_permission('edit_knowledge')
def update_knowledge_chunk(chunk_id):
    """
    编辑知识块内容
    
    权限：需要 teacher 或 admin 角色
    
    流程：
    1. 查询知识块
    2. 更新内容
    3. 重新向量化
    4. 更新 ChromaDB
    5. 保存到数据库
    
    请求格式：
    {
        "content": "新的内容",
        "chapter": "新章节",
        "section": "新小节",
        "keywords": ["关键词1", "关键词2"]
    }
    
    返回格式：
    {
        "status": "success",
        "message": "知识块更新成功",
        "data": {
            "id": 1,
            "content": "...",
            "updated_at": "2026-02-02T10:00:00"
        }
    }
    """
    try:
        # ========== 1. 权限检查 ==========
        from models.user import User
        user = User.query.get(g.user_id)
        
        if not user or not user.has_permission('edit_knowledge'):
            print(f"❌ 无权限编辑知识块: 用户 {g.user_id}")
            return jsonify({
                'status': 'error',
                'message': '无权限执行此操作，需要教师或管理员权限'
            }), 403
        
        print(f"\n{'='*60}")
        print(f"✏️ 编辑知识块请求")
        print(f"   操作用户: {user.username} ({user.get_role_display()})")
        print(f"   知识块ID: {chunk_id}")
        print(f"{'='*60}")
        
        # ========== 2. 查询知识块 ==========
        chunk = KnowledgeChunk.query.get(chunk_id)
        
        if not chunk:
            print(f"❌ 知识块不存在: {chunk_id}")
            print(f"{'='*60}\n")
            return jsonify({
                'status': 'error',
                'message': '知识块不存在'
            }), 404
        
        print(f"📄 原始数据:")
        print(f"   来源: {chunk.source}")
        print(f"   章节: {chunk.chapter}")
        print(f"   向量ID: {chunk.vector_id}")
        print(f"   字符数: {chunk.char_count}")
        
        # ========== 3. 获取更新数据 ==========
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': '请提供更新数据'
            }), 400
        
        # 记录旧内容（用于判断是否需要重新向量化）
        old_content = chunk.content
        content_changed = False
        
        # ========== 4. 更新字段 ==========
        
        # 更新内容
        if 'content' in data:
            new_content = data['content'].strip()
            
            if not new_content:
                return jsonify({
                    'status': 'error',
                    'message': '内容不能为空'
                }), 400
            
            if new_content != old_content:
                chunk.content = new_content
                chunk.calculate_content_features()  # 重新计算内容特征
                content_changed = True
                print(f"📝 内容已更新: {len(new_content)} 字符")
        
        # 更新章节
        if 'chapter' in data:
            chunk.chapter = data['chapter']
            print(f"📖 章节已更新: {chunk.chapter}")
        
        # 更新小节
        if 'section' in data:
            chunk.section = data['section']
            print(f"📑 小节已更新: {chunk.section}")
        
        # 更新关键词
        if 'keywords' in data:
            if isinstance(data['keywords'], list):
                chunk.set_keywords_list(data['keywords'])
                print(f"🏷️ 关键词已更新: {data['keywords']}")
            elif isinstance(data['keywords'], str):
                chunk.keywords = data['keywords']
                print(f"🏷️ 关键词已更新: {data['keywords']}")
        
        # 更新时间戳
        chunk.updated_at = datetime.now()
        
        # ========== 5. 如果内容改变，重新向量化 ==========
        
        if content_changed:
            print(f"\n🔄 内容已改变，开始重新向量化...")
            
            try:
                from services.vector_service import get_vector_service
                vector_service = get_vector_service()
                
                # 如果有旧向量，先删除
                if chunk.vector_id:
                    print(f"🗑️ 删除旧向量: {chunk.vector_id}")
                    vector_service.delete_documents([chunk.vector_id])
                
                # 生成新向量
                print(f"🧠 生成新向量...")
                
                # 构建元数据
                metadata = {
                    'source': chunk.source,
                    'chapter': chunk.chapter,
                    'section': chunk.section,
                }
                
                # 生成新的向量 ID
                new_vector_id = f"chunk_{chunk.id}_{int(datetime.now().timestamp())}"
                
                # 添加到向量数据库
                result = vector_service.add_documents(
                    texts=[chunk.content],
                    metadatas=[metadata],
                    ids=[new_vector_id]
                )
                
                if result['success']:
                    chunk.vector_id = new_vector_id
                    print(f"✅ 向量化成功: {new_vector_id}")
                else:
                    print(f"⚠️ 向量化失败: {result['message']}")
                    # 不阻止保存，但记录警告
                
            except Exception as ve:
                print(f"⚠️ 重新向量化失败: {ve}")
                traceback.print_exc()
                # 不阻止保存，但返回警告
        
        # ========== 6. 保存到数据库 ==========
        
        try:
            db.session.commit()
            print(f"✅ 数据库更新成功")
        except Exception as db_error:
            print(f"❌ 数据库更新失败: {db_error}")
            db.session.rollback()
            raise
        
        # ========== 7. 返回结果 ==========
        
        print(f"✅ 知识块更新完成")
        print(f"{'='*60}\n")
        
        return jsonify({
            'status': 'success',
            'message': '知识块更新成功' + ('（已重新向量化）' if content_changed else ''),
            'data': {
                'id': chunk.id,
                'content': chunk.content,
                'source': chunk.source,
                'chapter': chunk.chapter,
                'section': chunk.section,
                'keywords': chunk.get_keywords_list(),
                'char_count': chunk.char_count,
                'has_code': chunk.has_code,
                'vector_id': chunk.vector_id,
                'updated_at': chunk.updated_at.isoformat() if chunk.updated_at else None
            }
        }), 200
        
    except Exception as e:
        print(f"❌ 更新知识块失败: {e}")
        traceback.print_exc()
        print(f"{'='*60}\n")
        
        db.session.rollback()
        
        return jsonify({
            'status': 'error',
            'message': f'更新知识块失败: {str(e)}'
        }), 500

# ========== ⭐⭐⭐ 用户管理 API（仅管理员）⭐⭐⭐ ==========

@app.route('/api/admin/users', methods=['GET'])
@login_required
@require_role('admin')
def get_all_users():
    """
    获取所有用户列表
    
    权限：仅管理员
    
    返回格式：
    {
        "status": "success",
        "data": {
            "users": [
                {
                    "id": 1,
                    "username": "student1",
                    "nickname": "张三",
                    "role": "student",
                    "role_display": "学生",
                    "email": "student1@example.com",
                    "is_active": true,
                    "created_at": "2026-01-26T10:00:00",
                    "last_login": "2026-02-01T15:30:00"
                }
            ],
            "total": 10
        }
    }
    """
    try:
        from models.user import User
        
        # 查询所有用户（按创建时间降序）
        users = User.query.order_by(User.created_at.desc()).all()
        
        print(f"📋 查询用户列表: 共 {len(users)} 个用户")
        
        return jsonify({
            'status': 'success',
            'data': {
                'users': [user.to_dict() for user in users],
                'total': len(users)
            }
        }), 200
        
    except Exception as e:
        print(f"❌ 获取用户列表失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取用户列表失败: {str(e)}'
        }), 500


@app.route('/api/admin/users/<int:user_id>/role', methods=['PUT'])
@login_required
@require_permission('change_user_role')
def change_user_role(user_id):
    """
    修改用户角色
    
    权限：需要 change_user_role 权限（管理员）
    
    请求格式：
    {
        "role": "teacher"  // student | teacher | admin
    }
    
    返回格式：
    {
        "status": "success",
        "message": "用户 student1 角色已更新为 教师",
        "data": {
            "id": 1,
            "username": "student1",
            "role": "teacher",
            "role_display": "教师"
        }
    }
    """
    try:
        from models.user import User
        
        # 获取请求数据
        data = request.get_json()
        new_role = data.get('role')
        
        if not new_role:
            return jsonify({
                'status': 'error',
                'message': '请提供新角色'
            }), 400
        
        # 验证角色是否合法
        valid_roles = ['student', 'teacher', 'admin']
        if new_role not in valid_roles:
            return jsonify({
                'status': 'error',
                'message': f'无效的角色，可选值: {", ".join(valid_roles)}'
            }), 400
        
        # 不能修改自己的角色
        if user_id == g.user_id:
            return jsonify({
                'status': 'error',
                'message': '不能修改自己的角色'
            }), 400
        
        # 查询目标用户
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': '用户不存在'
            }), 404
        
        # 记录旧角色
        old_role = user.role
        
        # 更新角色
        success = user.set_role(new_role)
        
        if success:
            print(f"✅ 用户 {user.username} 角色已更新: {old_role} -> {new_role}")
            
            return jsonify({
                'status': 'success',
                'message': f'用户 {user.username} 角色已更新为 {user.get_role_display()}',
                'data': user.to_dict()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': '角色更新失败'
            }), 500
            
    except Exception as e:
        print(f"❌ 修改用户角色失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'修改用户角色失败: {str(e)}'
        }), 500


@app.route('/api/admin/users/<int:user_id>/status', methods=['PUT'])
@login_required
@require_permission('manage_users')
def toggle_user_status(user_id):
    """
    启用/禁用用户
    
    权限：需要 manage_users 权限（管理员）
    
    请求格式：
    {
        "is_active": false  // true | false
    }
    
    返回格式：
    {
        "status": "success",
        "message": "用户 student1 已被禁用",
        "data": {
            "id": 1,
            "username": "student1",
            "is_active": false
        }
    }
    """
    try:
        from models.user import User
        
        # 获取请求数据
        data = request.get_json()
        is_active = data.get('is_active')
        
        if is_active is None:
            return jsonify({
                'status': 'error',
                'message': '请提供 is_active 参数'
            }), 400
        
        # 不能禁用自己
        if user_id == g.user_id:
            return jsonify({
                'status': 'error',
                'message': '不能禁用自己的账号'
            }), 400
        
        # 查询目标用户
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': '用户不存在'
            }), 404
        
        # 更新状态
        user.is_active = is_active
        db.session.commit()
        
        action = '启用' if is_active else '禁用'
        print(f"✅ 用户 {user.username} 已被{action}")
        
        return jsonify({
            'status': 'success',
            'message': f'用户 {user.username} 已被{action}',
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        print(f"❌ 切换用户状态失败: {e}")
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'切换用户状态失败: {str(e)}'
        }), 500


@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
@require_permission('delete_user')
def delete_user(user_id):
    """
    删除用户（危险操作）
    
    权限：需要 delete_user 权限（管理员）
    
    返回格式：
    {
        "status": "success",
        "message": "用户 student1 已被删除"
    }
    """
    try:
        from models.user import User
        
        # 不能删除自己
        if user_id == g.user_id:
            return jsonify({
                'status': 'error',
                'message': '不能删除自己的账号'
            }), 400
        
        # 查询目标用户
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': '用户不存在'
            }), 404
        
        username = user.username
        
        # 删除用户（会级联删除相关会话和消息）
        db.session.delete(user)
        db.session.commit()
        
        print(f"✅ 用户 {username} 已被删除")
        
        return jsonify({
            'status': 'success',
            'message': f'用户 {username} 已被删除'
        }), 200
        
    except Exception as e:
        print(f"❌ 删除用户失败: {e}")
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'删除用户失败: {str(e)}'
        }), 500

@app.route('/api/code/analyze', methods=['POST'])
@login_required
def analyze_code():
    """
    代码分析 API
    
    权限：需要登录
    
    请求格式：
    {
        "code": "int main() { ... }",
        "analysis_type": "full"  // 可选：'syntax' | 'logic' | 'full'，默认 'full'
    }
    
    返回格式：
    {
        "status": "success",
        "data": {
            "success": true,
            "analysis_type": "full",
            "code": "...",
            "features": {
                "lines": 10,
                "functions": ["main"],
                "complexity": "low"
            },
            "syntax_check": {
                "valid": true
            },
            "ai_analysis": {
                "problems": [],
                "suggestions": [],
                "summary": "..."
            },
            "score": 85,
            "level": "B",
            "suggestions": [...]
        }
    }
    """
    try:
        print(f"\n{'='*60}")
        print(f"🔍 收到代码分析请求")
        print(f"   用户ID: {g.user_id}")
        
        # 1. 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': '请提供请求数据'
            }), 400
        
        code = data.get('code', '').strip()
        analysis_type = data.get('analysis_type', 'full')
        
        print(f"   分析类型: {analysis_type}")
        print(f"   代码长度: {len(code)} 字符")
        
        # 2. 验证数据
        if not code:
            print(f"❌ 代码为空")
            print(f"{'='*60}\n")
            return jsonify({
                'status': 'error',
                'message': '代码不能为空'
            }), 400
        
        # 验证分析类型
        valid_types = ['syntax', 'logic', 'full']
        if analysis_type not in valid_types:
            print(f"❌ 无效的分析类型: {analysis_type}")
            print(f"{'='*60}\n")
            return jsonify({
                'status': 'error',
                'message': f'无效的分析类型，可选值: {", ".join(valid_types)}'
            }), 400
        
        # 限制代码长度（防止滥用）
        max_code_length = 10000  # 10K 字符
        if len(code) > max_code_length:
            print(f"❌ 代码过长: {len(code)} > {max_code_length}")
            print(f"{'='*60}\n")
            return jsonify({
                'status': 'error',
                'message': f'代码长度不能超过 {max_code_length} 字符'
            }), 400
        
        # 3. 调用 Service
        print(f"🚀 开始分析...")
        service = get_code_service()
        result = service.analyze_code(code, analysis_type)
        
        # 4. 检查分析结果
        if not result.get('success', False):
            error_msg = result.get('error', '分析失败')
            print(f"❌ 分析失败: {error_msg}")
            print(f"{'='*60}\n")
            return jsonify({
                'status': 'error',
                'message': error_msg,
                'data': result
            }), 500
        
        # 5. ⭐⭐⭐ 记录代码提交行为 ⭐⭐⭐
        try:
            # 提取知识点（从代码特征中）
            knowledge_topics = None
            if result.get('features', {}).get('functions'):
                functions = result['features']['functions']
                knowledge_topics = functions[:5] if functions else None
            
            DataCollector.record_code_submission(
                user_id=g.user_id,
                session_id=None,  # 代码分析通常不在会话中
                code=code,
                result=result,
                knowledge_topics=knowledge_topics
            )
        except Exception as e:
            print(f"⚠️ 记录代码提交失败: {e}")
            # 不影响主流程，继续返回结果
        
        # 6. 返回结果
        print(f"✅ 分析完成")
        print(f"   评分: {result.get('score', 0)}")
        print(f"   等级: {result.get('level', 'N/A')}")
        print(f"   问题数: {len(result.get('ai_analysis', {}).get('problems', []))}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'status': 'success',
            'message': '代码分析完成',
            'data': result
        }), 200
        
    except Exception as e:
        print(f"❌ 代码分析异常: {e}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        
        return jsonify({
            'status': 'error',
            'message': f'代码分析失败: {str(e)}'
        }), 500
    
@app.route('/api/code/chat', methods=['POST'])
@login_required
def code_chat_stream():
    """
    代码分析对话（流式，不使用 RAG）
    
    请求体示例：
    {
        "message": "这段代码有什么问题？",
        "code": "#include <stdio.h>\nint main() {...}",
        "features": {
            "lines": 10,
            "functions": ["main"],
            "complexity": "low",
            "includes": ["stdio.h"]
        },
        "analysis": {  // 可选
            "problems": [...],
            "suggestions": [...],
            "summary": "..."
        }
    }
    
    返回：SSE 流式响应
    data: {"type": "content", "content": "这段代码"}
    data: {"type": "content", "content": "存在以下问题："}
    data: {"type": "done"}
    """
    try:
        # ========== 1. 获取并验证数据 ==========
        data = request.get_json()
        
        message = data.get('message', '').strip()
        code = data.get('code', '').strip()
        features = data.get('features', {})
        analysis = data.get('analysis')  # 可选
        
        # 验证必需字段
        if not message:
            return jsonify({
                'status': 'error',
                'message': '缺少问题内容'
            }), 400
        
        if not code:
            return jsonify({
                'status': 'error',
                'message': '缺少代码内容'
            }), 400
        
        print(f"\n{'='*60}")
        print(f"💬 代码对话请求")
        print(f"{'='*60}")
        print(f"用户ID: {g.user_id}")
        print(f"问题: {message[:50]}...")
        print(f"代码长度: {len(code)} 字符")
        print(f"特征: {features.get('lines', 0)} 行, 复杂度 {features.get('complexity', 'unknown')}")
        
        # ========== 2. 构建提示词 ==========
        messages = _build_code_chat_prompt(code, features, analysis, message)
        
        print(f"构建消息: {len(messages)} 条")
        
        # ========== 3. 流式生成响应 ==========
        def generate():
            """SSE 生成器"""
            full_response = ""
            
            try:
                # 获取 LLM 服务
                llm_service = get_llm_service()
                
                print(f"🤖 开始调用 LLM...")
                
                # 调用 OpenAI API（流式）
                stream = llm_service.client.chat.completions.create(
                    model=llm_service.model,
                    messages=messages,
                    temperature=0.3,  # ⭐ 代码分析需要准确，降低随机性
                    max_tokens=1000,
                    stream=True,
                    timeout=30.0
                )
                
                # 流式发送
                for chunk in stream:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        
                        if hasattr(delta, 'content') and delta.content:
                            content = delta.content
                            full_response += content
                            
                            # 发送内容块
                            yield f"data: {json.dumps({'type': 'content', 'content': content}, ensure_ascii=False)}\n\n"
                
                # 发送完成信号
                print(f"✅ 代码对话完成，共生成 {len(full_response)} 字符")
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
                
            except Exception as e:
                print(f"❌ LLM 调用失败: {e}")
                traceback.print_exc()
                
                # 发送错误信号
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        
        # ========== 4. 返回 SSE 响应 ==========
        return Response(
            stream_with_context(generate()),
            content_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )
        
    except Exception as e:
        print(f"❌ 代码对话 API 错误: {e}")
        traceback.print_exc()
        
        return jsonify({
            'status': 'error',
            'message': f'服务器错误: {str(e)}'
        }), 500


def _build_code_chat_prompt(code, features, analysis, user_message):
    """
    构建代码对话的提示词
    
    Args:
        code: 代码字符串
        features: 代码特征字典
        analysis: AI 分析结果（可选）
        user_message: 用户问题
    
    Returns:
        消息列表 [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
    """
    # ========== 系统提示词 ==========
    system_prompt = f"""你是一位专业的 C 语言代码分析专家，正在帮助学生理解以下代码。

【待分析代码】
```c
{code}
```

【代码基本信息】
- 行数: {features.get('lines', 0)}
- 字符数: {features.get('chars', 0)}
- 是否包含 main 函数: {'是' if features.get('has_main') else '否'}
"""
    
    # 添加头文件信息
    if features.get('includes'):
        system_prompt += f"- 包含头文件: {', '.join(features['includes'])}\n"
    
    # 添加函数信息
    if features.get('functions'):
        system_prompt += f"- 定义的函数: {', '.join(features['functions'])}\n"
    
    # 添加复杂度信息
    complexity_text = {
        'low': '低（简单逻辑）',
        'medium': '中等（有一定控制结构）',
        'high': '高（复杂逻辑）'
    }.get(features.get('complexity'), '未知')
    
    system_prompt += f"- 代码复杂度: {complexity_text}\n"
    
    # ========== 如果有 AI 分析结果，加入上下文 ==========
    if analysis:
        system_prompt += f"""
【AI 分析结果】
- 问题数: {len(analysis.get('problems', []))}
- 建议数: {len(analysis.get('suggestions', []))}
"""
        
        # 添加问题列表
        if analysis.get('problems'):
            system_prompt += "\n问题列表:\n"
            for i, problem in enumerate(analysis['problems'][:3], 1):
                severity = problem.get('severity', 'warning')
                desc = problem.get('description', '')
                system_prompt += f"{i}. [{severity}] {desc}\n"
        
        # 添加总结
        if analysis.get('summary'):
            system_prompt += f"\n总体评价: {analysis['summary']}\n"
    
    # ========== 回答原则 ==========
    system_prompt += """
【回答原则】
1. 针对具体代码行号给出建议（如果需要）
2. 解释概念时结合代码示例
3. 鼓励学生思考，不要直接给完整答案
4. 使用中文回答
5. 如果代码有错误，优先指出错误位置和原因
6. 回答简洁明了，重点突出

请根据以上信息，回答学生的问题。
"""
    
    # ========== 构建消息列表 ==========
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_message
        }
    ]
    
    return messages
# ========== ⭐⭐⭐ 学习分析 API（权限修复版）⭐⭐⭐ ==========

@app.route('/api/analytics/heartbeat', methods=['POST'])
@login_required
def analytics_heartbeat():
    """
    ⭐⭐⭐ 新增：学习心跳接口 ⭐⭐⭐
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


@app.route('/api/analytics/overview', methods=['GET'])
@login_required
def analytics_overview():
    """
    学习概览
    ⭐ 教师/管理员：可查看指定学生或所有学生汇总
    ⭐ 学生自己：不可访问（前端已隐藏入口）
    """
    try:
        user = User.query.get(g.user_id)
        if not user:
            return jsonify({'status': 'error', 'message': '用户不存在'}), 404
        
        days = request.args.get('days', 30, type=int)
        target_user_id = request.args.get('user_id', type=int)
        
        # ⭐ 学生不允许访问分析接口
        if user.role == 'student':
            return jsonify({'status': 'error', 'message': '无权限查看学习分析'}), 403
        
        # 教师/管理员查看
        if target_user_id:
            # 查看指定学生
            target_user = User.query.get(target_user_id)
            if not target_user or target_user.role != 'student':
                return jsonify({'status': 'error', 'message': '目标用户不是学生'}), 400
            
            data = StatsCalculator.get_user_overview(target_user_id, days)
        else:
            # 查看所有学生汇总
            data = StatsCalculator.get_all_students_overview(days)
        
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        print(f"❌ 获取学习概览失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/analytics/trend', methods=['GET'])
@login_required
def analytics_trend():
    """学习趋势（教师/管理员查看指定学生）"""
    try:
        user = User.query.get(g.user_id)
        if user.role == 'student':
            return jsonify({'status': 'error', 'message': '无权限'}), 403
        
        days = request.args.get('days', 30, type=int)
        target_user_id = request.args.get('user_id', type=int)
        
        if not target_user_id:
            return jsonify({'status': 'success', 'data': []})
        
        data = StatsCalculator.get_learning_trend(target_user_id, days)
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/analytics/knowledge-mastery', methods=['GET'])
@login_required
def analytics_knowledge_mastery():
    """知识点掌握度（教师/管理员查看指定学生）"""
    try:
        user = User.query.get(g.user_id)
        if user.role == 'student':
            return jsonify({'status': 'error', 'message': '无权限'}), 403
        
        days = request.args.get('days', 30, type=int)
        target_user_id = request.args.get('user_id', type=int)
        
        if not target_user_id:
            return jsonify({'status': 'success', 'data': []})
        
        data = StatsCalculator.get_knowledge_mastery(target_user_id, days)
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/analytics/weakness', methods=['GET'])
@login_required
def analytics_weakness():
    """薄弱环节分析（教师/管理员查看指定学生）"""
    try:
        user = User.query.get(g.user_id)
        if user.role == 'student':
            return jsonify({'status': 'error', 'message': '无权限'}), 403
        
        days = request.args.get('days', 30, type=int)
        target_user_id = request.args.get('user_id', type=int)
        
        if not target_user_id:
            return jsonify({'status': 'success', 'data': {}})
        
        data = WeaknessAnalyzer.analyze_weaknesses(target_user_id, days)
        return jsonify({'status': 'success', 'data': data})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/analytics/students', methods=['GET'])
@login_required
def analytics_students():
    """
    ⭐⭐⭐ 新增：获取学生列表（供教师/管理员选择查看）⭐⭐⭐
    """
    try:
        user = User.query.get(g.user_id)
        if user.role == 'student':
            return jsonify({'status': 'error', 'message': '无权限'}), 403
        
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

# 在学习分析 API 部分添加以下路由

@app.route('/api/analytics/report', methods=['GET'])
@login_required
def get_learning_report():
    """生成学情报告"""
    try:
        from services.analytics.report_generator import ReportGenerator

        days = request.args.get('days', 30, type=int)
        user_id = request.args.get('user_id', type=int)

        # 权限控制
        current_user = User.query.get(g.user_id)
        if user_id and user_id != g.user_id:
            # 非本人查看需要教师/管理员权限
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

@app.route('/api/analytics/report/pdf', methods=['GET'])
@login_required
def download_report_pdf():
    """下载 PDF 学情报告"""
    try:
        from services.analytics.report_generator import ReportGenerator
        from services.analytics.pdf_generator import PDFReportGenerator

        days = request.args.get('days', 30, type=int)
        user_id_param = request.args.get('user_id', type=int)

        # 权限控制
        current_user = User.query.get(g.user_id)
        if user_id_param and current_user.role in ['teacher', 'admin']:
            target_user_id = user_id_param
        else:
            target_user_id = g.user_id

        # 生成报告数据
        report_data = ReportGenerator.generate_json_report(target_user_id, days)

        if not report_data:
            return jsonify({'status': 'error', 'message': '报告数据生成失败'}), 500

        # 生成 PDF
        pdf_gen = PDFReportGenerator()
        pdf_bytes = pdf_gen.generate(report_data)

        # 构造文件名
        user = User.query.get(target_user_id)
        username = (user.nickname or user.username) if user else "student"
        filename = f"学情报告_{username}_{datetime.now().strftime('%Y%m%d')}.pdf"

        # 返回 PDF 下载
        from flask import send_file
        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"❌ PDF 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': f'PDF 生成失败: {str(e)}'}), 500



@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': '页面不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'status': 'error', 'message': '服务器内部错误'}), 500

if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)