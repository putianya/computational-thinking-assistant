# -*- coding: utf-8 -*-
"""
模型模块初始化
"""
from models.user import User
from models.chat_session import ChatSession
from models.chat_message import ChatMessage
from models.knowledge_chunk import KnowledgeChunk  # ⭐ 新增

__all__ = ['User', 'ChatSession', 'ChatMessage', 'KnowledgeChunk']