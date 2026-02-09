/**
 * 代码分析 API
 */

import axios from 'axios';
import { getToken } from './auth';

/**
 * 分析代码
 * 
 * @param {string} code - 待分析的代码字符串
 * @param {string} analysisType - 分析类型：'syntax' | 'logic' | 'full'
 * @returns {Promise<Object>} 分析结果
 * 
 * 返回格式：
 * {
 *   status: 'success',
 *   message: '代码分析完成',
 *   data: {
 *     success: true,
 *     analysis_type: 'full',
 *     code: '...',
 *     features: {
 *       lines: 10,
 *       chars: 150,
 *       has_main: true,
 *       includes: ['stdio.h'],
 *       functions: ['main'],
 *       keywords: { if: 1, for: 0, while: 0, switch: 0 },
 *       complexity: 'low'
 *     },
 *     syntax_check: {
 *       valid: true,
 *       error_count: 0,
 *       errors: []
 *     },
 *     ai_analysis: {
 *       success: true,
 *       problems: [
 *         { severity: 'error', description: '...' },
 *         { severity: 'warning', description: '...' }
 *       ],
 *       suggestions: ['...'],
 *       summary: '...',
 *       knowledge_used: ['第3章-指针', '第5章-数组'],
 *       raw_response: '...'
 *     },
 *     score: 85,
 *     level: 'B',
 *     suggestions: ['...']
 *   }
 * }
 */
export async function analyzeCode(code, analysisType = 'full') {
  try {
    console.log('📤 API: 发送代码分析请求', {
      code_length: code.length,
      analysis_type: analysisType
    });

    const response = await axios.post(
      '/api/code/analyze',
      {
        code: code,
        analysis_type: analysisType
      },
      {
        headers: {
          'Authorization': `Bearer ${getToken()}`
        }
      }
    );

    console.log('📥 API: 收到分析结果', {
      status: response.data.status,
      score: response.data.data?.score
    });

    return response.data;

  } catch (error) {
    console.error('❌ API: 代码分析请求失败', error);
    
    // 处理不同类型的错误
    if (error.response) {
      // 服务器返回错误状态码
      const { status, data } = error.response;
      
      if (status === 401) {
        throw new Error('未登录或登录已过期，请重新登录');
      } else if (status === 400) {
        throw new Error(data.message || '请求参数错误');
      } else if (status === 500) {
        throw new Error(data.message || '服务器错误，请稍后重试');
      } else {
        throw new Error(data.message || `请求失败 (${status})`);
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      throw new Error('网络连接失败，请检查网络');
    } else {
      // 其他错误
      throw new Error(error.message || '未知错误');
    }
  }
}

/**
 * 获取代码分析历史（如果后续需要）
 * 
 * @param {number} limit - 获取数量限制
 * @returns {Promise<Object>} 历史记录列表
 */
export async function getAnalysisHistory(limit = 10) {
  try {
    const response = await axios.get('/api/code/history', {
      params: { limit },
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    });

    return response.data;

  } catch (error) {
    console.error('❌ API: 获取分析历史失败', error);
    throw error;
  }
}

/**
 * 保存代码分析结果（如果后续需要）
 * 
 * @param {Object} analysisData - 分析结果数据
 * @returns {Promise<Object>} 保存结果
 */
export async function saveAnalysisResult(analysisData) {
  try {
    const response = await axios.post(
      '/api/code/save',
      analysisData,
      {
        headers: {
          'Authorization': `Bearer ${getToken()}`
        }
      }
    );

    return response.data;

  } catch (error) {
    console.error('❌ API: 保存分析结果失败', error);
    throw error;
  }
}