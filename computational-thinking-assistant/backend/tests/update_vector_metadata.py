# -*- coding: utf-8 -*-
"""
同步知识块 ID 到向量数据库

修复问题：向量数据库的 metadata 中缺少 chunk_id，导致引用统计无法更新
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from database import db
from models.knowledge_chunk import KnowledgeChunk
from services.vector_service import get_vector_service


def sync_chunk_ids():
    """同步 chunk_id 到向量数据库"""
    print("\n" + "=" * 60)
    print("🔧 同步知识块 ID 到向量数据库")
    print("=" * 60)
    
    with app.app_context():
        # 1. 获取所有知识块
        chunks = KnowledgeChunk.query.filter_by(is_active=True).all()
        print(f"\n📊 数据库中共有 {len(chunks)} 个活跃知识块")
        
        if not chunks:
            print("⚠️ 没有需要同步的知识块")
            return
        
        # 2. 获取向量服务
        vector_service = get_vector_service()
        
        # 3. 逐个更新
        updated_count = 0
        not_found_count = 0
        error_count = 0
        
        for chunk in chunks:
            if not chunk.vector_id:
                print(f"⚠️ 知识块 {chunk.id} 没有 vector_id，跳过")
                not_found_count += 1
                continue
            
            try:
                # 获取当前向量数据
                result = vector_service.collection.get(
                    ids=[chunk.vector_id],
                    include=['metadatas']
                )
                
                if not result['ids']:
                    print(f"⚠️ 向量 {chunk.vector_id} 不存在，跳过")
                    not_found_count += 1
                    continue
                
                # 获取现有 metadata
                current_metadata = result['metadatas'][0] if result['metadatas'] else {}
                
                # 检查是否已有 chunk_id
                if current_metadata.get('chunk_id') == chunk.id:
                    print(f"✓ 知识块 {chunk.id} 已同步，跳过")
                    continue
                
                # 更新 metadata
                current_metadata['chunk_id'] = chunk.id
                current_metadata['source'] = chunk.source or ''
                current_metadata['chapter'] = chunk.chapter or ''
                current_metadata['section'] = chunk.section or ''
                
                # 更新向量数据库
                vector_service.collection.update(
                    ids=[chunk.vector_id],
                    metadatas=[current_metadata]
                )
                
                updated_count += 1
                print(f"✅ 已同步: chunk_id={chunk.id} -> vector_id={chunk.vector_id}")
                
            except Exception as e:
                print(f"❌ 更新失败: chunk_id={chunk.id}, error={e}")
                error_count += 1
        
        # 4. 输出统计
        print(f"\n{'='*60}")
        print(f"📊 同步统计:")
        print(f"   成功更新: {updated_count}")
        print(f"   未找到: {not_found_count}")
        print(f"   失败: {error_count}")
        print(f"{'='*60}")
        
        # 5. 验证同步结果
        print(f"\n🔍 验证同步结果...")
        test_query = "指针"
        results = vector_service.search(test_query, top_k=3)
        
        print(f"   查询: '{test_query}'")
        print(f"   结果数: {len(results)}")
        
        for i, doc in enumerate(results, 1):
            chunk_id = doc.get('chunk_id') or doc.get('metadata', {}).get('chunk_id')
            print(f"   {i}. chunk_id={chunk_id}, score={doc.get('score', 0):.3f}")
            
            if chunk_id:
                # 验证数据库中是否存在
                db_chunk = KnowledgeChunk.query.get(chunk_id)
                if db_chunk:
                    print(f"      ✅ 数据库验证通过: {db_chunk.chapter}/{db_chunk.section}")
                else:
                    print(f"      ❌ 数据库中不存在此知识块")
            else:
                print(f"      ⚠️ 没有 chunk_id")
    
    print(f"\n{'='*60}")
    print("✅ 同步完成！")
    print("💡 请重新测试引用功能")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    sync_chunk_ids()