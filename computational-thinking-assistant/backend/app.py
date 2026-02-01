# -*- coding: utf-8 -*-
"""
Flask 应用主程序 - 后端 API 服务
"""
import os
import sys
import io
import json
import time
import traceback
from pathlib import Path
from werkzeug.utils import secure_filename  # ⭐ 新增：安全文件名处理

from flask import Flask, jsonify, request, Response, stream_with_context, g
from flask_cors import CORS
from datetime import datetime

from config import Config
from database import db, init_db
from services.auth_service import AuthService
from services.chat_service import ChatService
from utils.decorators import login_required, require_permission, require_role
from models.knowledge_chunk import KnowledgeChunk
from sqlalchemy import or_, and_

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



# ========== ⭐⭐⭐ 知识库管理 API ⭐⭐⭐ ==========

@app.route('/api/knowledge/chunks', methods=['GET'])
@login_required
def get_knowledge_chunks():
    """
    获取知识库列表（分页、过滤）
    
    查询参数：
    - page: 页码（默认 1）
    - per_page: 每页数量（默认 20）
    - source: 按来源过滤（可选）
    - chapter: 按章节过滤（可选）
    - search: 搜索关键词（可选）
    
    返回格式：
    {
        "status": "success",
        "data": {
            "chunks": [
                {
                    "id": 1,
                    "content": "指针是...",
                    "source": "test_pointer.md",
                    "chapter": "什么是指针",
                    "char_count": 120,
                    "retrieved_count": 5,
                    "created_at": "2026-01-26T10:00:00"
                }
            ],
            "pagination": {
                "page": 1,
                "per_page": 20,
                "total": 13,
                "pages": 1
            }
        }
    }
    """
    try:
        # 1. 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        source = request.args.get('source', None, type=str)
        chapter = request.args.get('chapter', None, type=str)
        search = request.args.get('search', None, type=str)
        
        # ⭐ 限制每页数量（防止恶意请求）
        per_page = min(per_page, 100)
        
        print(f"\n{'='*60}")
        print(f"📚 获取知识库列表")
        print(f"   页码: {page}")
        print(f"   每页: {per_page}")
        print(f"   来源: {source or '全部'}")
        print(f"   章节: {chapter or '全部'}")
        print(f"   搜索: {search or '无'}")
        
        # 2. 构建查询条件
        query = KnowledgeChunk.query.filter_by(is_active=True)
        
        # 按来源过滤
        if source:
            query = query.filter(KnowledgeChunk.source.like(f'%{source}%'))
        
        # 按章节过滤
        if chapter:
            query = query.filter(KnowledgeChunk.chapter.like(f'%{chapter}%'))
        
        # 搜索（在内容、章节、关键词中搜索）
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                or_(
                    KnowledgeChunk.content.like(search_pattern),
                    KnowledgeChunk.chapter.like(search_pattern),
                    KnowledgeChunk.keywords.like(search_pattern)
                )
            )
        
        # 3. 分页查询
        pagination = query.order_by(
            KnowledgeChunk.created_at.desc()  # 按创建时间降序
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False  # 页码超出时不报错
        )
        
        # 4. 构建返回数据（按照指定格式）
        chunks = []
        for chunk in pagination.items:
            chunks.append({
                'id': chunk.id,
                'content': chunk.content,
                'source': chunk.source,
                'chapter': chunk.chapter,
                'char_count': chunk.char_count,
                'retrieved_count': chunk.retrieved_count,
                'created_at': chunk.created_at.strftime('%Y-%m-%dT%H:%M:%S') if chunk.created_at else None
            })
        
        print(f"✅ 返回 {len(chunks)} 个知识块")
        print(f"   总数: {pagination.total}")
        print(f"   总页数: {pagination.pages}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'status': 'success',
            'data': {
                'chunks': chunks,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages
                }
            }
        }), 200
        
    except Exception as e:
        print(f"❌ 获取知识库列表失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取知识库列表失败: {str(e)}'
        }), 500



