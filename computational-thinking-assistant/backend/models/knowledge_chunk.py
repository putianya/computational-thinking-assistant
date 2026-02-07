# -*- coding: utf-8 -*-
"""
知识块模型

功能：
1. 存储分块后的知识文本
2. 关联向量数据库中的向量 ID
3. 记录检索和使用统计
4. 支持知识库管理和优化

作者: 计算思维助手团队
日期: 2026-01-21
"""

from database import db
from datetime import datetime
from typing import Dict, List, Optional


class KnowledgeChunk(db.Model):
    """
    知识块模型（存储分块后的知识）
    
    设计说明：
    ├─ 一份文档会被切分成多个 chunk
    ├─ 每个 chunk 有对应的向量（存在向量数据库中）
    ├─ 本表存储文本内容和元数据
    └─ 向量存储在专门的向量数据库（如 Milvus、Qdrant）
    
    使用场景：
    1. RAG 检索：根据 vector_id 找到相似向量，再用 id 查询文本
    2. 知识管理：按 source、chapter 组织知识
    3. 统计分析：根据 retrieved_count 优化知识库
    """
    
    __tablename__ = 'knowledge_chunks'
    
    # ========== 主键 ==========
    id = db.Column(
        db.Integer, 
        primary_key=True,
        comment='知识块唯一标识'
    )
    
    # ========== 文本内容 ==========
    content = db.Column(
        db.Text, 
        nullable=False,
        comment='分块后的知识文本内容'
    )
    
    content_hash = db.Column(
        db.String(64),
        unique=True,
        index=True,
        comment='内容哈希（用于去重）'
    )
    
    # ========== 元数据 ==========
    source = db.Column(
        db.String(255),
        index=True,
        comment='来源文档（如：《C语言程序设计》第3版）'
    )
    
    chapter = db.Column(
        db.String(100),
        index=True,
        comment='所属章节（如：第2章 数据类型）'
    )
    
    section = db.Column(
        db.String(100),
        comment='所属小节（如：2.1 基本数据类型）'
    )
    
    keywords = db.Column(
        db.String(500),
        comment='关键词（逗号分隔，用于关键词检索）'
    )

    level = db.Column(
        db.Integer,
        default=2,
        comment='标题层级（2=##, 3=###）'
    )
    
    
    # ========== 向量相关 ==========
    vector_id = db.Column(
        db.String(100),
        unique=True,
        index=True,
        comment='向量数据库中的向量 ID'
    )
    
    embedding_model = db.Column(
        db.String(50),
        default='text-embedding-ada-002',
        comment='生成向量使用的模型'
    )
    
    # ========== 统计数据 ==========
    retrieved_count = db.Column(
        db.Integer, 
        default=0,
        comment='被检索次数（用于热度分析）'
    )
    
    helpful_count = db.Column(
        db.Integer, 
        default=0,
        comment='用户标记为有用的次数'
    )
    
    unhelpful_count = db.Column(
        db.Integer,
        default=0,
        comment='用户标记为无用的次数'
    )
    
    # ========== 内容特征 ==========
    char_count = db.Column(
        db.Integer,
        comment='字符数（用于分块质量评估）'
    )
    
    word_count = db.Column(
        db.Integer,
        comment='词数（英文）'
    )
    
    has_code = db.Column(
        db.Boolean,
        default=False,
        comment='是否包含代码片段'
    )
    
    has_formula = db.Column(
        db.Boolean,
        default=False,
        comment='是否包含数学公式'
    )
    
    # ========== 状态标记 ==========
    is_active = db.Column(
        db.Boolean,
        default=True,
        index=True,
        comment='是否启用（支持软删除）'
    )
    
    quality_score = db.Column(
        db.Float,
        default=1.0,
        comment='内容质量评分（0-1，用于检索排序）'
    )
    
    # ========== 时间戳 ==========
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment='创建时间'
    )
    
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        comment='最后更新时间'
    )
    
    last_retrieved_at = db.Column(
        db.DateTime,
        comment='最后一次被检索的时间'
    )
    
    # ========== 索引 ==========
    __table_args__ = (
        db.Index('idx_source_chapter', 'source', 'chapter'),
        db.Index('idx_active_quality', 'is_active', 'quality_score'),
        db.Index('idx_retrieved_count', 'retrieved_count'),
    )
    
    
    def __repr__(self):
        """字符串表示"""
        return f"<KnowledgeChunk(id={self.id}, source='{self.source}', chapter='{self.chapter}')>"
    
    
    def to_dict(self, include_stats: bool = False) -> Dict:
        """
        转换为字典
        
        Args:
            include_stats: 是否包含统计数据
            
        Returns:
            字典格式的知识块信息
        """
        result = {
            'id': self.id,
            'content': self.content,
            'source': self.source,
            'chapter': self.chapter,
            'section': self.section,
            'keywords': self.keywords.split(',') if self.keywords else [],
            'has_code': self.has_code,
            'has_formula': self.has_formula,
            'char_count': self.char_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        
        # 可选：包含统计数据
        if include_stats:
            result.update({
                'retrieved_count': self.retrieved_count,
                'helpful_count': self.helpful_count,
                'unhelpful_count': self.unhelpful_count,
                'quality_score': self.quality_score,
                'last_retrieved_at': self.last_retrieved_at.isoformat() if self.last_retrieved_at else None,
            })
        
        return result
    
    
    def increment_retrieved(self):
        """
        增加检索计数
        
        调用时机：每次这个 chunk 被检索到时
        """
        self.retrieved_count += 1
        self.last_retrieved_at = datetime.utcnow()
        db.session.commit()
    
    
    def mark_helpful(self):
        """
        标记为有用
        
        调用时机：用户点击"有帮助"按钮时
        """
        self.helpful_count += 1
        self._update_quality_score()
        db.session.commit()
    
    
    def mark_unhelpful(self):
        """
        标记为无用
        
        调用时机：用户点击"无帮助"按钮时
        """
        self.unhelpful_count += 1
        self._update_quality_score()
        db.session.commit()
    
    
    def _update_quality_score(self):
        """
        更新质量评分
        
        算法：
        quality_score = (helpful - unhelpful) / (helpful + unhelpful + 1)
        归一化到 [0, 1]
        """
        total_feedback = self.helpful_count + self.unhelpful_count
        
        if total_feedback == 0:
            self.quality_score = 1.0  # 默认分数
        else:
            # 计算有用率
            helpful_ratio = self.helpful_count / total_feedback
            
            # 归一化到 [0.2, 1.0] 范围（避免过低）
            self.quality_score = 0.2 + (helpful_ratio * 0.8)
    
    
    def get_keywords_list(self) -> List[str]:
        """
        获取关键词列表
        
        Returns:
            关键词数组
        """
        if not self.keywords:
            return []
        return [kw.strip() for kw in self.keywords.split(',') if kw.strip()]
    
    
    def set_keywords_list(self, keywords: List[str]):
        """
        设置关键词列表
        
        Args:
            keywords: 关键词数组
        """
        self.keywords = ','.join([kw.strip() for kw in keywords if kw.strip()])
    
    
    def calculate_content_features(self):
        """
        计算内容特征
        
        自动检测：
        - 字符数
        - 词数
        - 是否包含代码
        - 是否包含公式
        """
        if not self.content:
            return
        
        # 字符数
        self.char_count = len(self.content)
        
        # 词数（简单分词）
        self.word_count = len(self.content.split())
        
        # 检测代码（包含代码块标记或关键字）
        code_indicators = ['```', 'def ', 'class ', 'import ', 'for ', 'while ', 'if ', '{', '}']
        self.has_code = any(indicator in self.content for indicator in code_indicators)
        
        # 检测公式（包含数学符号）
        formula_indicators = ['∫', '∑', '√', '∂', '∞', '≠', '≤', '≥', '±', '×', '÷']
        self.has_formula = any(indicator in self.content for indicator in formula_indicators)
    
    
    @staticmethod
    def generate_content_hash(content: str) -> str:
        """
        生成内容哈希（用于去重）
        
        Args:
            content: 内容文本
            
        Returns:
            SHA-256 哈希值
        """
        import hashlib
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    
    @classmethod
    def create_chunk(cls, 
                    content: str,
                    source: str,
                    chapter: str = None,
                    section: str = None,
                    keywords: List[str] = None,
                    vector_id: str = None) -> Optional['KnowledgeChunk']:
        """
        创建知识块（带去重）
        
        Args:
            content: 文本内容
            source: 来源文档
            chapter: 章节
            section: 小节
            keywords: 关键词列表
            vector_id: 向量 ID
            
        Returns:
            新创建的知识块，如果已存在则返回 None
        """
        # 1. 生成哈希
        content_hash = cls.generate_content_hash(content)
        
        # 2. 检查是否已存在
        existing = cls.query.filter_by(content_hash=content_hash).first()
        if existing:
            print(f"⚠️ 知识块已存在: {existing.id}")
            return None
        
        # 3. 创建新知识块
        chunk = cls(
            content=content,
            content_hash=content_hash,
            source=source,
            chapter=chapter,
            section=section,
            vector_id=vector_id
        )
        
        # 4. 设置关键词
        if keywords:
            chunk.set_keywords_list(keywords)
        
        # 5. 计算内容特征
        chunk.calculate_content_features()
        
        # 6. 保存到数据库
        db.session.add(chunk)
        db.session.commit()
        
        print(f"✅ 创建知识块: {chunk.id} (来源: {source}, 章节: {chapter})")
        
        return chunk
    
    
    @classmethod
    def get_by_vector_id(cls, vector_id: str) -> Optional['KnowledgeChunk']:
        """
        根据向量 ID 查询知识块
        
        Args:
            vector_id: 向量 ID
            
        Returns:
            知识块对象
        """
        return cls.query.filter_by(vector_id=vector_id, is_active=True).first()
    
    
    @classmethod
    def get_by_source(cls, source: str, chapter: str = None) -> List['KnowledgeChunk']:
        """
        按来源查询知识块
        
        Args:
            source: 来源文档
            chapter: 章节（可选）
            
        Returns:
            知识块列表
        """
        query = cls.query.filter_by(source=source, is_active=True)
        
        if chapter:
            query = query.filter_by(chapter=chapter)
        
        return query.order_by(cls.chapter, cls.section).all()
    
    
    @classmethod
    def get_hot_chunks(cls, limit: int = 10) -> List['KnowledgeChunk']:
        """
        获取热门知识块（检索次数最多）
        
        Args:
            limit: 返回数量
            
        Returns:
            知识块列表
        """
        return cls.query.filter_by(is_active=True)\
            .order_by(cls.retrieved_count.desc())\
            .limit(limit)\
            .all()
    
    
    @classmethod
    def get_high_quality_chunks(cls, limit: int = 10) -> List['KnowledgeChunk']:
        """
        获取高质量知识块
        
        Args:
            limit: 返回数量
            
        Returns:
            知识块列表
        """
        return cls.query.filter_by(is_active=True)\
            .filter(cls.helpful_count > 0)\
            .order_by(cls.quality_score.desc())\
            .limit(limit)\
            .all()


# ========== 导入到 models/__init__.py ==========
# 在 models/__init__.py 中添加：
# from models.knowledge_chunk import KnowledgeChunk

    @classmethod
    def batch_increment_retrieved(cls, chunk_ids: List[int]):
        """
        批量增加检索计数（性能优化）
        
        Args:
            chunk_ids: 知识块 ID 列表
        """
        try:
            from sqlalchemy import update
            from datetime import datetime
            
            # 过滤掉 None 值
            valid_ids = [cid for cid in chunk_ids if cid is not None]
            
            if not valid_ids:
                print("   ⚠️ 没有有效的 chunk_id 需要更新")
                return
            
            stmt = update(cls).where(cls.id.in_(valid_ids)).values(
                retrieved_count=cls.retrieved_count + 1,
                last_retrieved_at=datetime.utcnow()
            )
            
            db.session.execute(stmt)
            db.session.commit()
            
            print(f"📈 批量更新热度: {len(valid_ids)} 个知识块")
            
        except Exception as e:
            print(f"❌ 批量更新热度失败: {e}")
            db.session.rollback()