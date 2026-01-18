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
    
    # ========== 数据库配置 ⭐⭐⭐ ==========
    # SQLite 数据库路径
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f'sqlite:///{BASE_DIR}/data/app.db'  # ⭐ 默认使用 SQLite
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG  # 开发模式下打印 SQL 语句
    
    # ========== OpenAI API 配置 ==========
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    
    # ========== 聊天功能配置 ==========
    ENABLE_STREAMING = os.getenv('ENABLE_STREAMING', 'True').lower() == 'true'
    MAX_CONTEXT_MESSAGES = int(os.getenv('MAX_CONTEXT_MESSAGES', 10))
    TEMPERATURE = float(os.getenv('TEMPERATURE', 0.7))
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', 2000))
    
    # ========== 系统提示词 ==========
    SYSTEM_PROMPT = """你是一位专业的计算思维课程助教，擅长：
1. 帮助学生理解抽象、分解、模式识别、算法设计等计算思维核心概念
2. 引导学生分析问题、设计解决方案
3. 提供编程学习建议和代码示例
4. 解答课程相关疑问

请用简洁、易懂的语言回答问题，必要时提供示例代码。"""
    
    # ========== JWT 配置 ==========
    JWT_SECRET_KEY = SECRET_KEY  # 使用相同的密钥
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = 24
    
    @staticmethod
    def init_app(app):
        """初始化应用配置"""
        # 确保数据目录存在
        data_dir = BASE_DIR / 'data'
        data_dir.mkdir(exist_ok=True)
        print(f"✅ 数据目录: {data_dir}")