@app.route('/api/knowledge/upload', methods=['POST'])
@login_required
@require_permission('upload_doc')
def upload_document():
    """
    上传 Markdown 文档
    
    权限：需要 teacher 或 admin 角色
    
    请求格式：
    - Content-Type: multipart/form-data
    - file: Markdown 文件（.md）
    
    返回格式：
    {
        "status": "success",
        "message": "文件上传成功",
        "data": {
            "file_name": "test.md",
            "chunks_count": 15,
            "vector_count": 15,
            "db_count": 15
        }
    }
    """
    try:
        # ⭐⭐⭐ 1. 权限检查 ⭐⭐⭐
        from models.user import User
        user = User.query.get(g.user_id)
        
        if not user or not user.has_permission('upload_doc'):
            print(f"❌ 无权限上传文档: 用户 {g.user_id}")
            return jsonify({
                'status': 'error',
                'message': '无权限执行此操作，需要教师或管理员权限'
            }), 403
        
        print(f"\n{'='*60}")
        print(f"📤 文档上传请求")
        print(f"   操作用户: {user.username} ({user.get_role_display()})")
        print(f"{'='*60}")
        
        # ⭐⭐⭐ 2. 检查是否有文件 ⭐⭐⭐
        if 'file' not in request.files:
            print(f"❌ 请求中没有文件")
            return jsonify({
                'status': 'error',
                'message': '请选择要上传的文件'
            }), 400
        
        file = request.files['file']
        
        # 检查文件名是否为空
        if file.filename == '':
            print(f"❌ 文件名为空")
            return jsonify({
                'status': 'error',
                'message': '未选择文件'
            }), 400
        
        print(f"📁 收到文件: {file.filename}")
        
        # ⭐⭐⭐ 3. 验证文件格式（只接受 .md）⭐⭐⭐
        if not file.filename.lower().endswith('.md'):
            print(f"❌ 文件格式错误: {file.filename}")
            return jsonify({
                'status': 'error',
                'message': '只支持 Markdown 文件（.md）'
            }), 400
        
        # ⭐⭐⭐ 4. 生成安全的文件名 ⭐⭐⭐
        # secure_filename 会移除特殊字符，防止路径遍历攻击
        safe_filename = secure_filename(file.filename)
        
        # 如果文件名被完全过滤掉，使用时间戳
        if not safe_filename:
            import time
            safe_filename = f"upload_{int(time.time())}.md"
        
        print(f"📝 安全文件名: {safe_filename}")
        
        # ⭐⭐⭐ 5. 保存文件到 data/knowledge/ ⭐⭐⭐
        # 获取知识库目录路径
        knowledge_dir = Path(__file__).resolve().parent / 'data' / 'knowledge'
        knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = knowledge_dir / safe_filename
        
        # 检查文件是否已存在
        if file_path.exists():
            print(f"⚠️  文件已存在，将覆盖: {safe_filename}")
            # 可选：添加版本号而不是覆盖
            # base_name = file_path.stem
            # suffix = file_path.suffix
            # counter = 1
            # while file_path.exists():
            #     safe_filename = f"{base_name}_{counter}{suffix}"
            #     file_path = knowledge_dir / safe_filename
            #     counter += 1
        
        # 保存文件
        file.save(str(file_path))
        print(f"✅ 文件已保存: {file_path}")
        
        # ⭐⭐⭐ 6. 立即导入到知识库（分块 + 向量化）⭐⭐⭐
        print(f"🔄 开始导入知识库...")
        
        # 导入导入函数
        sys.path.insert(0, str(Path(__file__).resolve().parent / 'scripts'))
        from scripts.import_knowledge import import_single_file
        
        # 调用导入函数
        import_result = import_single_file(file_path)
        
        if not import_result['success']:
            # 导入失败，删除已保存的文件
            print(f"❌ 导入失败，删除文件: {file_path}")
            if file_path.exists():
                file_path.unlink()
            
            return jsonify({
                'status': 'error',
                'message': f"文件上传成功，但导入失败: {import_result['message']}"
            }), 500
        
        # ⭐⭐⭐ 7. 返回成功结果 ⭐⭐⭐
        print(f"✅ 文档上传并导入成功")
        print(f"{'='*60}\n")
        
        return jsonify({
            'status': 'success',
            'message': '文件上传并导入成功',
            'data': {
                'file_name': safe_filename,
                'chunks_count': import_result['chunks_count'],
                'vector_count': import_result.get('vector_count', 0),
                'db_count': import_result.get('db_count', 0)
            }
        }), 200
        
    except Exception as e:
        print(f"❌ 文档上传失败: {e}")
        traceback.print_exc()
        print(f"{'='*60}\n")
        
        return jsonify({
            'status': 'error',
            'message': f'文档上传失败: {str(e)}'
        }), 500

# ...existing code...

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

# ...existing code...

