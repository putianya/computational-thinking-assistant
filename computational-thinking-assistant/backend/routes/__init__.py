# -*- coding: utf-8 -*-
"""
路由模块 - 导出所有 Blueprint
"""
from routes.auth import auth_bp
from routes.chat import chat_bp
from routes.knowledge import knowledge_bp
from routes.code import code_bp
from routes.analytics import analytics_bp
from routes.admin import admin_bp

__all__ = ['auth_bp', 'chat_bp', 'knowledge_bp', 'code_bp', 'analytics_bp', 'admin_bp']
