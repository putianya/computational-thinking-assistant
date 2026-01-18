# 🎓 计算思维课程助手系统

基于大语言模型的智能教学辅助平台，提供用户认证、智能问答、流式对话等功能。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.5-brightgreen.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 目录

- [功能特性](#-功能特性)
- [技术栈](#-技术栈)
- [项目结构](#-项目结构)
- [快速开始](#-快速开始)
- [系统架构](#-系统架构)
- [API 文档](#-api-文档)
- [开发指南](#-开发指南)
- [常见问题](#-常见问题)

---

## ✨ 功能特性

### 🔐 用户认证系统

- ✅ 用户注册/登录（JWT Token 认证）
- ✅ 密码加密存储（Werkzeug Security）
- ✅ "记住密码"功能（localStorage/sessionStorage）
- ✅ 自动登录（Token 验证）
- ✅ 登录状态管理（Pinia）
- ✅ 路由守卫（未登录自动跳转）

### 💬 智能对话功能

- ✅ 实时流式输出（Server-Sent Events）
- ✅ 上下文对话记忆（支持多轮对话）
- ✅ 会话管理（多会话切换）
- ✅ 打字机效果展示
- ✅ Markdown 渲染支持
- ✅ 代码高亮显示

### 🎨 用户界面

- ✅ 响应式设计（适配多种屏幕）
- ✅ 现代化 UI（渐变色、动画效果）
- ✅ 消息气泡样式
- ✅ 加载动画
- ✅ 错误提示

---

## 🛠️ 技术栈

### 后端（Backend）

```
Flask 3.0+           # Web 框架
Flask-SQLAlchemy     # ORM（对象关系映射）
Flask-CORS           # 跨域资源共享
PyJWT                # JWT Token 认证
Werkzeug             # 密码加密
OpenAI API           # 大语言模型接口
Python-dotenv        # 环境变量管理
```

### 前端（Frontend）

```
Vue.js 3.5+          # 渐进式 JavaScript 框架
Pinia 2.3+           # 状态管理
Vue Router 4.5+      # 路由管理
Axios 1.7+           # HTTP 请求库
Vite 6.0+            # 构建工具
```

### 数据库（Database）

```
SQLite               # 轻量级关系型数据库（开发环境）
```

---

## 📁 项目结构

```
computational-thinking-assistant/
│
├── backend/                              # Flask 后端 API 服务
│   ├── app.py                           # Flask 主程序（REST API 路由）
│   ├── config.py                        # 配置文件（环境变量、数据库、AI 配置）
│   ├── database.py                      # 数据库初始化
│   ├── requirements.txt                 # Python 依赖
│   ├── .env                             # 环境变量（API 密钥、数据库配置等）
│   ├── init_admin.py                    # 初始化管理员账号脚本
│   │
│   ├── data/                            # 数据存储目录
│   │   └── app.db                      # SQLite 数据库文件
│   │
│   ├── models/                          # 数据模型层（ORM）
│   │   ├── __init__.py
│   │   ├── user.py                     # 用户模型
│   │   └── chat_session.py             # 聊天会话模型
│   │
│   ├── services/                        # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── auth_service.py             # 认证服务（注册、登录、Token）
│   │   └── llm_service.py              # LLM 服务（OpenAI API 封装）
│   │
│   └── utils/                           # 工具模块
│       ├── __init__.py
│       ├── decorators.py               # 装饰器（@login_required）
│       └── validators.py               # 数据验证工具
│
├── frontend/                             # Vue.js 前端应用
│   ├── index.html                       # HTML 入口
│   ├── package.json                     # npm 依赖配置
│   ├── vite.config.js                   # Vite 构建配置
│   ├── .gitignore                       # Git 忽略文件
│   │
│   └── src/                             # 源代码目录
│       ├── main.js                      # Vue 应用入口
│       ├── App.vue                      # 根组件
│       │
│       ├── api/                         # API 请求层
│       │   ├── auth.js                 # 认证 API（登录、注册、验证）
│       │   └── chat.js                 # 聊天 API（流式输出、上下文管理）
│       │
│       ├── components/                  # Vue 组件（视图层）
│       │   ├── Login.vue               # 登录组件
│       │   ├── Register.vue            # 注册组件
│       │   ├── ChatWindow.vue          # 聊天窗口容器
│       │   ├── ChatMessage.vue         # 单条消息组件
│       │   ├── ChatInput.vue           # 消息输入框
│       │   └── SystemTest.vue          # 系统测试组件
│       │
│       ├── router/                      # 路由配置
│       │   └── index.js                # Vue Router 配置（路由守卫）
│       │
│       ├── stores/                      # 状态管理层（Pinia）
│       │   ├── user.js                 # 用户状态（登录状态、Token）
│       │   └── chat.js                 # 聊天状态（会话、消息历史）
│       │
│       └── assets/                      # 静态资源
│           └── main.css                # 全局样式
│
├── .gitignore                           # 项目级 Git 忽略文件
└── README.md                            # 项目说明文档（本文件）
```

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.11+
- **Node.js**: 18+
- **npm**: 9+

---

### 1️⃣ 克隆项目

```bash
git clone https://github.com/yourusername/computational-thinking-assistant.git
cd computational-thinking-assistant
```

---

### 2️⃣ 后端设置

#### 安装依赖

```bash
cd backend
python -m venv venv                     # 创建虚拟环境
venv\Scripts\activate                   # Windows 激活虚拟环境
# source venv/bin/activate              # macOS/Linux 激活虚拟环境

pip install -r requirements.txt         # 安装依赖
```

#### 配置环境变量

创建 `backend/.env` 文件：

```env
# Flask 配置
SECRET_KEY=your-secret-key-change-in-production-12345678
DEBUG=True
HOST=0.0.0.0
PORT=5000

# 数据库配置（可选，默认使用 SQLite）
# DATABASE_URL=sqlite:///data/app.db

# OpenAI API 配置
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-3.5-turbo

# 聊天功能配置
ENABLE_STREAMING=True
MAX_CONTEXT_MESSAGES=10
TEMPERATURE=0.7
MAX_TOKENS=2000
```

#### 初始化数据库

```bash
python app.py                            # 首次运行会自动创建数据库表
```

#### （可选）创建管理员账号

```bash
python init_admin.py                     # 创建默认管理员账号（admin/admin123）
```

#### 启动后端服务

```bash
python app.py
```

**访问**: http://localhost:5000

---

### 3️⃣ 前端设置

#### 安装依赖

```bash
cd frontend
npm install                              # 安装所有依赖
```

#### 配置环境变量（可选）

创建 `frontend/.env`（可选）：

```env
VITE_API_BASE_URL=http://localhost:5000/api
```

#### 启动开发服务器

```bash
npm run dev
```

**访问**: http://localhost:5173

---

### 4️⃣ 开始使用

1. **注册账号**: 访问 http://localhost:5173/register
2. **登录系统**: 输入用户名密码登录
3. **开始对话**: 在聊天窗口中输入问题

---

## 🏗️ 系统架构

### 前后端分离架构

```
┌─────────────────────────────────┐         ┌─────────────────────────────────┐
│      Vue.js 前端 SPA            │         │      Flask 后端 API             │
│      (localhost:5173)           │         │      (localhost:5000)           │
├─────────────────────────────────┤         ├─────────────────────────────────┤
│                                 │         │                                 │
│  视图层 (View)                   │         │  路由层 (Routes)                 │
│  ├─ Login.vue                   │         │  ├─ /api/auth/register          │
│  ├─ Register.vue                │         │  ├─ /api/auth/login             │
│  ├─ ChatWindow.vue              │         │  ├─ /api/auth/verify            │
│  ├─ ChatMessage.vue             │         │  ├─ /api/chat/stream            │
│  └─ ChatInput.vue               │         │  └─ /api/chat/clear-context     │
│                                 │  HTTP   │                                 │
│  状态管理 (Store - Pinia)        │ ◄────► │  业务逻辑层 (Services)           │
│  ├─ user.js (用户状态)           │  JSON   │  ├─ auth_service.py             │
│  └─ chat.js (聊天状态)           │  API    │  └─ llm_service.py              │
│                                 │  +SSE   │                                 │
│  API 层 (Axios)                 │         │  数据层 (Models - SQLAlchemy)   │
│  ├─ auth.js                     │         │  ├─ user.py                     │
│  └─ chat.js                     │         │  └─ chat_session.py             │
│                                 │         │                                 │
│  路由管理 (Vue Router)           │         │  配置层 (Config)                │
│  └─ index.js (路由守卫)          │         │  └─ config.py                   │
│                                 │         │                                 │
└─────────────────────────────────┘         └─────────────────────────────────┘
    Vite 热更新                                  RESTful API + SSE
    组件化开发                                    JWT Token 认证
    响应式设计                                    SQLite 数据库
```

---

### 数据流向

```
用户操作 → Vue 组件 → Pinia Store → Axios API
                                        ↓
                                   Flask 路由
                                        ↓
                                   Service 层
                                        ↓
                              ┌─────────┴─────────┐
                              ↓                   ↓
                         SQLAlchemy          OpenAI API
                         (数据库)             (AI 模型)
                              ↓                   ↓
                         返回数据              流式返回
                              ↓                   ↓
                         JSON 响应           SSE 事件流
                              ↓                   ↓
                         Vue 组件更新        实时显示
```

---

## 📡 API 文档

### 认证相关 API

#### 1. 用户注册

```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "password": "123456",
  "email": "test@example.com",      // 可选
  "nickname": "测试用户"              // 可选
}
```

**响应**:

```json
{
  "status": "success",
  "message": "注册成功",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "nickname": "测试用户",
    "created_at": "2026-01-19T12:00:00"
  }
}
```

---

#### 2. 用户登录

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "123456"
}
```

**响应**:

```json
{
  "status": "success",
  "message": "登录成功",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "nickname": "测试用户"
  }
}
```

---

#### 3. Token 验证

```http
POST /api/auth/verify
Content-Type: application/json

{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**响应**:

```json
{
  "status": "success",
  "message": "Token 有效",
  "user_id": 1,
  "username": "testuser"
}
```

---

### 聊天相关 API

#### 4. 流式对话（SSE）

```http
POST /api/chat/stream
Content-Type: application/json
Authorization: Bearer <token>

{
  "message": "什么是计算思维？",
  "session_id": "uuid-1234-5678"       // 可选
}
```

**响应**（Server-Sent Events）:

```
data: {"type": "session", "session_id": "uuid-1234-5678"}

data: {"type": "content", "content": "计"}

data: {"type": "content", "content": "算"}

data: {"type": "content", "content": "思"}

data: {"type": "done"}
```

---

#### 5. 清除上下文

```http
POST /api/chat/clear-context
Content-Type: application/json
Authorization: Bearer <token>

{
  "session_id": "uuid-1234-5678"
}
```

---

## 🔧 开发指南

### 本地开发

#### 后端热重载

```bash
cd backend
export FLASK_ENV=development           # macOS/Linux
set FLASK_ENV=development              # Windows
python app.py                          # 自动热重载
```

#### 前端热重载

```bash
cd frontend
npm run dev                            # Vite 自动热重载
```

---

### 代码规范

#### Python (Backend)

```bash
# 使用 Black 格式化代码
pip install black
black backend/

# 使用 flake8 检查代码
pip install flake8
flake8 backend/
```

#### JavaScript (Frontend)

```bash
# 使用 ESLint 检查代码
npm run lint

# 自动修复
npm run lint:fix
```

---

### 数据库管理

#### 查看数据库内容

```bash
# 使用 Python 交互式环境
cd backend
python

>>> from app import app, db
>>> from models.user import User
>>> with app.app_context():
...     users = User.query.all()
...     for user in users:
...         print(user.username)
```

#### 重置数据库

```bash
cd backend
rm data/app.db                         # 删除数据库文件
python app.py                          # 重新创建表
python init_admin.py                   # 重新创建管理员
```

---

### 构建生产版本

#### 前端构建

```bash
cd frontend
npm run build                          # 构建到 dist/ 目录
npm run preview                        # 预览生产版本
```

#### 后端部署

```bash
cd backend
pip install gunicorn                   # 生产环境 WSGI 服务器
gunicorn -w 4 -b 0.0.0.0:5000 app:app  # 启动 4 个工作进程
```

---

## ❓ 常见问题

### Q1: 启动后端报错 `RuntimeError: Either 'SQLALCHEMY_DATABASE_URI' or 'SQLALCHEMY_BINDS' must be set.`

**A**: 检查 `backend/config.py` 中是否配置了 `SQLALCHEMY_DATABASE_URI`。

---

### Q2: 前端无法连接后端

**A**: 检查：

1. 后端是否启动（http://localhost:5000）
2. CORS 配置是否正确（`app.py` 中）
3. 前端 API 地址是否正确（`.env` 或 `chat.js`）

---

### Q3: 登录后刷新页面就退出了

**A**: 检查：

1. `stores/user.js` 中的 `autoLogin()` 是否调用
2. `App.vue` 中的 `onMounted()` 是否执行
3. 浏览器控制台是否有错误

---

### Q4: 流式输出不工作

**A**: 检查：

1. `config.py` 中 `ENABLE_STREAMING=True`
2. `OPENAI_API_KEY` 是否正确配置
3. 浏览器控制台 Network 标签查看 SSE 连接

---

### Q5: 如何更换 AI 模型？

**A**: 修改 `backend/.env`:

```env
OPENAI_MODEL=gpt-4                     # 更换为 GPT-4
# 或
OPENAI_BASE_URL=https://your-custom-api.com/v1  # 使用自定义 API
```

---

## 📝 License

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📧 联系方式

- **项目地址**: https://github.com/yourusername/computational-thinking-assistant
- **作者**: Your Name
- **邮箱**: your.email@example.com

---

<p align="center">
  Made with ❤️ by Your Name
</p>
