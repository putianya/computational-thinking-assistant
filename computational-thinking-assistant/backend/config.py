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
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', '')
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', '')
    OPENAI_TEMPERATURE = 0.7  # 回答的随机性（0-1）
    OPENAI_MAX_TOKENS = 1000  # 最大回复长度
    
    # ⭐ 新增：流式输出配置
    ENABLE_STREAMING = True
    STREAM_CHUNK_SIZE = 50  # 每次发送的字符数

    # ⭐ 新增：上下文配置
    MAX_CONTEXT_MESSAGES = 10  # 保留最近10轮对话
    CONTEXT_WINDOW = 4000  # token限制

    # ========== 系统配置 ==========
    SYSTEM_PROMPT = """你是一位专业的C语言和计算思维课程助教。
你的任务是：
1. 解答C语言编程问题
2. 分析代码错误并提供修改建议
3. 讲解数据结构和算法
4. 帮助学生培养计算思维

请用清晰、友好的方式回答，适当使用代码示例。"""
    
    # ========== 数据库配置（后续使用）==========
    DATABASE_PATH = 'data/app.db'