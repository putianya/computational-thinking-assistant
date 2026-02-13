# -*- coding: utf-8 -*-
"""
数据库初始化模块
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_db(app):
    """
    初始化数据库
    
    Args:
        app: Flask 应用实例
    """
    db.init_app(app)
    
    with app.app_context():
        # ⭐ 导入所有模型（确保表被创建）
        from models.user import User
        from models.chat_session import ChatSession
        from models.chat_message import ChatMessage
        # ⭐⭐⭐ 新增：学习分析模型 ⭐⭐⭐
        from models.learning_record import LearningRecord
        from models.error_pattern import ErrorPattern
        from models.learning_report import LearningReport
        
        # 创建所有表
        db.create_all()
        print("✅ 数据库初始化完成")
        
        # 打印表信息
        tables = db.metadata.tables.keys()
        print(f"📊 已创建的表: {', '.join(tables)}")