# -*- coding: utf-8 -*-
"""
修复知识块引用计数问题

问题诊断：
1. 检查向量数据库中是否有 chunk_id
2. 检查数据库记录是否有 vector_id
3. 同步两者的关联关系
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from database import db
from models.knowledge_chunk import KnowledgeChunk
from services.vector_service import get_vector_service


def diagnose():
    """诊断问题"""
    print("\n" + "=" * 60)
    print("🔍 诊断知识库数据一致性")
    print("=" * 60)
    
    with app.app_context():
        # 1. 检查数据库
        db_chunks = KnowledgeChunk.query.filter_by(is_active=True).all()
        print(f"\n📊 数据库中有 {len(db_chunks)} 个活跃知识块")
        
        db_with_vector_id = [c for c in db_chunks if c.vector_id]
        print(f"   有 vector_id 的: {len(db_with_vector_id)}")
        print(f"   无 vector_id 的: {len(db_chunks) - len(db_with_vector_id)}")
        
        # 2. 检查向量数据库
        vector_service = get_vector_service()
        collection_info = vector_service.get_collection_info()
        vector_count = collection_info.get('count', 0)
        print(f"\n📊 向量数据库中有 {vector_count} 个向量")
        
        # 3. 抽样检查向量的 metadata
        if vector_count > 0:
            print(f"\n🔍 抽样检查向量 metadata...")
            
            # 获取所有向量
            all_vectors = vector_service.collection.get(
                include=['metadatas']
            )
            
            if all_vectors['ids']:
                sample_size = min(5, len(all_vectors['ids']))
                print(f"   检查前 {sample_size} 个向量:")
                
                has_chunk_id = 0
                no_chunk_id = 0
                
                for i, (vec_id, metadata) in enumerate(zip(
                    all_vectors['ids'], 
                    all_vectors['metadatas']
                )):
                    chunk_id = metadata.get('chunk_id') if metadata else None
                    
                    if chunk_id:
                        has_chunk_id += 1
                    else:
                        no_chunk_id += 1
                    
                    if i < sample_size:
                        print(f"      {vec_id}: chunk_id={chunk_id}, source={metadata.get('source', 'N/A')}")
                
                print(f"\n   统计:")
                print(f"      有 chunk_id: {has_chunk_id}")
                print(f"      无 chunk_id: {no_chunk_id} ⚠️")
                
                if no_chunk_id > 0:
                    print(f"\n   ⚠️ 发现 {no_chunk_id} 个向量缺少 chunk_id！")
                    print(f"   这是导致引用计数无法更新的原因！")
                    return False
        
        return True


def fix_by_content_matching():
    """
    通过内容匹配修复 chunk_id
    
    策略：
    1. 遍历所有数据库知识块
    2. 根据内容在向量数据库中查找对应向量
    3. 更新向量的 metadata，添加 chunk_id
    """
    print("\n" + "=" * 60)
    print("🔧 修复：通过内容匹配同步 chunk_id")
    print("=" * 60)
    
    with app.app_context():
        vector_service = get_vector_service()
        
        # 1. 获取所有数据库知识块
        db_chunks = KnowledgeChunk.query.filter_by(is_active=True).all()
        print(f"\n📊 需要处理 {len(db_chunks)} 个知识块")
        
        fixed_count = 0
        not_found_count = 0
        already_fixed_count = 0
        
        for i, chunk in enumerate(db_chunks):
            print(f"\n[{i+1}/{len(db_chunks)}] 处理知识块 ID={chunk.id}")
            print(f"   章节: {chunk.chapter}")
            print(f"   内容预览: {chunk.content[:50]}...")
            
            # 2. 如果有 vector_id，直接更新
            if chunk.vector_id:
                try:
                    result = vector_service.collection.get(
                        ids=[chunk.vector_id],
                        include=['metadatas']
                    )
                    
                    if result['ids']:
                        current_metadata = result['metadatas'][0] if result['metadatas'] else {}
                        
                        # 检查是否已有 chunk_id
                        if current_metadata.get('chunk_id') == chunk.id:
                            print(f"   ✓ 已同步")
                            already_fixed_count += 1
                            continue
                        
                        # 更新 metadata
                        current_metadata['chunk_id'] = chunk.id
                        current_metadata['source'] = chunk.source or ''
                        current_metadata['chapter'] = chunk.chapter or ''
                        current_metadata['section'] = chunk.section or ''
                        
                        vector_service.collection.update(
                            ids=[chunk.vector_id],
                            metadatas=[current_metadata]
                        )
                        
                        print(f"   ✅ 已更新 chunk_id={chunk.id} 到 vector_id={chunk.vector_id}")
                        fixed_count += 1
                        continue
                        
                except Exception as e:
                    print(f"   ⚠️ 通过 vector_id 更新失败: {e}")
            
            # 3. 如果没有 vector_id，通过内容搜索
            print(f"   🔍 通过内容搜索匹配向量...")
            
            try:
                # 使用内容前100字符搜索
                search_text = chunk.content[:200]
                results = vector_service.search(query=search_text, top_k=1)
                
                if results and results[0].get('score', 0) > 0.95:
                    # 高度匹配
                    matched_vector_id = results[0].get('id')
                    matched_score = results[0].get('score', 0)
                    
                    print(f"   🎯 找到匹配向量: {matched_vector_id} (相似度: {matched_score:.3f})")
                    
                    # 更新数据库的 vector_id
                    chunk.vector_id = matched_vector_id
                    
                    # 更新向量的 metadata
                    vec_result = vector_service.collection.get(
                        ids=[matched_vector_id],
                        include=['metadatas']
                    )
                    
                    if vec_result['ids']:
                        current_metadata = vec_result['metadatas'][0] if vec_result['metadatas'] else {}
                        current_metadata['chunk_id'] = chunk.id
                        current_metadata['source'] = chunk.source or ''
                        current_metadata['chapter'] = chunk.chapter or ''
                        current_metadata['section'] = chunk.section or ''
                        
                        vector_service.collection.update(
                            ids=[matched_vector_id],
                            metadatas=[current_metadata]
                        )
                        
                        print(f"   ✅ 双向同步完成")
                        fixed_count += 1
                else:
                    print(f"   ❌ 未找到匹配向量")
                    not_found_count += 1
                    
            except Exception as e:
                print(f"   ❌ 搜索失败: {e}")
                not_found_count += 1
        
        # 4. 提交数据库更改
        db.session.commit()
        
        # 5. 输出统计
        print("\n" + "=" * 60)
        print("📊 修复统计:")
        print(f"   新修复: {fixed_count}")
        print(f"   已同步: {already_fixed_count}")
        print(f"   未找到: {not_found_count}")
        print("=" * 60)
        
        return fixed_count


def verify_fix():
    """验证修复结果"""
    print("\n" + "=" * 60)
    print("✅ 验证修复结果")
    print("=" * 60)
    
    with app.app_context():
        vector_service = get_vector_service()
        
        # 测试检索
        test_query = "指针"
        print(f"\n🔍 测试检索: '{test_query}'")
        
        results = vector_service.search(query=test_query, top_k=3)
        
        if not results:
            print("   ❌ 未检索到结果")
            return False
        
        print(f"   检索到 {len(results)} 个结果:")
        
        all_have_chunk_id = True
        for i, doc in enumerate(results, 1):
            metadata = doc.get('metadata', {})
            chunk_id = metadata.get('chunk_id')
            score = doc.get('score', 0)
            
            print(f"\n   结果 {i}:")
            print(f"      相似度: {score:.3f}")
            print(f"      chunk_id: {chunk_id}")
            print(f"      source: {metadata.get('source', 'N/A')}")
            
            if chunk_id:
                # 验证数据库中是否存在
                db_chunk = KnowledgeChunk.query.get(chunk_id)
                if db_chunk:
                    print(f"      ✅ 数据库验证通过")
                    print(f"      引用次数: {db_chunk.retrieved_count}")
                else:
                    print(f"      ❌ 数据库中不存在此 chunk_id")
                    all_have_chunk_id = False
            else:
                print(f"      ❌ 缺少 chunk_id")
                all_have_chunk_id = False
        
        if all_have_chunk_id:
            print("\n✅ 所有结果都有有效的 chunk_id，修复成功！")
            return True
        else:
            print("\n⚠️ 仍有部分结果缺少 chunk_id")
            return False


def test_retrieval_count():
    """测试引用计数更新"""
    print("\n" + "=" * 60)
    print("🧪 测试引用计数更新")
    print("=" * 60)
    
    with app.app_context():
        vector_service = get_vector_service()
        
        # 1. 选择一个知识块
        test_chunk = KnowledgeChunk.query.first()
        if not test_chunk:
            print("❌ 没有知识块可测试")
            return
        
        print(f"\n📄 测试知识块:")
        print(f"   ID: {test_chunk.id}")
        print(f"   章节: {test_chunk.chapter}")
        print(f"   当前引用次数: {test_chunk.retrieved_count}")
        
        old_count = test_chunk.retrieved_count or 0
        
        # 2. 模拟检索并更新
        print(f"\n🔄 模拟检索更新...")
        
        try:
            KnowledgeChunk.batch_increment_retrieved([test_chunk.id])
            db.session.commit()
            
            # 3. 重新查询
            db.session.refresh(test_chunk)
            new_count = test_chunk.retrieved_count
            
            print(f"   更新前: {old_count}")
            print(f"   更新后: {new_count}")
            
            if new_count == old_count + 1:
                print(f"   ✅ 引用计数更新成功！")
            else:
                print(f"   ❌ 引用计数更新失败")
                
        except Exception as e:
            print(f"   ❌ 更新失败: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='修复知识块引用计数问题')
    parser.add_argument('--diagnose', action='store_true', help='仅诊断问题')
    parser.add_argument('--fix', action='store_true', help='执行修复')
    parser.add_argument('--verify', action='store_true', help='验证修复结果')
    parser.add_argument('--test', action='store_true', help='测试引用计数更新')
    parser.add_argument('--all', action='store_true', help='执行所有步骤')
    
    args = parser.parse_args()
    
    if args.all or args.diagnose:
        diagnose()
    
    if args.all or args.fix:
        fix_by_content_matching()
    
    if args.all or args.verify:
        verify_fix()
    
    if args.all or args.test:
        test_retrieval_count()
    
    if not any([args.diagnose, args.fix, args.verify, args.test, args.all]):
        print("使用方法:")
        print("  python fix_chunk_ids.py --diagnose  # 诊断问题")
        print("  python fix_chunk_ids.py --fix       # 执行修复")
        print("  python fix_chunk_ids.py --verify    # 验证结果")
        print("  python fix_chunk_ids.py --test      # 测试计数")
        print("  python fix_chunk_ids.py --all       # 执行所有")