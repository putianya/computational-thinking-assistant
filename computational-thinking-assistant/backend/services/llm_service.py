# -*- coding: utf-8 -*-
"""
大语言模型服务 - 集成 RAG 知识检索
"""
from openai import OpenAI
from config import Config
from services.chat_service import ChatService
from services.vector_service import get_vector_service
from utils.question_classifier import classify_question


class LLMService:
    """
    LLM 服务类
    职责：
    1. 调用 OpenAI API
    2. 集成 RAG 知识检索
    3. 根据问题类型选择不同的提示词策略
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
        
        # ⭐ 初始化向量服务
        self.vector_service = get_vector_service()
    
    def chat_stream(self, user_message, session_id=None, max_context=None):
        """
        流式对话生成器（⭐ 支持保存 RAG 引用）
        
        Args:
            user_message: 用户消息
            session_id: 会话 ID（字符串）
            max_context: ⭐ 已废弃，不再使用
        
        Yields:
            str: AI 回复的文本块
        """
        try:
            # 1. 先保存用户消息到数据库
            if session_id:
                ChatService.save_message(session_id, 'user', user_message)
                print(f"💾 用户消息已保存: {user_message[:30]}...")
            
            # ⭐⭐⭐ 2. 构建消息（包含 RAG 检索）⭐⭐⭐
            # ⭐ 返回值改为元组：(messages, referenced_chunks)
            messages, referenced_chunks = self._build_messages(user_message, session_id)
            
            print(f"🧠 构建上下文: {len(messages)} 条消息")
            
            # 3. 调用 OpenAI API
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=Config.TEMPERATURE,
                max_tokens=Config.MAX_TOKENS,
                stream=True,
                timeout=30.0
            )
            
            full_reply = ""
            
            # 4. 逐块返回内容
            for chunk in stream:
                if not hasattr(chunk, 'choices') or not chunk.choices:
                    continue
                
                choice = chunk.choices[0]
                
                if not hasattr(choice, 'delta'):
                    continue
                
                delta = choice.delta
                
                if not hasattr(delta, 'content') or delta.content is None:
                    continue
                
                content = delta.content
                full_reply += content
                yield content
            
            # ⭐⭐⭐ 5. 流式结束后，保存 AI 回复（带引用）⭐⭐⭐
            if full_reply and session_id:
                # 提取知识块 ID
                referenced_chunk_ids = []
                
                if referenced_chunks:
                    for chunk in referenced_chunks:
                        chunk_id = chunk.get('id') or chunk.get('metadata', {}).get('id')
                        if chunk_id:
                            referenced_chunk_ids.append(chunk_id)
                
                # 保存消息（带引用信息）
                ChatService.save_message(
                    session_id=session_id,
                    role='assistant',
                    content=full_reply,
                    referenced_chunks=referenced_chunk_ids if referenced_chunk_ids else None  # ⭐ 传入引用
                )
                
                print(f"💾 AI 回复已保存（引用 {len(referenced_chunk_ids)} 个知识块）")
            
        except Exception as e:
            error_msg = f"\n\n❌ 流式生成错误: {str(e)}"
            print(f"❌ ERROR in chat_stream: {error_msg}")
            import traceback
            traceback.print_exc()
            yield error_msg
    
    def _build_messages(self, user_message, session_id):
        """
        构建发送给 AI 的消息列表（集成 RAG）（⭐ 返回引用信息）
        
        流程：
        1. 问题分类 → 确定检索策略
        2. 向量检索 → 查找相关知识
        3. 判断模式 → RAG 或 普通对话
        4. 构建消息 → 返回给 AI
        
        Args:
            user_message: 当前用户消息
            session_id: 会话 ID
        
        Returns:
            tuple: (messages, referenced_chunks)
                - messages: OpenAI API 格式的消息列表
                - referenced_chunks: 检索到的知识块列表（用于保存引用）
        """
        # ========== 步骤 1：问题分类 ==========
        print("\n" + "=" * 60)
        print("🔍 步骤 1：问题分类")
        print("=" * 60)
        
        classification = classify_question(user_message)
        question_type = classification.get('category') or classification.get('type', 'general')
        top_k = classification.get('top_k', 3)
        threshold = classification.get('threshold', 0.7)
        
        print(f"   问题类型: {question_type}")
        print(f"   置信度: {classification.get('confidence', 0):.2f}")
        print(f"   检索参数: top_k={top_k}, threshold={threshold}")
        
        # ========== 步骤 2：向量检索 ==========
        print("\n" + "=" * 60)
        print("🔍 步骤 2：向量检索")
        print("=" * 60)
        
        filtered_results = []
        
        try:
            # 调用向量检索
            results = self.vector_service.search(
                query=user_message,
                top_k=top_k
            )
            
            # 手动过滤低相似度结果
            filtered_results = [
                doc for doc in results 
                if doc.get('score', 0) >= threshold
            ]
            
            print(f"   检索到: {len(results)} 个结果")
            print(f"   过滤后: {len(filtered_results)} 个结果 (阈值 >= {threshold})")
            
            if filtered_results:
                print("\n   📄 相关知识预览:")
                for i, doc in enumerate(filtered_results[:2], 1):
                    print(f"      {i}. [{doc.get('score', 0):.3f}] {doc.get('text', '')[:50]}...")
        
        except Exception as e:
            print(f"   ⚠️ 检索失败: {e}")
            filtered_results = []
        
        # ========== 步骤 3：获取历史上下文 ==========
        print("\n" + "=" * 60)
        print("🔍 步骤 3：加载历史上下文")
        print("=" * 60)
        
        context = []
        if session_id:
            context = ChatService.get_context_for_ai(session_id, limit=None)
            print(f"   历史消息: {len(context)} 条")
        else:
            print("   历史消息: 无（新会话）")
        
        # ========== 步骤 4：判断使用哪种模式 ==========
        print("\n" + "=" * 60)
        print("🔍 步骤 4：选择对话模式")
        print("=" * 60)
        
        if filtered_results:
            # ✅ 使用 RAG 模式
            print("   ✅ 使用 RAG 模式（检索到相关知识）")
            messages = self._build_rag_messages(user_message, filtered_results, context)
        else:
            # ❌ 使用普通模式
            print("   ❌ 使用普通模式（未检索到相关知识）")
            messages = self._build_normal_messages(user_message, context)
        
        print("=" * 60 + "\n")
        
        # ⭐⭐⭐ 返回消息和引用信息 ⭐⭐⭐
        return messages, filtered_results
    
    def _build_rag_messages(self, user_message, knowledge_results, context):
        """
        构建 RAG 模式的消息列表
        
        格式：
        [
            system: RAG 系统提示词
            system: 【知识库内容】+ 相关知识
            ...历史对话...
            user: 用户问题
        ]
        
        Args:
            user_message: 用户问题
            knowledge_results: 检索到的知识
            context: 历史对话上下文
        
        Returns:
            list: 消息列表
        """
        # ⭐⭐⭐ 添加详细日志 ⭐⭐⭐
        print(f"\n{'=' * 60}")
        print(f"🔍 RAG 检索摘要")
        print(f"{'=' * 60}")
        print(f"📝 用户问题: {user_message[:50]}{'...' if len(user_message) > 50 else ''}")
        print(f"📚 检索结果: {len(knowledge_results)} 个知识块")
        
        if knowledge_results:
            print(f"\n💡 知识块详情:")
            for i, chunk in enumerate(knowledge_results, 1):
                score = chunk.get('score', 0)
                metadata = chunk.get('metadata', {})
                text = chunk.get('text', '')
                
                chapter = metadata.get('chapter', 'N/A')
                source = metadata.get('source', 'N/A')
                section = metadata.get('section', '')
                
                print(f"\n  📄 知识块 {i}:")
                print(f"     相似度: {score:.3f}")
                print(f"     来源: {source}")
                print(f"     章节: {chapter}")
                if section:
                    print(f"     小节: {section}")
                print(f"     内容: {text[:80]}{'...' if len(text) > 80 else ''}")
        
        print(f"\n📊 消息统计:")
        print(f"   - 系统提示词: 2 条（RAG 专用 + 知识库注入）")
        print(f"   - 历史对话: {len(context)} 条")
        print(f"   - 当前问题: 1 条")
        print(f"   - 总计: {2 + len(context) + 1} 条消息")
        print(f"{'=' * 60}\n")
        
        # ========== 构建消息列表 ==========
        messages = []
        
        # 1. 系统提示词（RAG 专用）
        messages.append({
            "role": "system",
            "content": Config.RAG_SYSTEM_PROMPT
        })
        
        # 2. 注入知识库内容（作为第二条系统消息）
        knowledge_context = self._format_knowledge(knowledge_results)
        
        messages.append({
            "role": "system",
            "content": f"""【知识库内容】

