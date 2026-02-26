# -*- coding: utf-8 -*-
"""
知识库路由 Blueprint
包含：documents CRUD, chunks CRUD, upload, stats
"""
import traceback
from datetime import datetime
from pathlib import Path
from flask import Blueprint, request, jsonify, g
from sqlalchemy import func
from config import BASE_DIR
from database import db
from models.knowledge_chunk import KnowledgeChunk
from services.analytics.data_collector import DataCollector
from services.vector_service import get_vector_service
from utils.decorators import login_required, require_permission

knowledge_bp = Blueprint('knowledge', __name__)


@knowledge_bp.route('/api/knowledge/documents', methods=['GET'])
@login_required
def get_knowledge_documents():
    """获取知识库文档列表（包含引用统计）"""
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

            chunks = KnowledgeChunk.query.filter_by(
                source=filename,
                is_active=True
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
                'chunks_count': chunks_count,
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
        traceback.print_exc()

        return jsonify({
            'status': 'error',
            'message': f'获取文档列表失败: {str(e)}'
        }), 500


@knowledge_bp.route('/api/knowledge/documents/<filename>', methods=['GET'])
@login_required
def get_document_chunks(filename):
    """获取指定文档的知识块列表（包含引用统计）"""
    try:
        print(f"\n📡 收到请求: GET /api/knowledge/documents/{filename}")

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
                'retrieved_count': chunk.retrieved_count or 0,
                'last_retrieved_at': chunk.last_retrieved_at.isoformat() if chunk.last_retrieved_at else None,
                'created_at': chunk.created_at.isoformat() if chunk.created_at else None,
            }
            chunks_data.append(chunk_dict)

            print(f"   知识块 {chunk.id}: {chunk.chapter}, 引用 {chunk.retrieved_count} 次")

        # 记录知识点查看行为（仅学生）
        try:
            DataCollector.record_knowledge_view(
                user_id=g.user_id,
                session_id=None,
                knowledge_title=filename,
                duration_seconds=None
            )
        except Exception as e:
            print(f"⚠️ 记录知识查看失败（不影响主流程）: {e}")

        return jsonify({
            'status': 'success',
            'message': f'成功获取 {len(chunks_data)} 个知识块',
            'data': {
                'filename': filename,
                'chunks': chunks_data
            }
        }), 200

    except Exception as e:
        print(f"❌ 获取知识块失败: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'获取知识块失败: {str(e)}'
        }), 500


@knowledge_bp.route('/api/knowledge/upload', methods=['POST'])
@login_required
@require_permission('upload_doc')
def upload_document():
    """上传 Markdown 文档到 /data/knowledge 目录"""
    try:
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

        knowledge_dir = Path(BASE_DIR) / 'data' / 'knowledge'
        knowledge_dir.mkdir(parents=True, exist_ok=True)

        file_path = knowledge_dir / filename

        is_overwrite = file_path.exists()

        file.save(str(file_path))
        print(f"✅ 文件已保存: {file_path}")

        if is_overwrite:
            old_chunks = KnowledgeChunk.query.filter_by(source=filename).all()
            for chunk in old_chunks:
                db.session.delete(chunk)
            db.session.commit()
            print(f"🗑️ 已删除旧知识块: {len(old_chunks)} 个")

        from scripts.import_knowledge import import_single_file

        vector_result = import_single_file(Path(file_path))

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
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'上传失败: {str(e)}'
        }), 500


@knowledge_bp.route('/api/knowledge/documents/<filename>', methods=['DELETE'])
@login_required
@require_permission('delete_knowledge')
def delete_document(filename):
    """删除文档（同时删除文件、向量、数据库记录）"""
    try:
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({
                'status': 'error',
                'message': '无效的文件名'
            }), 400

        knowledge_dir = Path(BASE_DIR) / 'data' / 'knowledge'
        file_path = knowledge_dir / filename

        if not file_path.exists():
            return jsonify({
                'status': 'error',
                'message': '文件不存在'
            }), 404

        vector_service = get_vector_service()

        chunks = KnowledgeChunk.query.filter_by(source=filename).all()
        vector_ids = [chunk.vector_id for chunk in chunks if chunk.vector_id]

        if vector_ids:
            try:
                vector_service.delete_documents(vector_ids)
                print(f"🗑️ 已删除向量: {len(vector_ids)} 个")
            except Exception as ve:
                print(f"⚠️ 删除向量时出错: {ve}")

        deleted_count = KnowledgeChunk.query.filter_by(source=filename).delete()
        db.session.commit()
        print(f"🗑️ 已删除数据库记录: {deleted_count} 条")

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
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'status': 'error',
            'message': f'删除失败: {str(e)}'
        }), 500