@app.route('/api/knowledge/stats', methods=['GET'])
@login_required
@require_permission('view_knowledge_stats')
def get_knowledge_stats():
    """
    获取知识库统计信息
    
    返回：
    - 总知识块数
    - 向量总数
    - 热门知识块（检索次数最多）
    - 按来源分布
    - 按章节分布
    
    返回格式：
    {
        "status": "success",
        "data": {
            "total_chunks": 45,
            "total_vectors": 45,
            "sources": [
                {"name": "test_pointer.md", "count": 12},
                {"name": "test_linkedlist.md", "count": 15}
            ],
            "chapters": [
                {"name": "什么是指针", "count": 5},
                {"name": "指针的应用", "count": 7}
            ],
            "hot_chunks": [
                {
                    "id": 3,
                    "chapter": "指针的声明",
                    "retrieved_count": 25,
                    "source": "test_pointer.md"
                }
            ]
        }
    }
    """
    try:
        from models.user import User
        user = User.query.get(g.user_id)
        
        # ⭐ 权限检查：只有教师和管理员可以查看统计
        if not user or not user.has_permission('view_knowledge_stats'):
            print(f"❌ 无权限查看统计: 用户 {g.user_id}")
            return jsonify({
                'status': 'error',
                'message': '无权限查看知识库统计'
            }), 403
        
        print(f"\n{'='*60}")
        print(f"📊 获取知识库统计")
        print(f"   操作用户: {user.username} ({user.get_role_display()})")
        print(f"{'='*60}")
        
        # ========== 1. 数据库统计 ==========
        
        # 总知识块数
        total_chunks = KnowledgeChunk.query.filter_by(is_active=True).count()
        print(f"📦 总知识块数: {total_chunks}")
        
        # 按来源统计
        source_stats = db.session.query(
            KnowledgeChunk.source,
            db.func.count(KnowledgeChunk.id).label('count')
        ).filter_by(is_active=True)\
         .group_by(KnowledgeChunk.source)\
         .order_by(db.text('count DESC'))\
         .all()
        
        sources = [
            {'name': source, 'count': count}
            for source, count in source_stats
        ]
        print(f"📚 来源数: {len(sources)}")
        
        # 按章节统计
        chapter_stats = db.session.query(
            KnowledgeChunk.chapter,
            db.func.count(KnowledgeChunk.id).label('count')
        ).filter_by(is_active=True)\
         .group_by(KnowledgeChunk.chapter)\
         .order_by(db.text('count DESC'))\
         .limit(10)\
         .all()
        
        chapters = [
            {'name': chapter or '未分类', 'count': count}
            for chapter, count in chapter_stats
        ]
        print(f"📖 章节数: {len(chapters)}")
        
        # 热门知识块（检索次数最多的前 10 个）
        hot_chunks = KnowledgeChunk.query\
            .filter_by(is_active=True)\
            .filter(KnowledgeChunk.retrieved_count > 0)\
            .order_by(KnowledgeChunk.retrieved_count.desc())\
            .limit(10)\
            .all()
        
        hot_chunks_data = [
            {
                'id': chunk.id,
                'source': chunk.source,
                'chapter': chunk.chapter,
                'section': chunk.section,
                'retrieved_count': chunk.retrieved_count,
                'content_preview': chunk.content[:80] + '...' if len(chunk.content) > 80 else chunk.content
            }
            for chunk in hot_chunks
        ]
        print(f"🔥 热门知识块: {len(hot_chunks_data)}")
        
        # ========== 2. 向量数据库统计 ==========
        
        try:
            from services.vector_service import get_vector_service
            vector_service = get_vector_service()
            
            vector_info = vector_service.get_collection_info()
            total_vectors = vector_info.get('count', 0)
            print(f"🧠 向量总数: {total_vectors}")
            
        except Exception as ve:
            print(f"⚠️ 获取向量统计失败: {ve}")
            total_vectors = 0
        
        # ========== 3. 内容质量统计 ==========
        
        # 平均字符数
        avg_char_count = db.session.query(
            db.func.avg(KnowledgeChunk.char_count)
        ).filter_by(is_active=True).scalar() or 0
        
        # 包含代码的知识块数
        code_chunk_count = KnowledgeChunk.query.filter_by(
            is_active=True,
            has_code=True
        ).count()
        
        print(f"📏 平均字符数: {avg_char_count:.0f}")
        print(f"💻 包含代码: {code_chunk_count} 个")
        
        # ========== 4. 构建返回数据 ==========
        
        print(f"✅ 统计信息获取成功")
        print(f"{'='*60}\n")
        
        return jsonify({
            'status': 'success',
            'data': {
                # 总体统计
                'total_chunks': total_chunks,
                'total_vectors': total_vectors,
                'avg_char_count': round(avg_char_count, 0),
                'code_chunk_count': code_chunk_count,
                
                # 分布统计
                'sources': sources,
                'chapters': chapters,
                
                # 热门内容
                'hot_chunks': hot_chunks_data,
                
                # 元信息
                'last_updated': datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        print(f"❌ 获取统计信息失败: {e}")
        traceback.print_exc()
        print(f"{'='*60}\n")
        return jsonify({
            'status': 'error',
            'message': f'获取统计信息失败: {str(e)}'
        }), 500

# ...existing code...

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

# ...existing code...

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

# ...existing code...

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': '页面不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'status': 'error', 'message': '服务器内部错误'}), 500

if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)