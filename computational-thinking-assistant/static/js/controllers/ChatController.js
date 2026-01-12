/**
 * ChatController - 控制器层
 * 职责: 事件处理、连接 Model 和 View
 * 相当于 Qt 的 MainWindow 类（槽函数）
 */
class ChatController {
    constructor() {
        // 创建 Model 和 View 实例
        this.model = new ChatModel();
        this.view = new ChatView();
        
        // 连接信号和槽
        this._connectSignals();
        
        if (AppConfig.debug) {
            console.log('💬 ChatController 初始化完成');
        }
    }
    
    /**
     * 连接信号和槽
     * 相当于 Qt 的: connect(ui->btn, SIGNAL(clicked()), this, SLOT(onBtnClicked()))
     */
    _connectSignals() {
        // 发送按钮点击事件
        this.view.elements.sendBtn.addEventListener('click', () => {
            this.onSendClicked();
        });
        
        // 输入框回车事件
        this.view.elements.messageInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                this.onSendClicked();
            }
        });
        
        // 测试按钮点击事件
        this.view.elements.testBtn.addEventListener('click', () => {
            this.onTestClicked();
        });
    }
    
    /**
     * 槽函数: 发送按钮被点击
     * 相当于 Qt 的: void MainWindow::onSendClicked()
     */
    async onSendClicked() {
        // 1. 获取并验证输入
        const message = this.view.getInputText();
        
        if (!message) {
            this.view.showError('请输入消息！');
            return;
        }
        
        if (message.length > AppConfig.maxMessageLength) {
            this.view.showError(`消息长度不能超过 ${AppConfig.maxMessageLength} 字符！`);
            return;
        }
        
        // 2. 更新 UI
        this.view.setButtonsEnabled(false);
        this.view.addMessage('user', message);
        this.view.clearInput();
        
        try {
            // 3. 调用 Model 发送消息
            const data = await this.model.sendMessage(message);
            
            // 4. 处理响应
            if (data.status === 'success') {
                this.view.addMessage('bot', data.bot_reply);
                
                if (AppConfig.debug) {
                    console.log('✅ 消息发送成功:', data);
                }
            } else {
                this.view.addMessage('bot', `❌ 错误: ${data.message}`);
            }
        } catch (error) {
            // 5. 错误处理
            console.error('❌ 发送消息失败:', error);
            this.view.addMessage('bot', `❌ 发送失败: ${error.message}`);
        } finally {
            // 6. 恢复 UI
            this.view.setButtonsEnabled(true);
            this.view.focusInput();
        }
    }
    
    /**
     * 槽函数: 测试按钮被点击
     * 相当于 Qt 的: void MainWindow::onTestClicked()
     */
    async onTestClicked() {
        // 1. 禁用按钮
        this.view.setTestButtonEnabled(false);
        this.view.showTestResult('<p class="info">⏳ 正在测试连接...</p>');
        
        try {
            // 2. 调用 Model 测试连接
            const data = await this.model.testConnection();
            
            // 3. 显示结果
            const resultHtml = `
                <p class="success">✅ ${data.message}</p>
                <p class="info"><strong>状态:</strong> ${data.status}</p>
                <p class="info"><strong>时间:</strong> ${data.timestamp}</p>
                <p class="info"><strong>版本:</strong> ${data.version}</p>
                <p class="info"><strong>Python:</strong> ${data.python_version}</p>
                <p class="info"><strong>OpenAI 配置:</strong> ${data.openai_configured ? '已配置 ✓' : '未配置 ✗'}</p>
            `;
            this.view.showTestResult(resultHtml);
            
            if (AppConfig.debug) {
                console.log('✅ 系统测试成功:', data);
            }
        } catch (error) {
            // 4. 错误处理
            console.error('❌ 系统测试失败:', error);
            
            const errorHtml = `
                <p class="error">❌ 连接失败</p>
                <p class="info"><strong>错误:</strong> ${error.message}</p>
                <p class="info">请检查:</p>
                <ul>
                    <li>后端服务是否启动</li>
                    <li>网络连接是否正常</li>
                    <li>API 配置是否正确</li>
                </ul>
            `;
            this.view.showTestResult(errorHtml);
        } finally {
            // 5. 恢复按钮
            this.view.setTestButtonEnabled(true);
        }
    }
    
    /**
     * 初始化应用
     * 相当于 Qt 的: void MainWindow::init()
     */
    init() {
        this.view.focusInput();
        
        if (AppConfig.debug) {
            console.log('✅ 应用初始化完成');
            console.log('📝 配置:', AppConfig);
        }
    }
}