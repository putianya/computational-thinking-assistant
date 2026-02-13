/**
 * 代码分析 API
 */

// 基础 URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

/**
 * 获取 token
 */
function getToken() {
  return localStorage.getItem("token");
}

/**
 * 分析代码
 *
 * @param {string} code - 代码内容
 * @param {string} analysisType - 分析类型 (syntax/logic/full)
 * @returns {Promise<Object>} 分析结果
 */
export async function analyzeCode(code, analysisType = "full") {
  try {
    console.log("📤 发送代码分析请求:", {
      codeLength: code.length,
      analysisType,
    });

    const response = await fetch(`${API_BASE_URL}/code/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getToken()}`,
      },
      credentials: "include",
      body: JSON.stringify({
        code,
        analysis_type: analysisType,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    console.log("✅ 分析完成:", result);

    return result;
  } catch (error) {
    console.error("❌ 代码分析失败:", error);
    throw error;
  }
}

/**
 * ⭐⭐⭐ 代码对话（流式）⭐⭐⭐
 *
 * @param {Object} params - 请求参数
 * @param {string} params.message - 用户问题
 * @param {string} params.code - 代码内容
 * @param {Object} params.features - 代码特征
 * @param {Object} params.analysis - AI 分析结果（可选）
 * @param {Function} onChunk - 接收数据块的回调
 * @param {Function} onComplete - 完成的回调
 * @param {Function} onError - 错误的回调
 */
export async function codeChat(
  { message, code, features, analysis },
  onChunk,
  onComplete,
  onError,
) {
  try {
    console.log("📤 发送代码对话请求:", {
      message: message.substring(0, 50) + "...",
      codeLength: code.length,
      hasAnalysis: !!analysis,
    });

    const response = await fetch(`${API_BASE_URL}/code/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getToken()}`,
        Accept: "text/event-stream",
      },
      credentials: "include",
      body: JSON.stringify({
        message,
        code,
        features,
        analysis,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    // ========== 读取 SSE 流 ==========
    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");

    let buffer = "";
    let firstChunkReceived = false;
    const startTime = Date.now();

    // ⭐ 累积所有内容
    let accumulatedContent = "";

    while (true) {
      const { done, value } = await reader.read();

      if (done) {
        console.log("📥 流式读取完成");
        console.log(`📊 总共接收: ${accumulatedContent.length} 字符`);
        break;
      }

      const text = decoder.decode(value, { stream: true });
      buffer += text;

      // 按行分割
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;

        const jsonStr = line.slice(6).trim();
        if (!jsonStr) continue;

        try {
          const data = JSON.parse(jsonStr);

          // ⭐ 首字节延迟统计
          if (!firstChunkReceived && data.type === "content") {
            firstChunkReceived = true;
            const latency = Date.now() - startTime;
            console.log(`⚡ 首字节延迟: ${latency}ms`);
          }

          switch (data.type) {
            case "content":
              if (data.content) {
                // 累积内容
                accumulatedContent += data.content;

                // 调用回调（前端显示）
                if (onChunk) {
                  onChunk(data.content);
                }
              }
              break;

            case "done":
              console.log("✅ 服务器发送完成信号");
              console.log(`📊 完整回答长度: ${accumulatedContent.length} 字符`);

              if (onComplete) {
                onComplete();
              }
              return;

            case "error":
              console.error("❌ 服务器错误:", data.message);
              if (onError) {
                onError(new Error(data.message));
              }
              return;
          }
        } catch (parseError) {
          console.warn("⚠️ JSON 解析失败:", jsonStr, parseError);
        }
      }
    }

    // ⭐ 如果没有明确的 done 信号，也调用 onComplete
    if (onComplete) {
      onComplete();
    }
  } catch (error) {
    console.error("❌ 代码对话失败:", error);
    if (onError) {
      onError(error);
    }
  }
}

/**
 * 获取代码示例列表（可选功能）
 */
export async function getCodeExamples() {
  try {
    const response = await fetch(`${API_BASE_URL}/code/examples`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${getToken()}`,
      },
      credentials: "include",
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error("❌ 获取示例失败:", error);
    throw error;
  }
}

// 导出默认对象（可选）
export default {
  analyzeCode,
  codeChat,
  getCodeExamples,
};
