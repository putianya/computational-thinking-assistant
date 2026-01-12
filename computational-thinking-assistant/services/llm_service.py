"""
LLM 服务 - 大语言模型调用服务
职责: 封装 OpenAI API 调用逻辑
相当于 Qt 的业务逻辑类
"""
from openai import OpenAI
from config import Config
from typing import Optional

class LLMService:
    """大语言模型服务"""
    
    _instance = None  # 单例模式
    
    def __new__(cls):
        """单例模式: 确保只创建一个实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化 OpenAI 客户端"""
        if self._initialized:
            return
        
        if not Config.OPENAI_API_KEY:
            raise ValueError("未配置 OpenAI API 密钥")
        
        self.client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url="https://models.inference.ai.azure.com"
        )
        
        self._initialized = True
        print("✅ LLM 服务初始化成功")
    
    def chat(self, user_message: str, system_prompt: Optional[str] = None) -> str:
        """
        发送消息到 AI
        
        Args:
            user_message: 用户消息
            system_prompt: 系统提示词（可选）
            
        Returns:
            str: AI 回复内容
            
        Raises:
            ValueError: 如果消息为空
            Exception: API 调用失败
        """
        if not user_message or not user_message.strip():
            raise ValueError("消息不能为空")
        
        # 使用默认系统提示词
        if system_prompt is None:
            system_prompt = Config.SYSTEM_PROMPT
        
        try:
            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=Config.OPENAI_TEMPERATURE,
                max_tokens=Config.OPENAI_MAX_TOKENS
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ LLM 服务调用失败: {str(e)}")
            raise
    
    def test_connection(self) -> bool:
        """
        测试 API 连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            response = self.chat("测试连接")
            return bool(response)
        except:
            return False
    
    @staticmethod
    def is_configured() -> bool:
        """检查是否已配置 API 密钥"""
        return bool(Config.OPENAI_API_KEY)