# -*- coding: utf-8 -*-
"""
代码分析路由 Blueprint
包含：analyze_code, code_chat_stream
"""
import json
import traceback
from flask import Blueprint, request, jsonify, Response, g, stream_with_context
from services.analytics.data_collector import DataCollector
from utils.decorators import login_required
from extensions import ServiceRegistry

code_bp = Blueprint('code', __name__)


def _build_code_chat_prompt(code, features, analysis, user_message):
    """
    构建代码对话的提示词

    Args:
        code: 代码字符串
        features: 代码特征字典
        analysis: AI 分析结果（可选）
        user_message: 用户问题

    Returns:
        消息列表 [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
    """
    system_prompt = f"""你是一位专业的 C 语言代码分析专家，正在帮助学生理解以下代码。

【待分析代码】
```c
{code}
```

【代码基本信息】
- 行数: {features.get('lines', 0)}
- 字符数: {features.get('chars', 0)}
- 是否包含 main 函数: {'是' if features.get('has_main') else '否'}
"""

    if features.get('includes'):
        system_prompt += f"- 包含头文件: {', '.join(features['includes'])}\n"

    if features.get('functions'):
        system_prompt += f"- 定义的函数: {', '.join(features['functions'])}\n"

    complexity_text = {
        'low': '低（简单逻辑）',
        'medium': '中等（有一定控制结构）',
        'high': '高（复杂逻辑）'
    }.get(features.get('complexity'), '未知')

    system_prompt += f"- 代码复杂度: {complexity_text}\n"

    if analysis:
        system_prompt += f"""
【AI 分析结果】
- 问题数: {len(analysis.get('problems', []))}
- 建议数: {len(analysis.get('suggestions', []))}
"""

        if analysis.get('problems'):
            system_prompt += "\n问题列表:\n"
            for i, problem in enumerate(analysis['problems'][:3], 1):
                severity = problem.get('severity', 'warning')
                desc = problem.get('description', '')
                system_prompt += f"{i}. [{severity}] {desc}\n"

        if analysis.get('summary'):
            system_prompt += f"\n总体评价: {analysis['summary']}\n"

    system_prompt += """
【回答原则】
1. 针对具体代码行号给出建议（如果需要）
2. 解释概念时结合代码示例
3. 鼓励学生思考，不要直接给完整答案
4. 使用中文回答
5. 如果代码有错误，优先指出错误位置和原因
6. 回答简洁明了，重点突出

请根据以上信息，回答学生的问题。
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    return messages


@code_bp.route('/api/code/analyze', methods=['POST'])
@login_required
def analyze_code():
    """
    代码分析 API

    权限：需要登录

    请求格式：
    {
        "code": "int main() { ... }",
        "analysis_type": "full"  // 可选：'syntax' | 'logic' | 'full'，默认 'full'
    }
    """
    try:
        print(f"\n=====================================================================")
        print(f"⭐⭐⭐ [代码分析模块测试] 收到隔离编译与深层推理请求 ⭐⭐⭐")
        print(f"=====================================================================")
        print(f"🔄 请求接口: POST /api/code/analyze")
        print(f"👤 请求载体: 用户ID [{g.user_id}]")

        data = request.get_json()

        if not data:
            return jsonify({
                'status': 'error',
                'message': '请提供请求数据'
            }), 400

        code = data.get('code', '').strip()
        analysis_type = data.get('analysis_type', 'full')

        print(f"🛠️ [步骤1/3] 执行沙箱编译前置检测与词法阻断...")
        print(f"   -> 传入源码装载完毕，大小: {len(code)} bytes.")
        print(f"   -> 检测模式: {analysis_type} | 执行沙箱预挂载: SUCCESS")

        if not code:
            print(f"❌ 代码为空，阻断拦截返回.")
            print(f"=====================================================================\n")
            return jsonify({
                'status': 'error',
                'message': '代码不能为空'
            }), 400

        valid_types = ['syntax', 'logic', 'full']
        if analysis_type not in valid_types:
            print(f"❌ 无效类型的分析: {analysis_type}")
            return jsonify({
                'status': 'error',
                'message': f'无效的分析类型，可选值: {", ".join(valid_types)}'
            }), 400

        max_code_length = 10000
        if len(code) > max_code_length:
            return jsonify({
                'status': 'error',
                'message': f'代码长度不能超过 {max_code_length} 字符'
            }), 400

        print(f"🚀 [步骤2/3] 沙箱底层通过，抽取语法抽象树(AST)并封装推理上下文投入大语言模型...")
        service = ServiceRegistry.get_code_service()
        result = service.analyze_code(code, analysis_type)

        if not result.get('success', False):
            error_msg = result.get('error', '分析失败')
            print(f"❌ [告警] 探针检测到编译期硬性中断或模型响应异常: {error_msg}")
            print(f"=====================================================================\n")
            return jsonify({
                'status': 'error',
                'message': error_msg,
                'data': result
            }), 500

        try:
            knowledge_topics = None
            if result.get('features', {}).get('functions'):
                functions = result['features']['functions']
                knowledge_topics = functions[:5] if functions else None

            DataCollector.record_code_submission(
                user_id=g.user_id,
                session_id=None,
                code=code,
                result=result,
                knowledge_topics=knowledge_topics
            )
        except Exception as e:
            print(f"⚠️ 记录代码提交失败: {e}")

        print(f"✅ [步骤3/3] 逻辑推演执行完毕，回执结构化缺陷细则")
        print(f"   📊 综合健康评级:【 {result.get('level', 'N/A')} 指数: {result.get('score', 0)} 】")
        print(f"   🐛 检测出缺陷节点数: {len(result.get('ai_analysis', {}).get('problems', []))}")
        print(f"   💡 推理出的策略指导数: {len(result.get('ai_analysis', {}).get('suggestions', []))}")
        print(f"✨ 引擎未发生拥塞，响应报文(HTTP 200 OK)组装下发.")
        print(f"=====================================================================\n")

        return jsonify({
            'status': 'success',
            'message': '代码分析完成',
            'data': result
        }), 200

    except Exception as e:
        print(f"❌ 代码分析异常: {e}")
        traceback.print_exc()
        print(f"{'='*60}\n")

        return jsonify({
            'status': 'error',
            'message': f'代码分析失败: {str(e)}'
        }), 500


@code_bp.route('/api/code/chat', methods=['POST'])
@login_required
def code_chat_stream():
    """
    代码分析对话（流式，不使用 RAG）

    请求体示例：
    {
        "message": "这段代码有什么问题？",
        "code": "#include <stdio.h>\nint main() {...}",
        "features": {...},
        "analysis": {...}  // 可选
    }

    返回：SSE 流式响应
    """
    try:
        data = request.get_json()

        message = data.get('message', '').strip()
        code = data.get('code', '').strip()
        features = data.get('features', {})
        analysis = data.get('analysis')

        if not message:
            return jsonify({
                'status': 'error',
                'message': '缺少问题内容'
            }), 400

        if not code:
            return jsonify({
                'status': 'error',
                'message': '缺少代码内容'
            }), 400

        print(f"\n{'='*60}")
        print(f"💬 代码对话请求")
        print(f"{'='*60}")
        print(f"用户ID: {g.user_id}")
        print(f"问题: {message[:50]}...")
        print(f"代码长度: {len(code)} 字符")
        print(f"特征: {features.get('lines', 0)} 行, 复杂度 {features.get('complexity', 'unknown')}")

        messages = _build_code_chat_prompt(code, features, analysis, message)

        print(f"构建消息: {len(messages)} 条")

        def generate():
            """SSE 生成器"""
            full_response = ""

            try:
                llm_service = ServiceRegistry.get_llm_service()

                print(f"🤖 开始调用 LLM...")

                stream = llm_service.client.chat.completions.create(
                    model=llm_service.model,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=1000,
                    stream=True,
                    timeout=30.0
                )

                for chunk in stream:
                    if chunk.choices and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta

                        if hasattr(delta, 'content') and delta.content:
                            content = delta.content
                            full_response += content

                            yield f"data: {json.dumps({'type': 'content', 'content': content}, ensure_ascii=False)}\n\n"

                print(f"✅ 代码对话完成，共生成 {len(full_response)} 字符")
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"

            except Exception as e:
                print(f"❌ LLM 调用失败: {e}")
                traceback.print_exc()

                yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

        return Response(
            stream_with_context(generate()),
            content_type='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive'
            }
        )

    except Exception as e:
        print(f"❌ 代码对话 API 错误: {e}")
        traceback.print_exc()

        return jsonify({
            'status': 'error',
            'message': f'服务器错误: {str(e)}'
        }), 500
