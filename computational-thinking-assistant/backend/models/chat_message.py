# -*- coding: utf-8 -*-
"""
聊天消息模型
"""
from datetime import datetime
from database import db


class ChatMessage(db.Model):
    """
    聊天消息表
    """
    __tablename__ = 'chat_messages'
    
    # ========== 基础字段 ==========
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)  # 'user' 或 'assistant'
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    
    # ========== 🆕 RAG 相关字段 ==========
    
    # 问题上下文关键词（用于 RAG 检索）
    context_keywords = db.Column(
        db.String(500),
        nullable=True,
        comment='上文提到的关键词（逗号分隔），用于多轮对话上下文理解'
    )
    
    # 引用的知识块 ID（记录使用了哪些知识库内容）
    referenced_chunks = db.Column(
        db.String(1000),
        nullable=True,
        comment='引用的知识块 ID 列表（JSON 格式），如: [1,3,5]，支持"查看引用"功能'
    )
    
    # 检索质量评分（用于优化）
    retrieval_score = db.Column(
        db.Float,
        nullable=True,
        comment='用户对回答的评分（0.0-1.0），用于优化检索策略'
    )
    
    # ========== 索引优化 ==========
    __table_args__ = (
        db.Index('idx_session_created', 'session_id', 'created_at'),
        db.Index('idx_retrieval_score', 'retrieval_score'),
    )
    
    # ========== 原有方法 ==========
    
    def to_dict(self):
        """
        转换为字典
        """
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            # 🆕 添加 RAG 相关字段
            'context_keywords': self.get_keywords_list(),
            'referenced_chunks': self.get_referenced_chunks(),
            'retrieval_score': self.retrieval_score
        }
    
    def __repr__(self):
        return f'<ChatMessage {self.role}: {self.content[:30]}...>'
    
    # ========== 🆕 RAG 辅助方法 ==========
    
    def get_keywords_list(self):
        """
        获取关键词列表
        
        Returns:
            list: 关键词数组
        """
        if not self.context_keywords:
            return []
        return [kw.strip() for kw in self.context_keywords.split(',') if kw.strip()]
    
    def set_keywords_list(self, keywords):
        """
        设置关键词列表
        
        Args:
            keywords: 关键词数组或逗号分隔的字符串
        """
        if isinstance(keywords, list):
            self.context_keywords = ','.join([kw.strip() for kw in keywords if kw.strip()])
        elif isinstance(keywords, str):
            self.context_keywords = keywords
        else:
            self.context_keywords = ''
    
    def get_referenced_chunks(self):
        """
        获取引用的知识块 ID 列表
        
        Returns:
            list: 知识块 ID 数组，如果没有引用则返回空列表
        """
        if not self.referenced_chunks:
            return []
        
        try:
            import json
            return json.loads(self.referenced_chunks)
        except (json.JSONDecodeError, TypeError):
            # 兼容旧格式（逗号分隔）
            return [int(x.strip()) for x in self.referenced_chunks.split(',') if x.strip().isdigit()]
    
    def set_referenced_chunks(self, chunk_ids):
        """
        设置引用的知识块 ID 列表
        
        Args:
            chunk_ids: 知识块 ID 列表（数组或 JSON 字符串）
        """
        if isinstance(chunk_ids, list):
            import json
            self.referenced_chunks = json.dumps(chunk_ids)
        elif isinstance(chunk_ids, str):
            self.referenced_chunks = chunk_ids
        else:
            self.referenced_chunks = None
    
    def set_retrieval_score(self, score):
        """
        设置检索质量评分
        
        Args:
            score: 评分值（0.0-1.0）
        """
        if score is not None:
            # 确保评分在 0-1 之间
            self.retrieval_score = max(0.0, min(1.0, float(score)))
        else:
            self.retrieval_score = None
    
    def add_referenced_chunk(self, chunk_id):
        """
        添加一个引用的知识块 ID
        
        Args:
            chunk_id: 知识块 ID
        """
        current_chunks = self.get_referenced_chunks()
        if chunk_id not in current_chunks:
            current_chunks.append(chunk_id)
            self.set_referenced_chunks(current_chunks)
    
    def has_references(self):
        """
        判断是否有引用知识库内容
        
        Returns:
            bool: 是否有引用
        """
        return bool(self.get_referenced_chunks())
    
    def get_reference_count(self):
        """
        获取引用的知识块数量
        
        Returns:
            int: 引用数量
        """
        return len(self.get_referenced_chunks())