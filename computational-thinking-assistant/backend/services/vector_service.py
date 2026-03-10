# -*- coding: utf-8 -*-
"""
向量服务 - ChromaDB 集成

功能：
1. 文本向量化（使用 sentence-transformers）
2. 向量存储（ChromaDB 持久化）
3. 相似度检索（RAG 核心）
4. 知识块管理

作者: 计算思维助手团队
日期: 2026-01-26
"""
import os
import chromadb
import torch
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional, Tuple
from config import Config
from datetime import datetime
import logging
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorService:
    """
    向量服务类（单例模式）
    
    使用方法:
        vector_service = VectorService()
        
        # 添加文档
        vector_service.add_documents(
            texts=["指针是用于存储地址的变量", "链表是线性数据结构"],
            metadatas=[{"topic": "指针"}, {"topic": "链表"}],
            ids=["chunk_1", "chunk_2"]
        )
        
        # 检索相似文档
        results = vector_service.search("什么是指针", top_k=3)
    """
    
    _instance = None  # 单例实例
    
    def __new__(cls):
        """单例模式：确保只创建一个实例"""
        if cls._instance is None:
            cls._instance = super(VectorService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化向量服务"""
        if self._initialized:
            return
    
        logger.info("=" * 60)
        logger.info("🚀 初始化向量服务...")
        logger.info("=" * 60)
        
        try:
            # ========== 步骤 1：加载 Embedding 模型 ==========
            logger.info(f"📦 加载 Embedding 模型: {Config.EMBEDDING_MODEL}")
            
            device = 'cpu'
            
            # ⭐⭐⭐ 修复：移除 trust_remote_code，使用标准加载方式 ⭐⭐⭐
            try:
                # 尝试直接加载（不使用 trust_remote_code）
                self.model = SentenceTransformer(
                    Config.EMBEDDING_MODEL,
                    device=device
                )
                logger.info("✅ 使用标准方式加载模型成功")
            except Exception as e:
                logger.warning(f"⚠️ 标准加载失败，尝试本地缓存: {e}")
                # 如果标准方式失败，尝试指定缓存目录
                cache_folder = os.path.join(os.path.dirname(__file__), '..', 'data', 'models')
                os.makedirs(cache_folder, exist_ok=True)
                
                self.model = SentenceTransformer(
                    Config.EMBEDDING_MODEL,
                    device=device,
                    cache_folder=cache_folder
                )
                logger.info("✅ 使用缓存目录加载模型成功")
            
            # ⭐ 确保模型在正确的设备上
            self.model = self.model.to(device)
            self.model.eval()
            
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            
            logger.info(f"✅ 模型加载成功")
            logger.info(f"   设备: {device}")
            logger.info(f"   向量维度: {self.embedding_dim}")
            
            # ========== 步骤 2：连接 ChromaDB ==========
            logger.info(f"\n🗄️  连接 ChromaDB...")
            
            # 确保数据目录存在
            persist_dir = os.path.abspath(Config.CHROMA_PERSIST_DIR)
            os.makedirs(persist_dir, exist_ok=True)
            
            logger.info(f"   数据目录: {persist_dir}")
            
            # 创建持久化客户端
            self.client = chromadb.PersistentClient(
                path=persist_dir,
                settings=Settings(
                    anonymized_telemetry=False,  # 关闭匿名遥测
                    allow_reset=True  # 允许重置（开发环境）
                )
            )
            
            logger.info("✅ ChromaDB 连接成功")
            
            # ========== 步骤 3：获取或创建集合 ==========
            logger.info(f"\n📚 初始化集合: {Config.COLLECTION_NAME}")
            
            # 获取或创建集合（使用余弦相似度）
            self.collection = self.client.get_or_create_collection(
                name=Config.COLLECTION_NAME,
                metadata={
                    "hnsw:space": "cosine",  # 使用余弦相似度
                    "description": "计算思维课程知识库",
                    "embedding_model": Config.EMBEDDING_MODEL,
                    "created_at": str(os.path.getmtime(persist_dir)) if os.path.exists(persist_dir) else "now"
                }
            )
            
            # 获取集合统计信息
            count = self.collection.count()
            
            logger.info("✅ 集合初始化成功")
            logger.info(f"   集合名称: {Config.COLLECTION_NAME}")
            logger.info(f"   相似度算法: 余弦相似度")
            logger.info(f"   当前文档数: {count} 条")
            
            # ========== 步骤 4：打印配置信息 ==========
            logger.info("\n⚙️  向量服务配置:")
            logger.info(f"   Top-K 结果数: {Config.TOP_K_RESULTS}")
            logger.info(f"   相似度阈值: {Config.SIMILARITY_THRESHOLD}")
            
            logger.info("=" * 60)
            logger.info("✅ 向量服务初始化完成！")
            logger.info("=" * 60)
            
            # 标记已初始化
            self._initialized = True
            
        except Exception as e:
            logger.error(f"❌ 向量服务初始化失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    # ========== 向量化方法 ==========
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        将文本转换为向量
        
        Args:
            texts: 文本列表
            
        Returns:
            向量列表（二维数组）
            
        示例:
            >>> vectors = vector_service.encode(["什么是指针", "指针的使用"])
            >>> len(vectors)
            2
            >>> len(vectors[0])  # 向量维度
            384
        """
        try:
            # 批量编码（性能更好）
            embeddings = self.model.encode(
                texts,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            # 转换为列表格式（ChromaDB 需要）
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"❌ 文本向量化失败: {e}")
            raise
    
    # ========== 文档管理方法 ==========
    
    def add_documents(self, documents: List[Dict]) -> Dict:
        """
        批量添加文档到向量数据库
        
        ⚠️⚠️⚠️ 关键修复：只负责向量化，不负责数据库插入 ⚠️⚠️⚠️
        """
        try:
            if not documents:
                return {'success': False, 'message': '文档列表为空'}
            
            logger.info(f"📤 准备添加 {len(documents)} 个文档到向量数据库...")
            
            # ========== 1. 提取文本并生成 ID ==========
            texts = []
            metadatas = []
            ids = []
            
            for i, doc in enumerate(documents):
                
                vector_id = f"chunk_{int(time.time() * 1000)}_{i}"
                doc['vector_id'] = vector_id
                texts.append(doc['content'])
                metadatas.append({
                    'source': doc.get('source', ''),
                    'chapter': doc.get('chapter', ''),
                    'section': doc.get('section', ''),
                    'level': doc.get('level', 2),
                    'chunk_id': doc.get('chunk_id')  # ⚠️ 这里是 None！需要在导入时传入
                })
                ids.append(vector_id)
            
            # ========== 2. 向量化 ==========
            logger.info(f"📝 向集合 '{self.collection.name}' 添加 {len(texts)} 个文档...")
            embeddings = self.encode(texts)
            
            # ========== 3. 添加到 ChromaDB ==========
            self.collection.add(
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"✅ 成功添加 {len(texts)} 个文档到向量数据库")
            
            # ⭐⭐⭐ 注意：不再插入数据库，只返回成功信息 ⭐⭐⭐
            return {
                'success': True,
                'message': f'成功添加 {len(texts)} 个文档到向量数据库',
                'added_count': len(texts),
                'vector_ids': ids  # ⭐ 返回向量ID列表
            }
            
        except Exception as e:
            logger.error(f"❌ 添加文档失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'添加文档失败: {str(e)}'
            }


    def search(
        self,
        query: str,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,   # ← 新增
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """检索相似文档（RAG 核心功能）"""
        try:
            top_k = top_k or Config.TOP_K_RESULTS
            threshold = Config.SIMILARITY_THRESHOLD
            
            logger.info(f"🔍 开始检索: '{query[:20]}...' (top_k={top_k}, threshold={threshold})")
            
            # 调试信息
            logger.info(f"\n{'='*60}")
            logger.info(f"🔍 向量检索调试信息")
            logger.info(f"{'='*60}")
            logger.info(f"查询文本: {query}")
            
            # 生成查询向量
            query_embedding = self.encode([query])[0]
            logger.info(f"查询向量维度: {len(query_embedding)}")
            logger.info(f"Top-K: {top_k}")
            logger.info(f"阈值: {threshold}")
            logger.info(f"集合文档数: {self.collection.count()}")
            
            # 执行检索 - ⭐⭐⭐ 确保包含 metadatas ⭐⭐⭐
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=['documents', 'metadatas', 'distances']
            )
            
            # 解析结果
            documents = []
            
            if results and results['ids'] and results['ids'][0]:
                ids = results['ids'][0]
                texts = results['documents'][0] if results['documents'] else []
                metadatas = results['metadatas'][0] if results['metadatas'] else []
                distances = results['distances'][0] if results['distances'] else []
                
                logger.info(f"\n📊 ChromaDB 原始结果:")
                logger.info(f"   返回文档数: {len(ids)}")
                logger.info(f"   距离值: {distances}")
                logger.info(f"\n   详细结果:")
                
                for i, (doc_id, text, metadata, distance) in enumerate(zip(ids, texts, metadatas, distances)):
                    # 计算相似度（余弦距离转相似度）
                    similarity = 1 - (distance / 2)
                    
                    logger.info(f"\n   结果 {i+1}:")
                    logger.info(f"      ID: {doc_id}")
                    logger.info(f"      距离: {distance:.4f}")
                    logger.info(f"      相似度: {similarity:.4f}")
                    logger.info(f"      是否通过阈值: {similarity >= threshold}")
                    logger.info(f"      内容预览: {text[:80] if text else 'N/A'}...")
                    
                    # ⭐⭐⭐ 关键：确保 metadata 中有 chunk_id ⭐⭐⭐
                    chunk_id = metadata.get('chunk_id') if metadata else None
                    logger.info(f"      chunk_id: {chunk_id}")
                    
                    documents.append({
                        'id': doc_id,
                        'text': text,
                        'score': similarity,
                        'metadata': metadata or {},
                        'chunk_id': chunk_id  # ⭐⭐⭐ 直接放在顶层，方便访问 ⭐⭐⭐
                    })
                
                logger.info(f"{'='*60}\n")
            
            # 按相似度过滤
            filtered = [doc for doc in documents if doc['score'] >= threshold]
            logger.info(f"🔍 检索到 {len(filtered)} 条相关文档（阈值 >= {threshold}）")
            
            return filtered
            
        except Exception as e:
            logger.error(f"❌ 检索失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def delete_documents(self, ids: List[str]) -> Dict:
        """
        删除文档
        
        Args:
            ids: 文档 ID 列表
            
        Returns:
            操作结果字典
        """
        try:
            self.collection.delete(ids=ids)
            
            logger.info(f"🗑️  成功删除 {len(ids)} 条文档")
            
            return {
                'success': True,
                'message': f'成功删除 {len(ids)} 条文档',
                'deleted_ids': ids
            }
            
        except Exception as e:
            logger.error(f"❌ 删除文档失败: {e}")
            return {
                'success': False,
                'message': f'删除失败: {str(e)}'
            }
    
    def update_document(self, doc_id: str, text: str, metadata: Optional[Dict] = None) -> Dict:
        """
        更新文档
        
        Args:
            doc_id: 文档 ID
            text: 新文本
            metadata: 新元数据（可选）
            
        Returns:
            操作结果字典
        """
        try:
            # 1. 向量化新文本
            embedding = self.encode([text])[0]
            
            # 2. 更新文档
            self.collection.update(
                ids=[doc_id],
                documents=[text],
                embeddings=[embedding],
                metadatas=[metadata] if metadata else None
            )
            
            logger.info(f"🔄 成功更新文档: {doc_id}")
            
            return {
                'success': True,
                'message': f'成功更新文档: {doc_id}'
            }
            
        except Exception as e:
            logger.error(f"❌ 更新文档失败: {e}")
            return {
                'success': False,
                'message': f'更新失败: {str(e)}'
            }
    
    def get_collection_info(self) -> Dict:
        """
        获取集合统计信息
        
        Returns:
            集合信息字典
        """
        try:
            count = self.collection.count()
            metadata = self.collection.metadata
            
            return {
                'success': True,
                'name': Config.COLLECTION_NAME,
                'count': count,
                'embedding_dim': self.embedding_dim,
                'metadata': metadata
            }
            
        except Exception as e:
            logger.error(f"❌ 获取集合信息失败: {e}")
            return {
                'success': False,
                'message': f'获取失败: {str(e)}'
            }
    
    def reset_collection(self) -> Dict:
        """
        重置集合（清空所有数据）- 仅用于开发测试
        
        警告: 此操作会删除所有向量数据！
        
        Returns:
            操作结果字典
        """
        try:
            # 删除旧集合
            self.client.delete_collection(name=Config.COLLECTION_NAME)
            
            # 重新创建集合
            self.collection = self.client.create_collection(
                name=Config.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.warning(f"⚠️  集合已重置: {Config.COLLECTION_NAME}")
            
            return {
                'success': True,
                'message': '集合已重置'
            }
            
        except Exception as e:
            logger.error(f"❌ 重置集合失败: {e}")
            return {
                'success': False,
                'message': f'重置失败: {str(e)}'
            }


# ========== 便捷函数（全局单例） ==========

# 创建全局单例实例
_vector_service_instance = None


def get_vector_service() -> VectorService:
    """
    获取向量服务单例实例
    
    Returns:
        VectorService 实例
        
    示例:
        >>> from services.vector_service import get_vector_service
        >>> vector_service = get_vector_service()
        >>> results = vector_service.search("什么是指针")
    """
    global _vector_service_instance
    
    if _vector_service_instance is None:
        _vector_service_instance = VectorService()
    
    return _vector_service_instance


