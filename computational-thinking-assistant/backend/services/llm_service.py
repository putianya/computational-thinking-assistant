# -*- coding: utf-8 -*-
"""
大语言模型服务 - 只负责调用 AI（不管理上下文）
"""
from openai import OpenAI
from config import Config
from services.chat_service import ChatService


class LLMService:
    """
    LLM 服务类
    职责：只负责调用 OpenAI API
    不负责：上下文管理、消息存储（由 ChatService 负责）
    """
    
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
        
        # ⭐ 删除：不再在内存中管理上下文
        # self.conversation_history = {}  # ❌ 已删除
    
    def chat_stream(self, user_message, session_id=None, max_context=None):
        """
        流式对话生成器
        
        Args:
            user_message: 用户消息
            session_id: 会话 ID（字符串）
            max_context: 上下文长度（默认使用配置值）
        
        Yields:
            str: AI 回复的文本块
        
        改进：
        1. ✅ 从数据库获取上下文（而非内存）
        2. ✅ 调用 ChatService 保存消息
        3. ✅ 支持可变上下文长度
        """
        try:
            # ⭐ 1. 先保存用户消息到数据库
            if session_id:
                ChatService.save_message(session_id, 'user', user_message)
                print(f"💾 用户消息已保存: {user_message[:30]}...")
            
            # ⭐ 2. 从数据库获取上下文（而非内存）
            context_limit = max_context or Config.MAX_CONTEXT_FOR_AI
            messages = self._build_messages(user_message, session_id, context_limit)
            
            print(f"🧠 构建上下文: {len(messages)} 条消息 (限制: {context_limit} 轮)")
            
            # ⭐ 3. 调用 OpenAI API
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS,
                stream=True,
                timeout=30.0
            )
            
            full_reply = ""
            
            # ⭐ 4. 逐块返回内容
            for chunk in stream:
                # 安全检查
                if not hasattr(chunk, 'choices') or not chunk.choices:
                    continue
                
                choice = chunk.choices[0]
                
                if not hasattr(choice, 'delta'):
                    continue
                
                delta = choice.delta
                
                if not hasattr(delta, 'content') or delta.content is None:
                    continue
                
                # ⭐ 返回内容块
                content = delta.content
                full_reply += content
                yield content
            
            # ⭐ 5. 流式结束后，保存 AI 回复到数据库
            if full_reply and session_id:
                ChatService.save_message(session_id, 'assistant', full_reply)
                print(f"💾 AI 回复已保存: {full_reply[:30]}... (共 {len(full_reply)} 字符)")
            
        except Exception as e:
            error_msg = f"\n\n❌ 流式生成错误: {str(e)}"
            print(f"❌ ERROR in chat_stream: {error_msg}")
            import traceback
            traceback.print_exc()
            yield error_msg
    
    def _build_messages(self, user_message, session_id, max_context):
        """
        构建发送给 AI 的消息列表
        
        Args:
            user_message: 当前用户消息
            session_id: 会话 ID
            max_context: 上下文长度（轮数）
        
        Returns:
            list: OpenAI API 格式的消息列表
            [
                {"role": "system", "content": "..."},
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."},
                ...
            ]
        
        改进：
        ✅ 从数据库获取上下文（而非内存）
        ✅ 不包含当前用户消息（已在数据库中保存）
        """
        messages = [
            {"role": "system", "content": Config.SYSTEM_PROMPT}
        ]
        
        # ⭐ 从数据库获取历史上下文（而非 self.conversation_history）
        if session_id:
            # 获取最近 N 条消息（不包含刚保存的用户消息）
            context = ChatService.get_context_for_ai(session_id, limit=max_context)
            
            if context:
                messages.extend(context)
                print(f"📜 加载历史上下文: {len(context)} 条消息")
        
        # ⭐ 注意：当前用户消息已在 chat_stream 开头保存到数据库
        # 但 OpenAI API 仍需要包含它
        messages.append({"role": "user", "content": user_message})
        
        return messages
    
    # ⭐⭐⭐ 删除以下方法（已移到 ChatService）⭐⭐⭐
    
    # ❌ 删除：_save_history()
    # def _save_history(self, session_id, user_message, bot_reply):
    #     """不再需要：由 ChatService.save_message() 替代"""
    #     pass
    
    # ❌ 删除：clear_history()
    # def clear_history(self, session_id):
    #     """不再需要：由 ChatService.clear_messages() 替代"""
    #     pass
    
    # ❌ 删除：get_history_length()
    # def get_history_length(self, session_id):
    #     """不再需要：由 ChatService.get_session_messages() 替代"""
    #     pass