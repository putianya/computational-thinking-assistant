# -*- coding: utf-8 -*-
"""
创建知识库相关数据表
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from database import db
from models.knowledge_chunk import KnowledgeChunk


def create_tables():
    """创建数据表"""
    with app.app_context():
        print("📦 创建知识库数据表...")
        
        # 创建表
        db.create_all()
        
        print("✅ 数据表创建成功！")
        
        # 验证
        tables = db.metadata.tables.keys()
        print(f"\n📊 当前数据表列表:")
        for table in tables:
            print(f"   - {table}")


if __name__ == "__main__":
    create_tables()