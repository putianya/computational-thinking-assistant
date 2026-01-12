# 类的定义
# 环境变量读取
# 配置分离（开发/生产环境）

# config.py
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class Config:
    """应用配置类"""
    
    # ========== Flask 配置 ==========
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
    DEBUG = True
    HOST = '0.0.0.0'
    PORT = 5000
    
    # ========== OpenAI 配置 ==========
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o')
    OPENAI_TEMPERATURE = 0.7  # 回答的随机性（0-1）
    OPENAI_MAX_TOKENS = 1000  # 最大回复长度
    
    # ========== 系统配置 ==========
    SYSTEM_PROMPT = """你是一个专业的计算思维课程助手，擅长：
1. 解答 C 语言编程问题
2. 分析代码错误并提供调试建议
3. 讲解数据结构和算法
4. 用简单易懂的方式解释复杂概念

请用中文回答，语气友好专业。"""
    
    # ========== 数据库配置（后续使用）==========
    DATABASE_PATH = 'data/app.db'