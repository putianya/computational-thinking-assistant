computational-thinking-assistant/
│
├── backend/                              # Flask 后端 API 服务
│   ├── app.py                           # Flask 主程序（REST API 路由）
│   ├── config.py                        # 配置文件（环境变量、OpenAI 配置）
│   ├── requirements.txt                 # Python 依赖（Flask, Flask-CORS, openai）
│   ├── .env                             # 环境变量（API 密钥等）
│   ├── services/                        # 业务逻辑层
│   │   ├── __init__.py
│   │   └── llm_service.py              # OpenAI 大语言模型服务
│   └── utils/                           # 工具模块
│       └── __init__.py
│
├── frontend/                             # Vue.js 前端应用
│   ├── index.html                       # HTML 入口（根目录）
│   ├── package.json                     # npm 依赖配置
│   ├── vite.config.js                   # Vite 构建工具配置
│   ├── .gitignore                       # Git 忽略文件
│   └── src/                             # 源代码目录
│       ├── main.js                      # Vue 应用入口
│       ├── App.vue                      # 根组件
│       ├── api/                         # API 请求层
│       │   └── chat.js                 # 封装的 HTTP 请求方法
│       ├── components/                  # Vue 组件（视图层）
│       │   ├── ChatWindow.vue          # 聊天窗口容器组件
│       │   ├── ChatMessage.vue         # 单条消息组件
│       │   ├── ChatInput.vue           # 消息输入框组件
│       │   └── SystemTest.vue          # 系统测试组件
│       ├── stores/                      # 状态管理层（Pinia）
│       │   └── chat.js                 # 聊天状态管理
│       └── assets/                      # 静态资源
│           └── main.css                # 全局样式
│
├── .gitignore                           # 项目级 Git 忽略文件
└── README.md                            # 项目说明文档


前后端分离架构 (Separated Frontend & Backend)

┌──────────────────────┐         ┌──────────────────────┐
│   Vue.js 前端 SPA    │         │   Flask 后端 API     │
│   (localhost:5173)   │         │   (localhost:5000)   │
├──────────────────────┤         ├──────────────────────┤
│                      │         │                      │
│  视图层 (View)        │         │  路由层 (Routes)      │
│  ├─ Components/      │         │  ├─ /api/test       │
│  │  ├─ ChatWindow   │         │  └─ /api/chat       │
│  │  ├─ ChatMessage  │         │                      │
│  │  └─ ChatInput    │         │  业务逻辑层 (Service) │
│                      │  HTTP   │  └─ llm_service.py  │
│  状态管理 (Store)    │ ◄────► │                      │
│  └─ Pinia (chat.js) │  JSON   │  数据层 (Data)       │
│                      │  API    │  └─ OpenAI API      │
│  API 层 (API)        │         │                      │
│  └─ axios (chat.js) │         │  配置层 (Config)     │
│                      │         │  └─ config.py       │
└──────────────────────┘         └──────────────────────┘
    Vite 热更新                       RESTful API
    组件化开发                        无状态服务