以下是从课程知识库中检索到的相关内容，请优先使用这些信息回答问题：

{knowledge_context}

---

请基于以上知识库内容回答学生的问题。如果知识库中没有相关信息，请明确告知学生。
"""
        })
        
        # 3. 历史对话上下文
        if context:
            messages.extend(context)
        
        # 4. 当前用户问题
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    def _build_normal_messages(self, user_message, context):
        """
        构建普通模式的消息列表
        
        格式：
        [
            system: 普通系统提示词
            ...历史对话...
            user: 用户问题
        ]
        
        Args:
            user_message: 用户问题
            context: 历史对话上下文
        
        Returns:
            list: 消息列表
        """
        # ⭐⭐⭐ 添加详细日志 ⭐⭐⭐
        print(f"\n{'=' * 60}")
        print(f"💬 普通对话模式")
        print(f"{'=' * 60}")
        print(f"📝 用户问题: {user_message[:50]}{'...' if len(user_message) > 50 else ''}")
        print(f"📊 消息统计:")
        print(f"   - 系统提示词: 1 条（普通模式）")
        print(f"   - 历史对话: {len(context)} 条")
        print(f"   - 当前问题: 1 条")
        print(f"   - 总计: {1 + len(context) + 1} 条消息")
        print(f"{'=' * 60}\n")
        
        # ========== 构建消息列表 ==========
        messages = []
        
        # 1. 系统提示词（普通模式）
        messages.append({
            "role": "system",
            "content": Config.SYSTEM_PROMPT
        })
        
        # 2. 历史对话上下文
        if context:
            messages.extend(context)
        
        # 3. 当前用户问题
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    def _format_knowledge(self, knowledge_results):
        """
        格式化知识库内容（优化版）
        
        格式示例：
        【参考资料 1】
        来源：test_pointer.md
        章节：什么是指针
        相似度：0.86
        内容：
        指针是 C 语言中的一种特殊变量类型...
        ----------------------------------------
        
        Args:
            knowledge_results: 检索结果列表
        
        Returns:
            str: 格式化后的知识文本
        """
        if not knowledge_results:
            return "（未找到相关知识）"
        
        formatted = []
        
        for i, doc in enumerate(knowledge_results, 1):
            score = doc.get('score', 0)
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})
            
            source = metadata.get('source', 'unknown')
            chapter = metadata.get('chapter', 'N/A')
            section = metadata.get('section', '')
            
            # ⭐ 优化：更清晰的格式
            knowledge_block = f"""【参考资料 {i}】
来源：{source}
章节：{chapter}"""
            
            # 如果有小节信息，添加上去
            if section:
                knowledge_block += f"\n小节：{section}"
            
            knowledge_block += f"""
相似度：{score:.2f}
内容：
{text}
{'-' * 40}
"""
            
            formatted.append(knowledge_block)
        
        return "\n".join(formatted)