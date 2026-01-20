# -*- coding: utf-8 -*-
"""
配置文件 - 应用配置和环境变量
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent


class Config:
    """应用配置类"""
    
    # ========== Flask 基础配置 ==========
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # ========== 数据库配置 ==========
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f'sqlite:///{BASE_DIR}/data/app.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG  # 开发模式下打印 SQL 语句
    
    # ========== OpenAI API 配置 ==========
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.deepseek.com')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'deepseek-chat')
    
    # ========== 聊天功能配置 ==========
    ENABLE_STREAMING = os.getenv('ENABLE_STREAMING', 'True').lower() == 'true'
    TEMPERATURE = float(os.getenv('TEMPERATURE', 0.3))
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', 1000))
    
    # ⭐⭐⭐ 新增：聊天会话配置 ⭐⭐⭐
    
    # 每个会话最多保留的消息数量（数据库存储）
    MAX_MESSAGES_PER_SESSION = int(os.getenv('MAX_MESSAGES_PER_SESSION', 50))
    
    # 发送给 AI 的上下文消息数量（默认值，可被前端覆盖）
    MAX_CONTEXT_FOR_AI = int(os.getenv('MAX_CONTEXT_FOR_AI', 10))
    
    # 默认会话标题
    DEFAULT_SESSION_TITLE = os.getenv('DEFAULT_SESSION_TITLE', '新对话')
    
    # 用户可设置的上下文范围（前端滑块的 min/max）
    MIN_CONTEXT_LENGTH = int(os.getenv('MIN_CONTEXT_LENGTH', 10))
    MAX_CONTEXT_LENGTH = int(os.getenv('MAX_CONTEXT_LENGTH', 50))
    
    # ========== 系统提示词 ==========
    SYSTEM_PROMPT = os.getenv(
        'SYSTEM_PROMPT',
        '你是计算思维课程助教，用简洁易懂的语言回答编程和算法问题。'
    )
    
    # ========== JWT 配置 ==========
    JWT_SECRET_KEY = SECRET_KEY
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保数据目录存在
        data_dir = BASE_DIR / 'data'
        data_dir.mkdir(exist_ok=True)
        print(f"✅ 数据目录: {data_dir}")
        
        # 打印配置信息
        print("\n" + "=" * 60)
        print("⚙️  应用配置")
        print("=" * 60)
        print(f"📊 数据库: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"🤖 AI 模型: {app.config['OPENAI_MODEL']}")
        print(f"🌡️  温度: {app.config['TEMPERATURE']}")
        print(f"💬 每会话最大消息数: {app.config['MAX_MESSAGES_PER_SESSION']}")
        print(f"🧠 默认上下文长度: {app.config['MAX_CONTEXT_FOR_AI']}")
        print(f"📏 上下文范围: {app.config['MIN_CONTEXT_LENGTH']}-{app.config['MAX_CONTEXT_LENGTH']}")
        print("=" * 60 + "\n")


# ========== 配置说明 ==========
"""
为什么分开 MAX_MESSAGES_PER_SESSION 和 MAX_CONTEXT_FOR_AI？

┌─────────────────────────────────────────────────────────────┐
│  MAX_MESSAGES_PER_SESSION = 50                              │
│  └─ 数据库存储 50 条消息                                      │
│     ├─ 用户可以查看完整聊天历史                                │
│     ├─ 支持导出对话记录                                        │
│     └─ 防止数据库无限增长                                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  MAX_CONTEXT_FOR_AI = 10 (默认值，可由用户调整 10-50)          │
│  └─ 只发送最近 10 条给 AI                                     │
│     ├─ 节省 Token（省钱！💰）                                  │
│     ├─ 提高响应速度（上下文越短，AI 越快）                      │
│     ├─ 避免超出模型的上下文限制                                 │
│     └─ AI 不需要知道所有历史，最近的对话就足够了                │
└─────────────────────────────────────────────────────────────┘

示例场景：

用户已发送 30 条消息：
  数据库保存：30 条（全部保留，用户可查看）
  发送给 AI：10 条（最近的 10 条，节省成本）

用户已发送 60 条消息：
  数据库保存：50 条（自动删除最旧的 10 条）
  发送给 AI：10 条（最近的 10 条）

用户调整记忆长度为 30 轮：
  数据库保存：仍然是 50 条
  发送给 AI：30 条（用户设置值）
"""