@knowledge_bp.route('/api/knowledge/stats', methods=['GET'])
@login_required
@require_permission('view_knowledge_stats')
def get_knowledge_stats():
    """获取知识库统计信息"""
    try:
        print("📊 计算知识库统计...")

        doc_stats = db.session.query(
            KnowledgeChunk.source,
            func.count(KnowledgeChunk.id).label('chunk_count'),
            func.sum(KnowledgeChunk.char_count).label('total_chars'),
            func.sum(KnowledgeChunk.retrieved_count).label('total_retrieved')
        ).filter(
            KnowledgeChunk.is_active == True
        ).group_by(
            KnowledgeChunk.source
        ).all()

        total_chunks = sum(stat.chunk_count for stat in doc_stats)
        total_chars = sum(stat.total_chars or 0 for stat in doc_stats)
        total_retrieved = sum(stat.total_retrieved or 0 for stat in doc_stats)

        total_docs = len(set(stat.source for stat in doc_stats))

        print(f"✅ 统计完成:")
        print(f"   文档数: {total_docs}")
        print(f"   知识块数: {total_chunks}")
        print(f"   总字符数: {total_chars}")
        print(f"   总引用次数: {total_retrieved}")

        vector_service = get_vector_service()
        vector_info = vector_service.get_collection_info()
        vector_count = vector_info.get('count', 0)

        print(f"   向量数据库文档数: {vector_count}")

        if total_chunks != vector_count:
            print(f"⚠️  警告：数据库知识块数 ({total_chunks}) 与向量数据库 ({vector_count}) 不一致！")

        return jsonify({
            'status': 'success',
            'data': {
                'document_count': total_docs,
                'chunk_count': total_chunks,
                'total_chars': total_chars,
                'total_retrieved': total_retrieved,
                'vector_count': vector_count,
                'is_synced': total_chunks == vector_count
            }
        })

    except Exception as e:
        print(f"❌ 获取统计失败: {e}")
        traceback.print_exc()

        return jsonify({
            'status': 'error',
            'message': f'获取统计失败: {str(e)}'
        }), 500


@knowledge_bp.route('/api/knowledge/chunks/<int:chunk_id>', methods=['DELETE'])
@login_required
@require_permission('delete_knowledge')
def delete_knowledge_chunk(chunk_id):
    """
    删除指定知识块

    权限检查：
    - 只有教师和管理员可以删除
    """
    try:
        print(f"\n{'='*60}")
        print(f"🗑️ 删除知识块请求")
        print(f"   操作用户: {g.user.username} ({g.user.get_role_display()})")
        print(f"   知识块ID: {chunk_id}")
        print(f"{'='*60}")

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

        if chunk.vector_id:
            try:
                vector_service = get_vector_service()

                print(f"🔄 删除向量: {chunk.vector_id}")
                vector_service.delete_documents([chunk.vector_id])
                print(f"✅ 向量已删除")

            except Exception as ve:
                print(f"⚠️ 删除向量失败: {ve}")
        else:
            print(f"⚠️ 知识块没有关联的向量ID")

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


@knowledge_bp.route('/api/knowledge/chunks/<int:chunk_id>', methods=['PUT'])
@login_required
@require_permission('edit_knowledge')
def update_knowledge_chunk(chunk_id):
    """
    编辑知识块内容

    权限：需要 teacher 或 admin 角色
    """
    try:
        print(f"\n{'='*60}")
        print(f"✏️ 编辑知识块请求")
        print(f"   操作用户: {g.user.username} ({g.user.get_role_display()})")
        print(f"   知识块ID: {chunk_id}")
        print(f"{'='*60}")

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

        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error',
                'message': '请提供更新数据'
            }), 400

        old_content = chunk.content
        content_changed = False

        if 'content' in data:
            new_content = data['content'].strip()

            if not new_content:
                return jsonify({
                    'status': 'error',
                    'message': '内容不能为空'
                }), 400

            if new_content != old_content:
                chunk.content = new_content
                chunk.calculate_content_features()
                content_changed = True
                print(f"📝 内容已更新: {len(new_content)} 字符")

        if 'chapter' in data:
            chunk.chapter = data['chapter']
            print(f"📖 章节已更新: {chunk.chapter}")

        if 'section' in data:
            chunk.section = data['section']
            print(f"📑 小节已更新: {chunk.section}")

        if 'keywords' in data:
            if isinstance(data['keywords'], list):
                chunk.set_keywords_list(data['keywords'])
                print(f"🏷️ 关键词已更新: {data['keywords']}")
            elif isinstance(data['keywords'], str):
                chunk.keywords = data['keywords']
                print(f"🏷️ 关键词已更新: {data['keywords']}")

        chunk.updated_at = datetime.now()

        if content_changed:
            print(f"\n🔄 内容已改变，开始重新向量化...")

            try:
                vector_service = get_vector_service()

                if chunk.vector_id:
                    print(f"🗑️ 删除旧向量: {chunk.vector_id}")
                    vector_service.delete_documents([chunk.vector_id])

                print(f"🧠 生成新向量...")

                metadata = {
                    'source': chunk.source,
                    'chapter': chunk.chapter,
                    'section': chunk.section,
                }

                new_vector_id = f"chunk_{chunk.id}_{int(datetime.now().timestamp())}"

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

            except Exception as ve:
                print(f"⚠️ 重新向量化失败: {ve}")
                traceback.print_exc()

        try:
            db.session.commit()
            print(f"✅ 数据库更新成功")
        except Exception as db_error:
            print(f"❌ 数据库更新失败: {db_error}")
            db.session.rollback()
            raise

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
