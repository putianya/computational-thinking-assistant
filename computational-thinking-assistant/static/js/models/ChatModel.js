/**
 * ChatModel - 前端数据模型
 * 职责: 与后端 API 通信
 * 相当于 Qt 的 QNetworkAccessManager
 */
class ChatModel {
    constructor() {
        this.apiBaseUrl = AppConfig.apiBaseUrl;
        this.endpoints = AppConfig.endpoints;
    }
    
    /**
     * 发送 HTTP 请求（通用方法）
     * 相当于 Qt 的 QNetworkRequest
     */
    async _request(url, options = {}) {
        try {
            const response = await fetch(url, options);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('❌ 网络请求失败:', error);
            throw error;
        }
    }
    
    /**
     * 测试系统连接
     */
    async testConnection() {
        const url = `${this.apiBaseUrl}${this.endpoints.test}`;
        return await this._request(url);
    }
    
    /**
     * 发送聊天消息
     * @param {string} message - 用户消息
     * @returns {Promise<Object>} API 响应
     */
    async sendMessage(message) {
        const url = `${this.apiBaseUrl}${this.endpoints.chat}`;
        
        return await this._request(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });
    }
    
    /**
     * 回声测试
     * @param {string} message - 测试消息
     */
    async echoTest(message) {
        const url = `${this.apiBaseUrl}${this.endpoints.echo}`;
        
        return await this._request(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });
    }
}