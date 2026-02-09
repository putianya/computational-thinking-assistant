import ast
import re
from typing import Dict, List, Any, Optional
from .llm_service import LLMService
from .vector_service import VectorService


class CodeService:
    """代码分析服务类"""
    
    def __init__(self, llm_service: LLMService, vector_service: VectorService):
        """
        初始化代码分析服务
        
        Args:
            llm_service: LLM 服务实例
            vector_service: 向量服务实例
        """
        self.llm_service = llm_service
        self.vector_service = vector_service
    
    def analyze_code(self, code: str, analysis_type: str = 'full') -> Dict[str, Any]:
        """
        分析代码的主入口方法
        
        Args:
            code: 学生提交的代码字符串
            analysis_type: 分析类型 ('syntax', 'logic', 'full')
        
        Returns:
            包含分析结果的字典
        """
        result = {
            'success': False,
            'analysis_type': analysis_type,
            'code': code,
            'features': {},
            'syntax_check': {},
            'ai_analysis': {},
            'score': 0,
            'level': '',  # ⭐ 添加等级字段
            'suggestions': []
        }
        
        try:
            # 1. 预处理代码
            processed_code = self._preprocess_code(code)
            
            # 2. 提取代码特征
            features = self._extract_code_features(processed_code)
            result['features'] = features
            
            # 3. 语法检查
            if analysis_type in ['syntax', 'full']:
                syntax_result = self._check_syntax(processed_code)
                result['syntax_check'] = syntax_result
                
                # 如果语法错误严重，提前返回
                if not syntax_result['valid'] and syntax_result['error_count'] > 0:
                    result['success'] = True
                    result['score'] = 0
                    result['level'] = 'F'  # ⭐ 添加等级
                    return result
            
            # 4. AI 深度分析
            if analysis_type in ['logic', 'full']:
                ai_result = self._ai_analysis(processed_code, features, result['syntax_check'])  # ⭐ 修复：传递 syntax_check
                result['ai_analysis'] = ai_result
            
            # 5. 计算综合评分
            score = self._calculate_score(
                result['syntax_check'],
                result['ai_analysis'],
                features
            )
            result['score'] = score
            result['level'] = self._get_score_level(score)  # ⭐ 添加等级
            
            # 6. 生成改进建议
            suggestions = self._generate_suggestions(
                result['syntax_check'],
                result['ai_analysis'],
                features
            )
            result['suggestions'] = suggestions
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
        
        return result

    def _preprocess_code(self, code: str) -> str:
        """
        预处理代码：去除多余空白、统一格式
        
        Args:
            code: 原始代码
        
        Returns:
            处理后的代码
        """
        # 1. 统一换行符（Windows \r\n → Unix \n）
        code = code.replace('\r\n', '\n')
        
        # 2. 移除首尾空白
        code = code.strip()
        
        # 3. 移除多余的空行（保留最多一个空行）
        # 将 3 个及以上的连续换行符替换为 2 个
        code = re.sub(r'\n{3,}', '\n\n', code)
        
        return code

    def _extract_code_features(self, code: str) -> Dict[str, Any]:
        """
        提取代码特征
    
        Args:
            code: 代码字符串
    
        Returns:
            代码特征字典
        """
        features = {
            # 基础特征
            'lines': 0,
            'chars': 0,
            'has_main': False,
            
            # 高级特征
            'includes': [],
            'functions': [],
            'keywords': {
                'if': 0,
                'for': 0,
                'while': 0,
                'switch': 0
            },
            
            # 复杂度
            'complexity': 'low'
        }
        
        # 基础统计
        features['lines'] = code.count('\n') + 1
        features['chars'] = len(code)
        features['has_main'] = 'int main' in code or 'void main' in code
        
        # 提取头文件
        includes = re.findall(r'#include\s*[<"]([^>"]+)[>"]', code)
        features['includes'] = includes
        
        # 提取函数定义
        # 匹配: int/void/char/float/double function_name(...)
        function_matches = re.findall(
            r'\b(int|void|char|float|double)\s+(\w+)\s*\(',
            code
        )
        features['functions'] = [name for _, name in function_matches]
        
        # 统计关键字出现次数
        features['keywords']['if'] = len(re.findall(r'\bif\s*\(', code))
        features['keywords']['for'] = len(re.findall(r'\bfor\s*\(', code))
        features['keywords']['while'] = len(re.findall(r'\bwhile\s*\(', code))
        features['keywords']['switch'] = len(re.findall(r'\bswitch\s*\(', code))
        
        # 计算复杂度
        control_structures = sum(features['keywords'].values())
        
        if control_structures < 5:
            features['complexity'] = 'low'
        elif control_structures <= 10:
            features['complexity'] = 'medium'
        else:
            features['complexity'] = 'high'
        
        return features

    def _check_syntax(self, code: str) -> Dict[str, Any]:
        """
        语法检查（使用 GCC 编译器）
        
        Returns:
            {
                'valid': bool,
                'error_count': int,
                'errors': [{'line': int, 'message': str}],
                'warnings': [...]
            }
        """
        import subprocess
        import tempfile
        import os
        
        result = {
            'valid': True,
            'error_count': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            # 1. 创建临时文件
            with tempfile.NamedTemporaryFile(
                mode='w', 
                suffix='.c', 
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(code)
                temp_file = f.name
            
            # 2. 调用 GCC 进行语法检查
            # -fsyntax-only: 只检查语法，不生成目标文件
            # -Wall: 显示所有警告
            # -Wextra: 额外警告
            gcc_cmd = [
                'gcc',  # 如果需要指定路径：r'S:\Qt\Tools\mingw1310_64\bin\gcc.exe'
                '-fsyntax-only',
                '-Wall',
                '-Wextra',
                '-std=c11',  # 使用C11标准
                temp_file
            ]
            
            process = subprocess.run(
                gcc_cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=5  # 5秒超时
            )
            
            # 3. 解析 GCC 输出
            if process.returncode != 0:
                result['valid'] = False
                
                # 解析错误信息
                for line in process.stderr.splitlines():
                    # GCC 输出格式：文件名:行号:列号: 错误类型: 错误信息
                    if 'error:' in line.lower():
                        # 提取行号和错误信息
                        parts = line.split(':', 3)
                        if len(parts) >= 4:
                            try:
                                line_num = int(parts[1])
                                message = parts[3].strip()
                                result['errors'].append({
                                    'line': line_num,
                                    'message': message
                                })
                            except (ValueError, IndexError):
                                result['errors'].append({
                                    'line': 0,
                                    'message': line.strip()
                                })
                        
                    elif 'warning:' in line.lower():
                        parts = line.split(':', 3)
                        if len(parts) >= 4:
                            try:
                                line_num = int(parts[1])
                                message = parts[3].strip()
                                result['warnings'].append({
                                    'line': line_num,
                                    'message': message
                                })
                            except (ValueError, IndexError):
                                pass
                        
                result['error_count'] = len(result['errors'])
            
            # 4. 清理临时文件
            try:
                os.unlink(temp_file)
            except:
                pass
            
        except subprocess.TimeoutExpired:
            result['valid'] = False
            result['errors'].append({
                'line': 0,
                'message': '编译超时（代码可能存在死循环或无限递归）'
            })
        
        except FileNotFoundError:
            # GCC 未安装
            result['valid'] = False
            result['errors'].append({
                'line': 0,
                'message': '系统未安装 GCC 编译器，无法进行语法检查'
            })
        
        except Exception as e:
            result['valid'] = False
            result['errors'].append({
                'line': 0,
                'message': f'语法检查失败: {str(e)}'
            })
        
        return result

    def _ai_analysis(
        self, code: str, features: Dict[str, Any], syntax_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用 AI 进行深度代码分析
        
        Args:
            code: 预处理后的代码
            features: 代码特征
            syntax_result: 语法检查结果
        
        Returns:
            AI 分析结果字典
        """
        try:
            # 1. 从知识库检索相关知识
            knowledge_context = self._retrieve_code_knowledge(code, features)
            
            # 2. 构建分析提示词
            prompt = self._build_analysis_prompt(
                code, features, syntax_result, knowledge_context
            )
            
            # 3. 调用 LLM 分析
            response = self.llm_service.client.chat.completions.create(
                model=self.llm_service.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的 C 语言代码分析助手，擅长发现代码问题并给出改进建议。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # 较低温度，保证输出稳定
                max_tokens=2000
            )
            
            # 4. 解析 AI 返回结果
            ai_content = response.choices[0].message.content
            parsed_result = self._parse_ai_response(ai_content)
            
            return {
                'success': True,
                'problems': parsed_result.get('problems', []),
                'suggestions': parsed_result.get('suggestions', []),
                'summary': parsed_result.get('summary', ''),  # ⭐ 修复：改为 summary
                'knowledge_used': knowledge_context.get('sources', []),
                'raw_response': ai_content
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'problems': [],
                'suggestions': [],
                'summary': ''  # ⭐ 修复：改为 summary
            }

    def _retrieve_code_knowledge(
        self, code: str, features: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        从知识库检索与代码相关的知识
        
        Args:
            code: 代码字符串
            features: 代码特征
        
        Returns:
            检索到的知识上下文
        """
        # 构建检索查询（关键词映射策略）
        query_parts = []
        
        # 检查指针相关
        if '*' in code or 'pointer' in code.lower():
            query_parts.append('指针错误 指针使用')
        
        # 检查数组相关
        if '[' in code or 'array' in code.lower():
            query_parts.append('数组越界 数组访问')
        
        # 检查内存管理
        if 'malloc' in code or 'free' in code:
            query_parts.append('内存管理 内存泄漏')
        
        # 基于包含的头文件查询
        if features['includes']:
            query_parts.append(f"使用了库: {', '.join(features['includes'])}")
        
        # 基于复杂度查询
        if features['complexity'] == 'high':
            query_parts.append("复杂代码 常见错误")
        
        # 合并查询词
        query = ' '.join(query_parts) if query_parts else "C语言 常见错误"
        
        # 调用向量服务检索
        search_results = self.vector_service.search(
            query=query,
            top_k=3,
            threshold=0.6
        )
        
        # 整理检索结果
        context = {
            'query': query,
            'sources': [],
            'content': []
        }
        
        for result in search_results:
            context['sources'].append(result.get('source', 'unknown'))
            context['content'].append(result.get('text', ''))
        
        return context

    def _build_analysis_prompt(
        self,
        code: str,
        features: Dict[str, Any],
        syntax_result: Dict[str, Any],
        knowledge_context: Dict[str, Any]
    ) -> str:
        """
        构建代码分析提示词
        
        Args:
            code: 代码字符串
            features: 代码特征
            syntax_result: 语法检查结果
            knowledge_context: 知识库上下文
        
        Returns:
            分析提示词
        """
        prompt = """【代码信息】
- 行数：{lines}
- 函数：{functions}
- 复杂度：{complexity}
- 包含头文件：{includes}
- 控制结构：if {if_count}次, for {for_count}次, while {while_count}次

【待分析代码】
```c
{code}
```
""".format(
            lines=features['lines'],
            functions=', '.join(features['functions']) if features['functions'] else '无',
            complexity=features['complexity'],
            includes=', '.join(features['includes']) if features['includes'] else '无',
            if_count=features['keywords']['if'],
            for_count=features['keywords']['for'],
            while_count=features['keywords']['while'],
            code=code
        )

        # 添加语法错误信息
        if not syntax_result.get('valid', True):
            prompt += f"""\n【语法错误】
{syntax_result.get('error_message', '存在语法错误')}
"""

        # 添加知识库参考
        if knowledge_context.get('content'):
            prompt += "\n【参考资料】\n"
            for i, (source, content) in enumerate(zip(
                knowledge_context.get('sources', []),
                knowledge_context['content']
            ), 1):
                prompt += f"来源：{source}\n内容：{content[:200]}...\n\n"

        # 分析要求
        prompt += """【分析要求】
请从以下方面分析：
1. 语法和逻辑错误
2. 代码风格
3. 性能优化
4. 最佳实践

【输出格式】
严格按照以下格式输出：

【问题列表】
1. [严重] 问题描述
2. [警告] 问题描述

【修改建议】
1. 建议内容
2. 建议内容

【总结】
总体评价
"""

        return prompt

    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """
        解析 AI 返回的分析结果
        
        Args:
            response: AI 返回的原始文本
        
        Returns:
            结构化的分析结果
        """
        result = {
            'problems': [],      # 问题列表
            'suggestions': [],   # 修改建议
            'summary': ''        # 总结
        }
        
        # 1. 提取【问题列表】部分
        issues_match = re.search(
            r'【问题列表】(.+?)【修改建议】',
            response,
            re.DOTALL
        )
        
        if issues_match:
            issues_text = issues_match.group(1)
            # 匹配格式：1. [严重] 问题描述
            issue_lines = re.findall(
                r'\d+\.\s*\[(.+?)\]\s*(.+?)(?=\n\d+\.|\n【|\Z)',
                issues_text,
                re.DOTALL
            )
            
            for severity, description in issue_lines:
                result['problems'].append({
                    'severity': 'error' if '严重' in severity else 'warning',
                    'description': description.strip()
                })
        
        # 2. 提取【修改建议】部分
        suggestions_match = re.search(
            r'【修改建议】(.+?)【总结】',
            response,
            re.DOTALL
        )
        
        if suggestions_match:
            suggestions_text = suggestions_match.group(1)
            # 匹配格式：1. 建议内容
            suggestion_lines = re.findall(
                r'\d+\.\s*(.+?)(?=\n\d+\.|\n【|\Z)',
                suggestions_text,
                re.DOTALL
            )
            
            result['suggestions'] = [s.strip() for s in suggestion_lines]
        
        # 3. 提取【总结】部分
        summary_match = re.search(
            r'【总结】\s*(.+?)(?:\Z)',
            response,
            re.DOTALL
        )
        
        if summary_match:
            result['summary'] = summary_match.group(1).strip()
        
        return result

    def _calculate_score(
        self,
        syntax_result: Dict[str, Any],
        ai_result: Dict[str, Any],
        features: Dict[str, Any]
    ) -> int:
        """
        计算综合评分（0-100分）
        
        评分维度：
        - 语法正确性：30分
        - 逻辑正确性：30分
        - 代码风格：20分
        - 性能优化：20分
        
        Args:
            syntax_result: 语法检查结果
            ai_result: AI 分析结果
            features: 代码特征
        
        Returns:
            分数（0-100）
        """
        score = 100  # 从满分开始扣分
        
        # ========== 1. 语法正确性（30分） ==========
        if not syntax_result.get('valid', True):
            # 每个语法错误扣5分
            error_count = syntax_result.get('error_count', 0)
            score -= min(error_count * 5, 30)  # 最多扣30分
        
        # ========== 2. 逻辑正确性 + 代码风格（50分） ==========
        # 从 AI 分析结果中统计问题
        if ai_result.get('success', False):
            problems = ai_result.get('problems', [])
            
            for problem in problems:
                severity = problem.get('severity', 'warning')
                
                if severity == 'error':
                    # 严重问题（逻辑错误）：-5分
                    score -= 5
                else:
                    # 警告问题（风格问题）：-2分
                    score -= 2
        
        # ========== 3. 性能优化（根据复杂度和代码特征） ==========
        # 如果复杂度过高，扣分
        if features.get('complexity') == 'high':
            score -= 5
        
        # 如果没有注释（根据代码行数判断）
        if features.get('lines', 0) > 20:
            # 检查是否有 # 注释（简化判断）
            has_comments = '//' in ai_result.get('raw_response', '') or '/*' in ai_result.get('raw_response', '')
            if not has_comments:
                score -= 5
        
        # ========== 4. 确保分数在 0-100 范围内 ==========
        score = max(0, min(score, 100))
        
        return score

    def _get_score_level(self, score: int) -> str:
        """
        根据分数获取等级
        
        Args:
            score: 分数（0-100）
        
        Returns:
            等级字符串（A/B/C/D/F）
        """
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    def _generate_suggestions(
        self,
        syntax_result: Dict[str, Any],
        ai_result: Dict[str, Any],
        features: Dict[str, Any]
    ) -> List[str]:
        """
        生成改进建议
        
        Args:
            syntax_result: 语法检查结果
            ai_result: AI 分析结果
            features: 代码特征
        
        Returns:
            建议列表
        """
        suggestions = []
        
        # 从 AI 分析结果中提取建议
        if ai_result.get('suggestions'):
            suggestions.extend(ai_result['suggestions'])
        
        return suggestions

