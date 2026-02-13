# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\tests\test_data_collection.py
# -*- coding: utf-8 -*-
"""
测试学习数据采集服务
"""

import sys
import os

# ⭐ 修复：添加正确的项目根目录路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)  # backend 目录
project_dir = os.path.dirname(backend_dir)  # 项目根目录

# 将 backend 目录添加到路径
sys.path.insert(0, backend_dir)

# ⭐ 修复：直接导入（不使用 backend 前缀）
from database import db
from models.user import User
from models.chat_session import ChatSession
from models.learning_record import LearningRecord
from models.error_pattern import ErrorPattern
from services.analytics.data_collector import DataCollector
from datetime import datetime
import uuid
import json  # ⭐ 新增：用于解析 JSON 数据

# ⭐ 修复：初始化 Flask 应用
from flask import Flask

app = None


def init_app():
    """初始化 Flask 应用和数据库"""
    global app
    
    if app is not None:
        return app
    
    print("🔧 初始化 Flask 应用...")
    
    # 创建 Flask 应用
    app = Flask(__name__)
    
    # 配置数据库
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///computational_thinking.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化数据库
    db.init_app(app)
    
    # 创建表
    with app.app_context():
        db.create_all()
        print("✅ 数据库初始化完成")
    
    return app


def setup_test_data():
    """创建测试用户和会话"""
    print("\n[1/4] 创建测试用户...")
    
    # 创建测试用户
    test_user = User.query.filter_by(username='test_collector').first()
    if not test_user:
        test_user = User(
            username='test_collector',
            email='collector@test.com',
            role='student'
        )
        test_user.set_password('test123')
        db.session.add(test_user)
        db.session.commit()
        print(f"✅ 创建测试用户: {test_user.username} (ID: {test_user.id})")
    else:
        print(f"✅ 使用现有用户: {test_user.username} (ID: {test_user.id})")
    
    # 创建测试会话
    test_session = ChatSession(
        session_id=f"test_session_{uuid.uuid4().hex[:16]}",
        user_id=test_user.id,
        title='测试数据采集',
        is_active=True
    )
    db.session.add(test_session)
    db.session.commit()
    print(f"✅ 创建测试会话: {test_session.title} (ID: {test_session.id})")
    
    return test_user, test_session


def get_record_content(record):
    """辅助函数：解析记录的 content 字段"""
    if record.content:
        try:
            return json.loads(record.content)
        except:
            return {}
    return {}


def test_record_question():
    """测试记录提问行为"""
    print("\n[2/4] 测试提问记录...")
    
    test_user, test_session = setup_test_data()
    
    # 测试记录提问
    questions = [
        ("什么是指针？", ["指针", "内存管理"]),
        ("如何使用数组？", ["数组", "数据结构"]),
        ("循环语句怎么写？", ["循环", "控制结构"])
    ]
    
    for question, topics in questions:
        record = DataCollector.record_question(
            user_id=test_user.id,
            session_id=test_session.id,
            question=question,
            knowledge_topics=topics
        )
        
        if record:
            print(f"✅ 记录提问: {question[:20]}... (ID: {record.id})")
        else:
            print(f"❌ 记录失败: {question}")
    
    # 查询记录
    count = LearningRecord.query.filter_by(
        user_id=test_user.id,
        action_type='ask'
    ).count()
    print(f"\n📊 总共记录了 {count} 条提问")


