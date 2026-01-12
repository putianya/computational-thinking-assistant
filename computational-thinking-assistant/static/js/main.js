/**
 * 应用程序入口
 * 相当于 Qt 的 main.cpp:
 * 
 * int main(int argc, char *argv[]) {
 *     QApplication app(argc, argv);
 *     MainWindow window;
 *     window.show();
 *     return app.exec();
 * }
 */

// 全局 Controller 实例
let chatController;

/**
 * DOM 加载完成后初始化应用
 */
window.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 应用启动中...');
    
    try {
        // 创建 Controller（相当于创建 MainWindow）
        chatController = new ChatController();
        
        // 初始化应用
        chatController.init();
        
        console.log('✅ 应用启动成功');
    } catch (error) {
        console.error('❌ 应用启动失败:', error);
        alert('应用启动失败，请刷新页面重试！');
    }
});

/**
 * 页面卸载前的清理工作
 */
window.addEventListener('beforeunload', () => {
    if (AppConfig.debug) {
        console.log('👋 应用正在关闭...');
    }
});