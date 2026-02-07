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
    
    # ⭐⭐⭐ RAG 置信度阈值配置 ⭐⭐⭐
    RAG_HIGH_CONFIDENCE = 0.80    # 高置信度阈值
    RAG_MEDIUM_CONFIDENCE = 0.60  # 中置信度阈值
    RAG_MIN_RESULTS = 1           # 最少需要的结果数
    
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
        
        total_start_time = time.time()
        
        try:
            # 1. 保存用户消息
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
            
            # 3. 动态 max_tokens
            msg_lower = user_message.lower().strip()
            chat_keywords = ['你好', '谢谢', '再见', '天气', '你是谁', '好的', '嗯', 'ok', 'hi', 'hello']
            is_simple_chat = any(kw in msg_lower for kw in chat_keywords) and len(user_message) < 20
            
            if is_simple_chat:
                max_tokens = 300
                print(f"📏 简单闲聊模式: max_tokens={max_tokens}")
            else:
                max_tokens = Config.MAX_TOKENS
                print(f"📏 标准模式: max_tokens={max_tokens}")
            
            preprocess_time = time.time() - total_start_time
            print(f"⏱️ 预处理总耗时: {preprocess_time:.2f}秒")
            
            # 4. 调用 OpenAI API
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
            
            # 5. 流式生成
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
            
            # 6. 保存 AI 回复
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
        """
        构建消息列表（智能降级版）
        """
        print("\n" + "=" * 60)
        print(f"🔍 【消息构建】步骤")
        print("=" * 60)
        
        try:
            # ========== 1. 检测"继续"指令 ==========
            continue_keywords = ['继续', 'continue', '接着写', '接下去', '往下说', '还有呢', '然后呢']
            is_continue_request = user_message.strip().lower() in continue_keywords
            
            if is_continue_request:
                print("🔄 检测到续写请求")
                context = []
                if session_id:
                    context = ChatService.get_context_for_ai(session_id)
                return self._build_continue_messages(user_message, context)
            
            # ========== 2. 问题分类 ==========
            classify_start = time.time()
            classification = classify_question(user_message)
            question_type = classification.get('category', 'general')
            needs_rag = classification.get('needs_rag', True)
            skip_reason = classification.get('skip_reason', '')
            
            print(f"🔍 分类结果: 类型={question_type}, 需要RAG={needs_rag}")
            if skip_reason:
                print(f"   跳过原因: {skip_reason}")
            
            # ========== 3. 向量检索（如果需要）==========
            search_results = []
            rag_mode = 'none'
            max_score = 0.0
            referenced_chunks = []  # ⭐⭐⭐ 记录引用的知识块 ID ⭐⭐⭐
            
            if needs_rag:
                search_start = time.time()
                top_k = classification.get('top_k', 5)
                threshold = classification.get('threshold', self.RAG_MEDIUM_CONFIDENCE)
                
                # 执行检索
                raw_results = self.vector_service.search(
                    query=user_message,
                    top_k=top_k
                )
                
                print(f"🔍 检索耗时: {time.time() - search_start:.2f}s, 原始结果: {len(raw_results)}条")
                
                # ⭐⭐⭐ 分析检索质量并提取 chunk_id ⭐⭐⭐
                if raw_results:
                    max_score = max(doc.get('score', 0) for doc in raw_results)
                    print(f"   检索到 {len(raw_results)} 个结果")
                    print(f"   最高相似度: {max_score:.3f}")
                    
                    # ⭐⭐⭐ 提取有效的 chunk_id ⭐⭐⭐
                    chunk_ids_to_update = []
                    for doc in raw_results:
                        metadata = doc.get('metadata', {})
                        chunk_id = metadata.get('chunk_id')
                        
                        if chunk_id:
                            chunk_ids_to_update.append(chunk_id)
                            print(f"   ✅ 找到知识块 chunk_id={chunk_id}, score={doc.get('score', 0):.3f}")
                        else:
                            print(f"   ⚠️ 知识块缺少 chunk_id: vector_id={doc.get('id')}")
                    
                    # ⭐⭐⭐ 批量更新引用计数 ⭐⭐⭐
                    if chunk_ids_to_update:
                        try:
                            KnowledgeChunk.batch_increment_retrieved(chunk_ids_to_update)
                            print(f"   📊 已更新 {len(chunk_ids_to_update)} 个知识块的引用计数")
                            referenced_chunks = chunk_ids_to_update  # 记录下来
                        except Exception as e:
                            print(f"   ⚠️ 更新引用计数失败: {e}")
                    else:
                        print(f"   ⚠️ 未找到有效的 chunk_id，无法更新引用计数")
                    
                    # 根据最高分确定 RAG 模式
                    if max_score >= self.RAG_HIGH_CONFIDENCE:
                        rag_mode = 'high'
                        search_results = [
                            doc for doc in raw_results 
                            if doc.get('score', 0) >= self.RAG_MEDIUM_CONFIDENCE
                        ]
                        print(f"✅ 高置信度模式: 最高分={max_score:.3f}, 有效结果={len(search_results)}条")
                        
                    elif max_score >= self.RAG_MEDIUM_CONFIDENCE:
                        rag_mode = 'medium'
                        search_results = [
                            doc for doc in raw_results 
                            if doc.get('score', 0) >= self.RAG_MEDIUM_CONFIDENCE
                        ]
                        print(f"⚠️ 中置信度模式: 最高分={max_score:.3f}, 有效结果={len(search_results)}条")
                        
                    else:
                        rag_mode = 'low'
                        search_results = []
                        print(f"❌ 低置信度: 最高分={max_score:.3f}, 不使用知识库")
                else:
                    rag_mode = 'none'
                    print("❌ 未检索到任何结果")
            else:
                print(f"⏭️ 跳过RAG检索: {skip_reason}")
            
            # ========== 4. 获取历史上下文 ==========
            context_start = time.time()
            context = []
            if session_id:
                context = ChatService.get_context_for_ai(session_id)
            print(f"📚 上下文: {len(context)}条消息")
            
            # ========== 5. 根据 RAG 模式构建消息 ==========
            if rag_mode == 'high':
                messages = self._build_high_confidence_rag_messages(
                    user_message, search_results, context, max_score
                )
                print("📝 使用【高置信度RAG】模式")
                
            elif rag_mode == 'medium':
                messages = self._build_medium_confidence_rag_messages(
                    user_message, search_results, context, max_score
                )
                print("📝 使用【中置信度RAG】模式")
                
            else:
                messages = self._build_fallback_messages(
                    user_message, context, needs_rag, max_score
                )
                print("📝 使用【普通对话】模式")
            
            return messages, referenced_chunks
            
        except Exception as e:
            print(f"❌ 构建消息失败: {e}")
            import traceback
            traceback.print_exc()
            return None, []
    
    # ⭐⭐⭐ 高置信度 RAG 消息构建 ⭐⭐⭐
    def _build_high_confidence_rag_messages(self, user_message, knowledge_results, context, max_score):
        """构建高置信度 RAG 消息"""
        messages = []
        
        high_confidence_prompt = f'''{Config.RAG_SYSTEM_PROMPT}

【重要提示】
我已从课程知识库中找到与学生问题高度相关的内容（相似度: {max_score:.1%}）。

请严格遵守以下规则：
1. **必须优先使用**下方知识库内容回答问题
2. **必须使用【参考资料X】格式标注引用**
3. 如果知识库内容与问题完全匹配，直接引用不要改写
4. 如果需要补充说明，明确区分"知识库内容"和"补充说明"
5. 不要编造知识库中没有的内容
'''
        messages.append({
            "role": "system",
            "content": high_confidence_prompt
        })
        
        knowledge_context = self._format_knowledge_detailed(knowledge_results)
        messages.append({
            "role": "system",
            "content": f"【课程知识库内容】\n{knowledge_context}"
        })
        
        if context:
            messages.extend(context)
        
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    # ⭐⭐⭐ 中置信度 RAG 消息构建 ⭐⭐⭐
    def _build_medium_confidence_rag_messages(self, user_message, knowledge_results, context, max_score):
        """构建中置信度 RAG 消息"""
        messages = []
        
        medium_confidence_prompt = f'''{Config.RAG_SYSTEM_PROMPT}

【参考提示】
我找到了一些可能相关的知识库内容（最高相似度: {max_score:.1%}），供你参考。

请注意：
1. 这些内容**可能相关但不完全匹配**学生的问题
2. 你可以选择性使用，如果使用请标注【参考资料X】
3. 可以结合你的知识进行补充和扩展
4. 如果知识库内容不够准确，以你的专业判断为准
5. 回答时说明哪些是知识库内容，哪些是你的补充
'''
        messages.append({
            "role": "system",
            "content": medium_confidence_prompt
        })
        
        knowledge_context = self._format_knowledge_detailed(knowledge_results)
        messages.append({
            "role": "system",
            "content": f"【可参考的知识库内容】\n{knowledge_context}\n\n注：以上内容仅供参考，请根据问题实际需要选择使用。"
        })
        
        if context:
            messages.extend(context)
        
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    # ⭐⭐⭐ 低置信度/普通模式消息构建 ⭐⭐⭐
    def _build_fallback_messages(self, user_message, context, tried_rag, max_score):
        """构建普通模式消息"""
        messages = []
        
        if tried_rag and max_score > 0:
            fallback_prompt = f'''{Config.SYSTEM_PROMPT}

【提示】
我在课程知识库中没有找到与学生问题高度相关的内容（最高相似度仅为 {max_score:.1%}）。

请注意：
1. 使用你的专业知识回答问题
2. 在回答开头简要说明："关于这个问题，课程知识库中暂无相关内容，我将根据C语言/数据结构的通用知识来回答。"
3. 如果问题超出计算思维课程范围，礼貌告知学生
4. 鼓励学生参考教材或咨询老师获取更权威的答案
'''
        elif tried_rag:
            fallback_prompt = f'''{Config.SYSTEM_PROMPT}

【提示】
课程知识库中没有找到与此问题相关的内容。

请注意：
1. 使用你的专业知识回答
2. 在回答开头说明："这个问题在课程知识库中暂无收录，我来为你解答。"
3. 保持计算思维课程助教的角色定位
'''
        else:
            fallback_prompt = Config.SYSTEM_PROMPT
        
        messages.append({
            "role": "system",
            "content": fallback_prompt
        })
        
        if context:
            messages.extend(context)
        
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    # ⭐⭐⭐ 详细格式化知识库内容 ⭐⭐⭐
    def _format_knowledge_detailed(self, knowledge_results):
        """详细格式化知识库内容"""
        if not knowledge_results:
            return "（未找到相关知识）"
        
        formatted = []
        for i, doc in enumerate(knowledge_results, 1):
            score = doc.get('score', 0)
            text = doc.get('text', '')
            metadata = doc.get('metadata', {})
            
            source = metadata.get('source', '未知来源')
            chapter = metadata.get('chapter', '')
            chunk_id = metadata.get('chunk_id', 'N/A')
            
            if score >= 0.85:
                confidence_tag = "⭐高度相关"
            elif score >= 0.75:
                confidence_tag = "相关"
            else:
                confidence_tag = "可能相关"
            
            formatted.append(
                f"【参考资料 {i}】[{confidence_tag}]\n"
                f"来源: {source}\n"
                f"章节: {chapter}\n"
                f"相似度: {score:.1%}\n"
                f"知识块ID: {chunk_id}\n"
                f"内容:\n{text}\n"
                f"{'─' * 40}"
            )
        
        return "\n\n".join(formatted)
    
    # ⭐⭐⭐ 处理"继续"指令的消息构建 ⭐⭐⭐
    def _build_continue_messages(self, user_message, context):
        """构建"继续"指令的消息列表"""
        messages = []
        
        continue_prompt = f'''{Config.SYSTEM_PROMPT}

【续写模式】
学生请求你继续上一次的回答。请：
1. 延续上一次回答的内容和风格
2. 保持话题连贯性
3. 如果上次回答已经完整，告知学生
4. 不要重复已说过的内容
'''
        messages.append({
            "role": "system",
            "content": continue_prompt
        })
        
        if context:
            for msg in context:
                messages.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
        
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        print(f"📝 构建续写消息: {len(messages)} 条（包含 {len(context)} 条历史）")
        
        return messages, []  # 返回 (messages, referenced_chunks)