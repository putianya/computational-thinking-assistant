/**
 * 前端配置文件
 * 相当于 Qt 的配置类
 */
const AppConfig = {
    // API 基础地址
    apiBaseUrl: '',
    
    // API 端点
    endpoints: {
        test: '/api/test',
        chat: '/api/chat',
        echo: '/api/echo'
    },
    
    // 应用信息
    appName: '计算思维课程助手系统',
    version: '1.0.0',
    
    // UI 配置
    maxMessageLength: 1000,
    typingDelay: 500,  // 打字动画延迟（毫秒）
    
    // 开发模式
    debug: true
};

// 冻结配置对象（防止被修改）
Object.freeze(AppConfig);