def test_record_code_submission():
    """测试记录代码提交"""
    print("\n[3/4] 测试代码提交记录...")
    
    test_user, test_session = setup_test_data()
    
    # 模拟代码分析结果
    test_cases = [
        {
            'code': '#include <stdio.h>\nint main() { return 0; }',
            'result': {
                'score': 85,
                'level': 'B',
                'syntax_check': {
                    'valid': True
                },
                'features': {
                    'functions': ['main']
                }
            }
        },
        {
            'code': '#include <stdio.h>\nint main() { int x = 10 return 0; }',
            'result': {
                'score': 40,
                'level': 'F',
                'syntax_check': {
                    'valid': False,
                    'errors': [
                        {
                            'line': 2,
                            'message': '缺少分号',
                            'related_topic': 'C语言语法'
                        }
                    ]
                },
                'features': {
                    'functions': ['main']
                }
            }
        },
        {
            'code': '#include <stdio.h>\nint main() { int arr[5]; return 0; }',
            'result': {
                'score': 75,
                'level': 'C',
                'syntax_check': {
                    'valid': True
                },
                'ai_analysis': {
                    'problems': [
                        {
                            'severity': 'warning',
                            'description': '数组未初始化',
                            'related_topic': '数组'
                        }
                    ]
                },
                'features': {
                    'functions': ['main']
                }
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        record = DataCollector.record_code_submission(
            user_id=test_user.id,
            session_id=test_session.id,
            code=test_case['code'],
            result=test_case['result']
        )
        
        if record:
            print(f"✅ 记录代码提交 {i}: Score {test_case['result']['score']} (ID: {record.id})")
        else:
            print(f"❌ 记录失败: 测试用例 {i}")
    
    # 查询统计
    code_count = LearningRecord.query.filter_by(
        user_id=test_user.id,
        action_type='code_submit'
    ).count()
    
    error_count = ErrorPattern.query.filter_by(
        user_id=test_user.id
    ).count()
    
    print(f"\n📊 总共记录了:")
    print(f"   - {code_count} 条代码提交")
    print(f"   - {error_count} 个错误模式")
    
    # 显示错误模式
    if error_count > 0:
        print("\n📋 错误模式详情:")
        patterns = ErrorPattern.query.filter_by(user_id=test_user.id).all()
        for pattern in patterns:
            print(f"   - [{pattern.error_type}] {pattern.error_description} (出现 {pattern.occurrence_count} 次)")


def test_record_knowledge_view():
    """测试记录知识查看"""
    print("\n[4/4] 测试知识查看记录...")
    
    test_user, test_session = setup_test_data()
    
    knowledge_topics = [
        ("指针基础", 120),
        ("数组操作", 90),
        ("循环语句", 60)
    ]
    
    for topic, duration in knowledge_topics:
        record = DataCollector.record_knowledge_view(
            user_id=test_user.id,
            session_id=test_session.id,
            knowledge_title=topic,
            duration_seconds=duration
        )
        
        if record:
            print(f"✅ 记录知识查看: {topic} (时长: {duration}秒)")
        else:
            print(f"❌ 记录失败: {topic}")
    
    # 查询统计
    view_count = LearningRecord.query.filter_by(
        user_id=test_user.id,
        action_type='view_knowledge'
    ).count()
    print(f"\n📊 总共记录了 {view_count} 条知识查看")


def test_activity_summary():
    """测试活动摘要"""
    print("\n[📊] 测试活动摘要...")
    
    test_user, _ = setup_test_data()
    
    summary = DataCollector.get_user_activity_summary(
        user_id=test_user.id,
        days=7
    )
    
    if summary:
        print("\n✅ 用户活动摘要（最近7天）:")
        print(f"   - 总行为数: {summary['total_actions']}")
        print(f"   - 提问次数: {summary['ask_count']}")
        print(f"   - 代码提交: {summary['code_submit_count']}")
        print(f"   - 知识查看: {summary['view_knowledge_count']}")
    else:
        print("❌ 获取活动摘要失败")


def test_edge_cases():
    """测试边界情况和异常处理"""
    print("\n[5/9] 测试边界情况...")
    
    test_user, test_session = setup_test_data()
    
    # 测试1: 空问题
    record = DataCollector.record_question(
        user_id=test_user.id,
        session_id=test_session.id,
        question="",
        knowledge_topics=[]
    )
    print(f"{'✅' if record else '❌'} 测试空问题: {'记录成功' if record else '正确拒绝'}")
    
    # 测试2: 超长问题
    long_question = "什么是指针？" * 100
    record = DataCollector.record_question(
        user_id=test_user.id,
        session_id=test_session.id,
        question=long_question,
        knowledge_topics=["指针"]
    )
    if record:
        content = get_record_content(record)  # ⭐ 修复：使用辅助函数
        question_len = len(content.get('question', ''))
        print(f"✅ 测试超长问题: 记录了 {question_len} 字符")
    else:
        print(f"❌ 超长问题记录失败")
    
    # 测试3: 无效用户ID
    try:
        record = DataCollector.record_question(
            user_id=99999,
            session_id=test_session.id,
            question="测试问题",
            knowledge_topics=["测试"]
        )
        print(f"❌ 无效用户ID应该失败")
    except Exception as e:
        print(f"✅ 正确捕获异常: {type(e).__name__}")
    
    # 测试4: 空代码提交
    record = DataCollector.record_code_submission(
        user_id=test_user.id,
        session_id=test_session.id,
        code="",
        result={'score': 0, 'level': 'F', 'syntax_check': {'valid': False}}
    )
    print(f"{'✅' if record else '❌'} 测试空代码: {'记录成功' if record else '正确拒绝'}")


def test_error_pattern_tracking():
    """测试错误模式追踪和更新"""
    print("\n[6/9] 测试错误模式追踪...")
    
    test_user, test_session = setup_test_data()
    
    # 重复提交相同错误
    same_error_code = '#include <stdio.h>\nint main() { int x = 10 return 0; }'
    same_error_result = {
        'score': 40,
        'level': 'F',
        'syntax_check': {
            'valid': False,
            'errors': [
                {
                    'line': 2,
                    'message': '缺少分号',
                    'related_topic': 'C语言语法'
                }
            ]
        },
        'features': {'functions': ['main']}
    }
    
    # 第一次提交
    record1 = DataCollector.record_code_submission(
        user_id=test_user.id,
        session_id=test_session.id,
        code=same_error_code,
        result=same_error_result
    )
    
    # 第二次提交相同错误
    record2 = DataCollector.record_code_submission(
        user_id=test_user.id,
        session_id=test_session.id,
        code=same_error_code,
        result=same_error_result
    )
    
    # 检查错误模式是否更新
    pattern = ErrorPattern.query.filter_by(
        user_id=test_user.id,
        error_description='缺少分号'
    ).first()
    
    if pattern:
        print(f"✅ 错误模式更新: '缺少分号' 出现 {pattern.occurrence_count} 次")
        print(f"   最后出现: {pattern.last_seen}")  # ⭐ 修复：last_seen 而不是 last_occurrence
    else:
        print(f"❌ 错误模式未创建")


def test_knowledge_topics_aggregation():
    """测试知识点聚合统计"""
    print("\n[7/9] 测试知识点统计...")
    
    test_user, test_session = setup_test_data()
    
    # 提交多个包含相同知识点的问题
    questions = [
        ("指针是什么？", ["指针", "内存管理"]),
        ("指针如何使用？", ["指针", "语法"]),
        ("数组和指针的关系？", ["指针", "数组"]),
    ]
    
    for question, topics in questions:
        DataCollector.record_question(
            user_id=test_user.id,
            session_id=test_session.id,
            question=question,
            knowledge_topics=topics
        )
    
    # 统计知识点频率
    from sqlalchemy import func
    topic_stats = db.session.query(
        func.count(LearningRecord.id).label('count')
    ).filter(
        LearningRecord.user_id == test_user.id,
        LearningRecord.action_type == 'ask',
        LearningRecord.knowledge_topics.like('%指针%')
    ).scalar()
    
    print(f"✅ '指针' 知识点出现 {topic_stats} 次")


def test_time_series_analysis():
    """测试时间序列分析"""
    print("\n[8/9] 测试时间序列分析...")
    
    test_user, test_session = setup_test_data()
    
    from datetime import timedelta
    import time
    
    # 模拟不同时间的学习行为
    for i in range(5):
        DataCollector.record_question(
            user_id=test_user.id,
            session_id=test_session.id,
            question=f"测试问题 {i+1}",
            knowledge_topics=["测试"]
        )
        time.sleep(0.1)  # 确保时间戳不同
    
    # 查询最近的记录
    recent_records = LearningRecord.query.filter(
        LearningRecord.user_id == test_user.id,
        LearningRecord.created_at >= datetime.now() - timedelta(minutes=1)
    ).order_by(LearningRecord.created_at.asc()).all()
    
    if len(recent_records) >= 2:
        time_diff = (recent_records[-1].created_at - recent_records[0].created_at).total_seconds()
        print(f"✅ 时间跨度: {time_diff:.2f} 秒")
        print(f"   记录数: {len(recent_records)}")
    else:
        print(f"❌ 记录不足")


def test_performance_metrics():
    """测试性能指标计算"""
    print("\n[9/9] 测试性能指标...")
    
    test_user, test_session = setup_test_data()
    
    # 提交不同分数的代码
    scores = [85, 75, 90, 65, 80, 95]
    
    for score in scores:
        DataCollector.record_code_submission(
            user_id=test_user.id,
            session_id=test_session.id,
            code=f'// Test code for score {score}',
            result={
                'score': score,
                'level': 'A' if score >= 90 else 'B',
                'syntax_check': {'valid': True},
                'features': {'functions': ['main']}
            }
        )
    
    # 计算统计数据
    code_records = LearningRecord.query.filter(
        LearningRecord.user_id == test_user.id,
        LearningRecord.action_type == 'code_submit'
    ).all()
    
    # 手动计算平均分
    total_score = 0
    score_count = 0
    pass_count = 0
    
    for record in code_records:
        content = get_record_content(record)
        score = content.get('score', 0)
        if score > 0:
            total_score += score
            score_count += 1
            if score >= 60:
                pass_count += 1
    
    avg_score = total_score / score_count if score_count > 0 else 0
    pass_rate = (pass_count / score_count * 100) if score_count > 0 else 0
    
    print(f"✅ 性能指标:")
    print(f"   - 平均分数: {avg_score:.2f}")
    print(f"   - 提交总数: {score_count}")
    print(f"   - 通过数量: {pass_count}")
    print(f"   - 通过率: {pass_rate:.1f}%")


def test_concurrent_submissions():
    """测试并发提交"""
    print("\n[额外] 测试并发提交...")
    
    test_user, test_session = setup_test_data()
    
    import threading
    
    results = []
    
    def submit_question(question_id):
        try:
            record = DataCollector.record_question(
                user_id=test_user.id,
                session_id=test_session.id,
                question=f"并发测试问题 {question_id}",
                knowledge_topics=["并发测试"]
            )
            results.append(record is not None)
        except Exception as e:
            results.append(False)
            print(f"❌ 线程 {question_id} 失败: {e}")
    
    # 创建10个并发线程
    threads = []
    for i in range(10):
        thread = threading.Thread(target=submit_question, args=(i,))
        threads.append(thread)
        thread.start()
    
    # 等待所有线程完成
    for thread in threads:
        thread.join()
    
    success_count = sum(results)
    print(f"✅ 并发提交: {success_count}/{len(results)} 成功")


def test_data_validation():
    """测试数据验证"""
    print("\n[额外] 测试数据验证...")
    
    test_user, test_session = setup_test_data()
    
    # 测试负分数
    negative_score_result = {
        'score': -10,
        'level': 'F',
        'syntax_check': {'valid': False}
    }
    
    record = DataCollector.record_code_submission(
        user_id=test_user.id,
        session_id=test_session.id,
        code='// negative test',
        result=negative_score_result
    )
    
    if record:
        content = get_record_content(record)
        actual_score = content.get('score', 0)
        if actual_score >= 0:
            print(f"✅ 负分数被修正为: {actual_score}")
        else:
            print(f"⚠️ 负分数未修正: {actual_score}")
    else:
        print(f"❌ 记录失败")


def test_cleanup_strategy():
    """测试数据清理策略"""
    print("\n[额外] 测试数据清理...")
    
    test_user, _ = setup_test_data()
    
    # 创建旧数据
    from datetime import timedelta
    old_date = datetime.now() - timedelta(days=91)
    
    old_record = LearningRecord(
        user_id=test_user.id,
        session_id=1,
        action_type='ask',
        content=json.dumps({'question': '旧数据测试'}),
        created_at=old_date
    )
    db.session.add(old_record)
    db.session.commit()
    
    # 查询旧数据
    old_records = LearningRecord.query.filter(
        LearningRecord.user_id == test_user.id,
        LearningRecord.created_at < datetime.now() - timedelta(days=60)
    ).count()
    
    print(f"✅ 发现 {old_records} 条旧数据（>60天）")
    print(f"   建议: {'需要清理' if old_records > 100 else '暂不需要'}")


def show_all_records():
    """显示所有测试记录"""
    print("\n" + "=" * 60)
    print("📋 所有学习记录")
    print("=" * 60)
    
    test_user = User.query.filter_by(username='test_collector').first()
    if not test_user:
        print("❌ 测试用户不存在")
        return
    
    records = LearningRecord.query.filter_by(user_id=test_user.id) \
                                  .order_by(LearningRecord.created_at.desc()) \
                                  .limit(20).all()
    
    if not records:
        print("暂无记录")
        return
    
    for record in records:
        print(f"\n[{record.action_type.upper()}] ID: {record.id}")
        print(f"  时间: {record.created_at}")
        print(f"  会话: {record.session_id}")
        print(f"  知识点: {record.knowledge_topics or '无'}")
        if record.is_correct is not None:
            print(f"  正确性: {'✅ 正确' if record.is_correct else '❌ 错误'}")


def cleanup_test_data():
    """清理测试数据"""
    print("\n[🗑️] 清理测试数据...")
    
    confirm = input("确定要清理所有测试数据吗？(yes/no): ")
    
    if confirm.lower() != 'yes':
        print("❌ 操作已取消")
        return
    
    test_user = User.query.filter_by(username='test_collector').first()
    if not test_user:
        print("❌ 测试用户不存在")
        return
    
    # 删除学习记录
    lr_count = LearningRecord.query.filter_by(user_id=test_user.id).delete()
    
    # 删除错误模式
    ep_count = ErrorPattern.query.filter_by(user_id=test_user.id).delete()
    
    # 删除会话
    cs_count = ChatSession.query.filter_by(user_id=test_user.id).delete()
    
    # 删除用户
    db.session.delete(test_user)
    
    db.session.commit()
    
    print(f"✅ 清理完成:")
    print(f"   - 学习记录: {lr_count} 条")
    print(f"   - 错误模式: {ep_count} 条")
    print(f"   - 会话: {cs_count} 条")
    print(f"   - 用户: 1 个")


def main():
    """主测试流程"""
    print("=" * 60)
    print("测试学习数据采集服务 - 完整版")
    print("=" * 60)
    
    try:
        # 基础功能测试
        test_record_question()
        test_record_code_submission()
        test_record_knowledge_view()
        test_activity_summary()
        
        # 扩展测试
        test_edge_cases()
        test_error_pattern_tracking()
        test_knowledge_topics_aggregation()
        test_time_series_analysis()
        test_performance_metrics()
        
        # 额外测试（可选）
        print("\n" + "=" * 60)
        print("额外测试（性能和健壮性）")
        print("=" * 60)
        test_concurrent_submissions()
        test_data_validation()
        test_cleanup_strategy()
        
        # 显示记录
        show_all_records()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        
        # 询问是否清理
        print("\n是否清理测试数据？")
        cleanup_test_data()
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='测试学习数据采集')
    parser.add_argument('action', nargs='?', default='all',
                       choices=['all', 'question', 'code', 'knowledge', 'summary', 'show', 'cleanup'],
                       help='测试操作')
    
    args = parser.parse_args()
    
    # ⭐ 先初始化应用
    app = init_app()
    
    # ⭐ 在应用上下文中运行测试
    with app.app_context():
        if args.action == 'all':
            main()
        elif args.action == 'question':
            setup_test_data()
            test_record_question()
        elif args.action == 'code':
            setup_test_data()
            test_record_code_submission()
        elif args.action == 'knowledge':
            setup_test_data()
            test_record_knowledge_view()
        elif args.action == 'summary':
            setup_test_data()
            test_activity_summary()
        elif args.action == 'show':
            show_all_records()
        elif args.action == 'cleanup':
            cleanup_test_data()
