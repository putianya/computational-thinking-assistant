/**
 * ChatView - 视图层
 * 职责: DOM 操作和 UI 更新
 * 相当于 Qt 的 QWidget 操作（ui->label->setText()）
 */
class ChatView {
    constructor() {
        // 获取 DOM 元素（相当于 Qt 的 ui->xxx）
        this.elements = {
            messagesContainer: document.getElementById('chatMessages'),
            messageInput: document.getElementById('messageInput'),
            sendBtn: document.getElementById('sendBtn'),
            testBtn: document.getElementById('testBtn'),
            testResult: document.getElementById('testResult')
        };
        
        // 验证元素是否存在
        this._validateElements();
    }
    
    /**
     * 验证必需的 DOM 元素是否存在
     */
    _validateElements() {
        for (const [key, element] of Object.entries(this.elements)) {
            if (!element) {
                console.error(`❌ 找不到元素: ${key}`);
            }
        }
    }
    
    /**
     * 添加消息到聊天区域
     * @param {string} type - 消息类型 ('user' 或 'bot')
     * @param {string} content - 消息内容
     */
    addMessage(type, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const timeStr = new Date().toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        // 转义 HTML 并保留换行
        const safeContent = this._escapeHtml(content).replace(/\n/g, '<br>');
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${safeContent}
                <span class="message-time">${timeStr}</span>
            </div>
        `;
        
        this.elements.messagesContainer.appendChild(messageDiv);
        this._scrollToBottom();
    }
    
    /**
     * 转义 HTML（防止 XSS 攻击）
     */
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * 滚动到底部
     */
    _scrollToBottom() {
        this.elements.messagesContainer.scrollTop = 
            this.elements.messagesContainer.scrollHeight;
    }
    
    /**
     * 获取输入框内容
     * 相当于 Qt 的: ui->input->text()
     */
    getInputText() {
        return this.elements.messageInput.value.trim();
    }
    
    /**
     * 清空输入框
     * 相当于 Qt 的: ui->input->clear()
     */
    clearInput() {
        this.elements.messageInput.value = '';
    }
    
    /**
     * 设置按钮启用状态
     * 相当于 Qt 的: ui->btn->setEnabled(bool)
     */
    setButtonsEnabled(enabled) {
        this.elements.messageInput.disabled = !enabled;
        this.elements.sendBtn.disabled = !enabled;
        
        if (enabled) {
            this.elements.sendBtn.innerHTML = '发送';
            this.elements.sendBtn.classList.remove('loading');
        } else {
            this.elements.sendBtn.innerHTML = '<span class="spinner"></span> 发送中...';
            this.elements.sendBtn.classList.add('loading');
        }
    }
    
    /**
     * 显示测试结果
     */
    showTestResult(html) {
        this.elements.testResult.classList.add('show');
        this.elements.testResult.innerHTML = html;
    }
    
    /**
     * 设置测试按钮状态
     */
    setTestButtonEnabled(enabled) {
        this.elements.testBtn.disabled = !enabled;
        
        if (enabled) {
            this.elements.testBtn.textContent = '测试系统状态';
        } else {
            this.elements.testBtn.textContent = '测试中...';
        }
    }
    
    /**
     * 聚焦到输入框
     * 相当于 Qt 的: ui->input->setFocus()
     */
    focusInput() {
        this.elements.messageInput.focus();
    }
    
    /**
     * 显示错误提示
     */
    showError(message) {
        alert(`❌ ${message}`);
    }
    
    /**
     * 显示成功提示
     */
    showSuccess(message) {
        // 可以改用 toast 提示
        console.log(`✅ ${message}`);
    }
}