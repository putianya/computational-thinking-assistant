# -*- coding: utf-8 -*-
"""
大语言模型服务 - 支持流式输出和上下文管理
"""
from openai import OpenAI
from config import Config

class LLMService:
    def __init__(self):
        """初始化 OpenAI 客户端"""
        # ⭐ 针对特定 API 的请求头配置
        extra_headers = {}
        base_url_lower = Config.OPENAI_BASE_URL.lower()
        
        if 'githubcopilot' in base_url_lower or 'github' in base_url_lower:
            extra_headers = {
                "Editor-Version": "vscode/1.85.0",
                "Editor-Plugin-Version": "copilot/1.150.0",
                "User-Agent": "GithubCopilot/1.150.0"
            }
        
        self.client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url=Config.OPENAI_BASE_URL,
            default_headers=extra_headers if extra_headers else None,
            timeout=30.0,
            max_retries=2
        )
        self.model = Config.OPENAI_MODEL
        # 上下文存储
        self.conversation_history = {}
    
    def chat_stream(self, user_message, session_id=None):
        """
        ⭐ 流式对话生成器（完整错误处理版）
        """
        try:
            messages = self._build_messages(user_message, session_id)
            
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3,
                max_tokens=1000,
                stream=True,
                timeout=30.0
            )
            
            full_reply = ""
            
            # ⭐ 逐块返回内容（完整的安全检查）
            for chunk in stream:
                # 检查 chunk 是否有 choices 属性
                if not hasattr(chunk, 'choices'):
                    continue
                
                # 检查 choices 是否为空
                if not chunk.choices or len(chunk.choices) == 0:
                    continue
                
                # 安全获取第一个 choice
                choice = chunk.choices[0]
                
                # 检查是否有 delta
                if not hasattr(choice, 'delta'):
                    continue
                
                delta = choice.delta
                
                # 检查 delta 是否有 content
                if not hasattr(delta, 'content') or delta.content is None:
                    continue
                
                # ⭐ 到这里才是真正的内容
                content = delta.content
                full_reply += content
                yield content
            
            # 完成后保存历史
            if full_reply:
                self._save_history(session_id, user_message, full_reply)
            
        except Exception as e:
            error_msg = f"\n\n❌ 流式生成错误: {str(e)}"
            print(f"❌ ERROR in chat_stream: {error_msg}")
            import traceback
            traceback.print_exc()
            yield error_msg
    
    def _build_messages(self, user_message, session_id):
        """
        构建消息列表（包含系统提示词和历史上下文）
        """
        messages = [
            {"role": "system", "content": Config.SYSTEM_PROMPT}
        ]
        
        # 添加历史上下文
        if session_id and session_id in self.conversation_history:
            history = self.conversation_history[session_id]
            # 只保留最近N轮对话
            recent_history = history[-(Config.MAX_CONTEXT_MESSAGES * 2):]
            messages.extend(recent_history)
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    def _save_history(self, session_id, user_message, bot_reply):
        """
        保存对话历史
        """
        if not session_id:
            return
        
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        
        self.conversation_history[session_id].extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": bot_reply}
        ])
        
        # 限制历史长度
        max_pairs = Config.MAX_CONTEXT_MESSAGES
        if len(self.conversation_history[session_id]) > max_pairs * 2:
            self.conversation_history[session_id] = \
                self.conversation_history[session_id][-(max_pairs * 2):]
    
    def clear_history(self, session_id):
        """
        清除会话历史
        """
        if session_id in self.conversation_history:
            del self.conversation_history[session_id]
            return True
        return False
    
    def get_history_length(self, session_id):
        """
        获取历史消息数量
        """
        if session_id in self.conversation_history:
            return len(self.conversation_history[session_id]) // 2
        return 0