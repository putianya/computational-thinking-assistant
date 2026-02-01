# -*- coding: utf-8 -*-
"""
大语言模型服务 - 集成 RAG 知识检索
"""
import time
import traceback
from openai import OpenAI
from config import Config
from services.chat_service import ChatService
from services.vector_service import get_vector_service
from utils.question_classifier import classify_question
from models.knowledge_chunk import KnowledgeChunk

class LLMService:
    """LLM 服务类"""
    
    def __init__(self):
        """初始化"""
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
        self.vector_service = get_vector_service()
    
    def chat_stream(self, user_message, session_id=None, max_context=None):
        """流式对话生成器"""
        
        # ⭐⭐⭐ 记录总开始时间 ⭐⭐⭐
        total_start_time = time.time()
        
        try:
            # 1. 保存用户消息（异步会更好，但先同步处理）
            save_start = time.time()
            if session_id:
                ChatService.save_message(session_id, 'user', user_message)
            print(f"💾 保存用户消息耗时: {time.time() - save_start:.2f}秒")
            
            # 2. 构建消息
            build_start = time.time()
            messages, referenced_chunks = self._build_messages(user_message, session_id)
            print(f"🔧 构建消息耗时: {time.time() - build_start:.2f}秒")
            
            if messages is None:
                print("❌ 构建消息失败")
                yield "抱歉，系统错误，请重试。"
                return
            
            print(f"🧠 构建上下文: {len(messages)} 条消息")
            
            # 3. 动态 max_tokens（快速判断，不需要再次分类）
            # ⭐⭐⭐ 优化：使用简单规则而不是重复分类 ⭐⭐⭐
            msg_lower = user_message.lower().strip()
            
            # 简单的闲聊检测
            chat_keywords = ['你好', '谢谢', '再见', '天气', '你是谁', '好的', '嗯', 'ok', 'hi', 'hello']
            is_simple_chat = any(kw in msg_lower for kw in chat_keywords) and len(user_message) < 20
            
            if is_simple_chat:
                max_tokens = 300  # 闲聊用更少的 tokens
                print(f"📏 简单闲聊模式: max_tokens={max_tokens}")
            else:
                max_tokens = Config.MAX_TOKENS
                print(f"📏 标准模式: max_tokens={max_tokens}")
            
            # ⭐⭐⭐ 4. 记录预处理总耗时 ⭐⭐⭐
            preprocess_time = time.time() - total_start_time
            print(f"⏱️ 预处理总耗时: {preprocess_time:.2f}秒")
            
            # 5. 调用 OpenAI API
            api_start_time = time.time()
            
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=Config.TEMPERATURE,
                max_tokens=max_tokens,
                stream=True,
                timeout=30.0
            )
            
            full_response = ""
            first_chunk = True
            
            # 6. 流式生成
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    
                    if hasattr(delta, 'content') and delta.content:
                        if first_chunk:
                            api_first_byte = time.time() - api_start_time
                            total_first_byte = time.time() - total_start_time
                            print(f"⚡ API 首字节延迟: {api_first_byte:.2f}秒")
                            print(f"⚡ 总首字节延迟: {total_first_byte:.2f}秒 (预处理: {preprocess_time:.2f}秒)")
                            first_chunk = False
                        
                        content = delta.content
                        full_response += content
                        yield content
            
            # 7. 保存 AI 回复
            if session_id and full_response:
                ChatService.save_message(
                    session_id, 
                    'assistant', 
                    full_response,
                    referenced_chunks=referenced_chunks
                )
            
            total_time = time.time() - total_start_time
            print(f"✅ 流式输出完成，总耗时: {total_time:.2f}秒")
            
        except Exception as e:
            print(f"❌ 流式生成错误: {e}")
            traceback.print_exc()
            yield f"\n\n抱歉，发生错误：{str(e)}"
    
    def _build_messages(self, user_message, session_id):
        """构建消息列表"""
        try:
            # ⭐⭐⭐ 优化：减少日志输出，加快处理 ⭐⭐⭐
            
            # 检测"继续"指令
            continue_keywords = ['继续', 'continue', '接着写', '接下去', '往下说', '还有呢', '然后呢']
            is_continue_request = user_message.strip().lower() in continue_keywords
            
            if is_continue_request:
                print("🔄 检测到续写请求")
                context = []
                if session_id:
                    context = ChatService.get_context_for_ai(session_id, limit=None)
                messages = self._build_continue_messages(user_message, context)
                return messages, []
            
            # 问题分类
            classify_start = time.time()
            classification = classify_question(user_message)
            question_type = classification.get('category', 'general')
            needs_rag = classification.get('needs_rag', True)
            skip_reason = classification.get('skip_reason', '')
            print(f"🔍 分类耗时: {time.time() - classify_start:.2f}秒, 类型: {question_type}, RAG: {needs_rag}")
            
            # 向量检索
            filtered_results = []
            
            if needs_rag:
                search_start = time.time()
                top_k = classification.get('top_k', 3)
                threshold = classification.get('threshold', Config.SIMILARITY_THRESHOLD)
                
                try:
                    results = self.vector_service.search(
                        query=user_message, 
                        top_k=top_k
                    )
                    
                    # 过滤低相似度结果
                    filtered_results = [
                        doc for doc in results 
                        if doc.get('score', 0) >= threshold
                    ]
                    
                    # ⭐⭐⭐ 新增：累加热度 ⭐⭐⭐
                    for result in filtered_results:
                        vector_id = result.get('id')
                        if vector_id:
                            chunk = KnowledgeChunk.get_by_vector_id(vector_id)
                            if chunk:
                                chunk.increment_retrieved()
                                print(f"📈 知识块 {chunk.id} 热度 +1 (当前: {chunk.retrieved_count})")
                    
                except Exception as e:
                    print(f"⚠️ 检索失败: {e}")
            else:
                print(f"⏭️ 跳过检索: {skip_reason}")
            
            # 获取历史上下文
            context_start = time.time()
            context = []
            if session_id:
                context = ChatService.get_context_for_ai(session_id, limit=None)
            print(f"📚 上下文耗时: {time.time() - context_start:.2f}秒, 消息数: {len(context)}")
            
            # 构建消息
            if filtered_results:
                print(f"✅ RAG 模式 (知识块: {len(filtered_results)})")
                messages = self._build_rag_messages(user_message, filtered_results, context)
                referenced_chunks = filtered_results
            else:
                print(f"💬 普通模式")
                messages = self._build_normal_messages(user_message, context)
                referenced_chunks = []
            
            return messages, referenced_chunks
            
        except Exception as e:
            print(f"❌ 构建消息失败: {e}")
            traceback.print_exc()
            return None, []
    
    def _build_rag_messages(self, user_message, knowledge_results, context):
        """构建 RAG 模式消息"""
        messages = []
        
        # 1. RAG 系统提示词
        messages.append({
            "role": "system",
            "content": Config.RAG_SYSTEM_PROMPT
        })
        
        # 2. 注入知识库内容
        knowledge_context = self._format_knowledge(knowledge_results)
        messages.append({
            "role": "system",
            "content": f"【知识库内容】\n{knowledge_context}\n---\n请基于以上知识库内容回答学生的问题。"
        })
        
        # 3. 历史对话
        if context:
            messages.extend(context)
        
        # 4. 当前问题
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    def _build_normal_messages(self, user_message, context):
        """构建普通模式消息"""
        messages = []
        
        # 系统提示词
        messages.append({
            "role": "system",
            "content": Config.SYSTEM_PROMPT
        })
        
        # 历史对话
        if context:
            messages.extend(context)
        
        # 当前问题
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    def _build_continue_messages(self, user_message, context):
        """构建续写模式消息"""
        if not context or len(context) < 2:
            return [
                {"role": "system", "content": Config.SYSTEM_PROMPT},
                {"role": "user", "content": "请先提出一个问题，才能使用'继续'功能。"}
            ]
        
        messages = []
        messages.append({"role": "system", "content": Config.SYSTEM_PROMPT})
        messages.append({"role": "system", "content": "【续写模式】用户要求继续上一个回答。请直接从上次中断的地方继续，不要重复。"})
        messages.extend(context)
        messages.append({"role": "user", "content": "请继续"})
        
        return messages
    
    def _format_knowledge(self, knowledge_results):
        """格式化知识库内容"""
        if not knowledge_results:
            return "（未找到相关知识）"
        
        formatted = []
        for i, doc in enumerate(knowledge_results, 1):
            score = doc.get('score', 0)
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})
            
            formatted.append(f"【参考资料 {i}】\n来源：{metadata.get('source', 'N/A')}\n内容：{text[:500]}...")
        
        return "\n".join(formatted)

    # 批量更新热度（性能更好）
    def batch_increment_retrieved(self, chunk_ids):
        """批量更新热度"""
        if chunk_ids:
            KnowledgeChunk.batch_increment_retrieved(chunk_ids)