# -*- coding: utf-8 -*-
"""
创建学习分析相关的数据表
用于初始化 learning_records, error_patterns, learning_reports 表
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import db, init_db
from backend.models.learning_record import LearningRecord
from backend.models.error_pattern import ErrorPattern
from backend.models.learning_report import LearningReport


def create_analytics_tables():
    """
    创建学习分析相关的数据表
    """
    print("=" * 60)
    print("创建学习分析数据表")
    print("=" * 60)
    
    try:
        # 初始化数据库连接
        print("\n[1/4] 初始化数据库连接...")
        init_db()
        print("✅ 数据库连接成功")
        
        # 创建表
        print("\n[2/4] 创建数据表...")
        
        # 检查表是否已存在
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        existing_tables = inspector.get_table_names()
        
        tables_to_create = {
            'learning_records': LearningRecord,
            'error_patterns': ErrorPattern,
            'learning_reports': LearningReport
        }
        
        for table_name, model in tables_to_create.items():
            if table_name in existing_tables:
                print(f"⚠️  表 {table_name} 已存在，跳过创建")
            else:
                print(f"📝 创建表 {table_name}...")
        
        # 创建所有表（如果不存在）
        db.create_all()
        print("✅ 数据表创建完成")
        
        # 验证表结构
        print("\n[3/4] 验证表结构...")
        inspector = inspect(db.engine)
        
        for table_name, model in tables_to_create.items():
            if table_name in inspector.get_table_names():
                columns = inspector.get_columns(table_name)
                print(f"\n✅ {table_name} 表结构:")
                for col in columns:
                    print(f"   - {col['name']}: {col['type']}")
            else:
                print(f"❌ {table_name} 表创建失败")
        
        # 显示外键关系
        print("\n[4/4] 验证外键关系...")
        for table_name in tables_to_create.keys():
            foreign_keys = inspector.get_foreign_keys(table_name)
            if foreign_keys:
                print(f"\n✅ {table_name} 外键:")
                for fk in foreign_keys:
                    print(f"   - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
            else:
                print(f"ℹ️  {table_name} 无外键")
        
        print("\n" + "=" * 60)
        print("✅ 学习分析数据表创建成功！")
        print("=" * 60)
        
        # 显示使用说明
        print("\n📚 使用说明:")
        print("1. learning_records: 记录用户的学习行为（提问、代码提交、查看知识等）")
        print("2. error_patterns: 记录用户的常见错误模式，用于分析和改进")
        print("3. learning_reports: 存储定期生成的学习分析报告")
        print("\n可以在业务代码中使用这些模型来记录和分析学习数据。")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 创建数据表失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def drop_analytics_tables():
    """
    删除学习分析相关的数据表（谨慎使用！）
    """
    print("=" * 60)
    print("⚠️  警告：即将删除学习分析数据表！")
    print("=" * 60)
    
    confirm = input("\n确定要删除所有学习分析数据表吗？这将清除所有数据！(yes/no): ")
    
    if confirm.lower() != 'yes':
        print("❌ 操作已取消")
        return False
    
    try:
        init_db()
        
        # 删除表
        tables = ['learning_reports', 'error_patterns', 'learning_records']
        
        for table_name in tables:
            print(f"🗑️  删除表 {table_name}...")
            db.session.execute(f"DROP TABLE IF EXISTS {table_name} CASCADE")
        
        db.session.commit()
        
        print("\n✅ 学习分析数据表已删除")
        return True
        
    except Exception as e:
        print(f"\n❌ 删除数据表失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_table_info():
    """
    显示数据表信息
    """
    print("=" * 60)
    print("学习分析数据表信息")
    print("=" * 60)
    
    try:
        init_db()
        
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        
        tables = {
            'learning_records': '学习行为记录表',
            'error_patterns': '错误模式表',
            'learning_reports': '学习报告表'
        }
        
        for table_name, description in tables.items():
            print(f"\n📋 {description} ({table_name})")
            
            if table_name in inspector.get_table_names():
                # 显示列信息
                columns = inspector.get_columns(table_name)
                print("\n字段列表:")
                for col in columns:
                    nullable = "NULL" if col['nullable'] else "NOT NULL"
                    default = f", 默认值: {col['default']}" if col['default'] else ""
                    print(f"  - {col['name']}: {col['type']} ({nullable}{default})")
                
                # 显示索引
                indexes = inspector.get_indexes(table_name)
                if indexes:
                    print("\n索引:")
                    for idx in indexes:
                        unique = "UNIQUE" if idx['unique'] else "INDEX"
                        print(f"  - {idx['name']}: {unique} on {idx['column_names']}")
                
                # 统计记录数
                from sqlalchemy import text
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                print(f"\n📊 记录数: {count}")
            else:
                print("❌ 表不存在")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"\n❌ 获取表信息失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='学习分析数据表管理工具')
    parser.add_argument('action', choices=['create', 'drop', 'info'], 
                       help='操作类型: create(创建表), drop(删除表), info(查看信息)')
    
    args = parser.parse_args()
    
    if args.action == 'create':
        create_analytics_tables()
    elif args.action == 'drop':
        drop_analytics_tables()
    elif args.action == 'info':
        show_table_info()
