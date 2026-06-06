# 🎓 计算思维课程助手系统

基于大语言模型（LLM）与 RAG 检索增强生成技术的智能教学辅助平台，提供用户认证、智能问答、代码分析、知识库管理、学习数据分析等功能。

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1+-green.svg)](https://flask.palletsprojects.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.4+-brightgreen.svg)](https://vuejs.org/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.4+-orange.svg)](https://www.trychroma.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 目录

- [功能特性](#-功能特性)
- [技术栈](#-技术栈)
- [项目结构](#-项目结构)
- [相关文档（部署与使用指南）](#-相关文档部署与使用指南)
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
- ✅ 用户登出

### 💬 智能对话功能

- ✅ 实时流式输出（Server-Sent Events）
- ✅ 上下文对话记忆（支持多轮对话）
- ✅ 多会话管理（新建、切换、重命名、删除会话）
- ✅ 打字机效果展示
- ✅ Markdown 渲染支持（marked.js）
- ✅ 代码高亮显示
- ✅ RAG 检索增强：自动检索知识库相关内容辅助回答

### 📚 知识库管理（RAG）

- ✅ 文档上传（支持 TXT、PDF、Markdown 等格式）
- ✅ 自动文本分块与向量化（ChromaDB + sentence-transformers）
- ✅ 知识块查看、编辑、删除
- ✅ 向量相似度检索
- ✅ 中文分词支持（jieba）
- ✅ 知识库统计信息

### 🔍 代码分析功能

- ✅ Python 代码语法检查（AST 解析）
- ✅ 代码逻辑分析（复杂度、结构）
- ✅ AI 驱动的代码评分与建议
- ✅ 代码问答（针对提交代码的流式问答）

### 📊 学习数据分析

- ✅ 学习概览（问答次数、活跃天数、知识覆盖率）
- ✅ 学习趋势图（活跃度热力图、趋势折线图）
- ✅ 知识掌握度分析（各知识点掌握情况）
- ✅ 薄弱点分析（高频错误模式）
- ✅ 学习报告生成与 PDF 导出

### 👑 管理员功能

- ✅ 用户列表查看
- ✅ 用户角色管理（普通用户 / 管理员）
- ✅ 用户状态管理（启用 / 禁用）
- ✅ 用户删除
- ✅ 学生学习数据统计

### 🎨 用户界面

- ✅ 响应式设计（适配多种屏幕）
- ✅ 现代化 UI（渐变色、动画效果）
- ✅ 标签页导航（对话 / 代码分析 / 知识库 / 学习分析）
- ✅ 消息气泡样式
- ✅ 加载动画与错误提示

---

## 🛠️ 技术栈

### 后端（Backend）

```
Flask 3.1+                # Web 框架
Flask-SQLAlchemy          # ORM（对象关系映射）
Flask-CORS                # 跨域资源共享
PyJWT                     # JWT Token 认证
Werkzeug                  # 密码加密
OpenAI API (openai 2.x)   # 大语言模型接口（兼容第三方 API）
Python-dotenv             # 环境变量管理
ChromaDB 0.4+             # 向量数据库（RAG 核心）
sentence-transformers     # 文本向量化模型
jieba                     # 中文分词
matplotlib                # 图表生成（学习报告）
reportlab                 # PDF 报告生成
```

### 前端（Frontend）

```
Vue.js 3.4+               # 渐进式 JavaScript 框架
Pinia 2.1+                # 状态管理
Vue Router 4.6+           # 路由管理
Axios 1.6+                # HTTP 请求库
marked 17.x               # Markdown 渲染
Vite 5.0+                 # 构建工具
```

### 数据库（Database）

```
SQLite                    # 轻量级关系型数据库（开发/生产环境）
ChromaDB                  # 向量数据库（知识块嵌入存储）
```

---

## 📁 项目结构

```
computational-thinking-assistant/
│
├── backend/                                   # Flask 后端 API 服务
│   ├── app.py                                # Flask 主程序（所有 REST API 路由）
│   ├── config.py                             # 配置文件（环境变量、数据库、AI 配置）
│   ├── database.py                           # 数据库初始化
│   ├── requirements.txt                      # Python 依赖
│   ├── .env                                  # 环境变量（API 密钥等，不提交到 Git）
│   │
│   ├── data/                                 # 数据存储目录
│   │   └── app.db                           # SQLite 数据库文件
│   │
│   ├── models/                               # 数据模型层（SQLAlchemy ORM）
│   │   ├── __init__.py
│   │   ├── user.py                          # 用户模型
│   │   ├── chat_session.py                  # 聊天会话模型
│   │   ├── chat_message.py                  # 聊天消息模型
│   │   ├── knowledge_chunk.py               # 知识块模型
│   │   ├── error_pattern.py                 # 错误模式模型（薄弱点分析）
│   │   ├── learning_record.py               # 学习记录模型
│   │   └── learning_report.py               # 学习报告模型
│   │
│   ├── services/                             # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── auth_service.py                  # 认证服务（注册、登录、Token）
│   │   ├── llm_service.py                   # LLM 服务（OpenAI API 封装，流式输出）
│   │   ├── chat_service.py                  # 聊天服务（会话、消息持久化）
│   │   ├── vector_service.py                # 向量服务（ChromaDB，RAG 检索）
│   │   ├── code_service.py                  # 代码分析服务（AST 解析 + AI 评分）
│   │   └── analytics/                       # 数据分析服务包
│   │       ├── __init__.py
│   │       ├── data_collector.py            # 学习数据采集
│   │       ├── stats_calculator.py          # 统计指标计算
│   │       ├── weakness_analyzer.py         # 薄弱点分析
│   │       ├── chart_generator.py           # 图表生成（matplotlib）
│   │       ├── report_generator.py          # 报告生成
│   │       └── pdf_generator.py             # PDF 导出（reportlab）
│   │
│   ├── utils/                                # 工具模块
│   │   ├── __init__.py
│   │   ├── decorators.py                    # 装饰器（@login_required, @admin_required）
│   │   ├── validators.py                    # 数据验证工具
│   │   ├── text_processor.py               # 文本预处理（分块、清洗）
│   │   └── question_classifier.py           # 问题类型分类器
│   │
│   ├── scripts/                              # 运维脚本
│   │   ├── import_knowledge.py             # 批量导入知识库脚本
│   │   └── fix_chunk_ids.py                # 修复知识块 ID 脚本（数据迁移/异常修复用）
│   │
│   └── tests/                               # 测试文件
│       ├── test_api.py                      # API 集成测试
│       ├── test_vector_service.py           # 向量服务测试
│       ├── test_rag_degradation.py          # RAG 降级测试
│       ├── test_data_collection.py          # 数据采集测试
│       └── ...                              # 其他测试脚本
│
├── frontend/                                  # Vue.js 前端应用
│   ├── index.html                            # HTML 入口
│   ├── package.json                          # npm 依赖配置
│   ├── vite.config.js                        # Vite 构建配置
│   ├── .gitignore                            # Git 忽略文件
│   │
│   └── src/                                  # 源代码目录
│       ├── main.js                           # Vue 应用入口
│       ├── App.vue                           # 根组件（路由入口）
│       │
│       ├── api/                              # API 请求层（Axios 封装）
│       │   ├── auth.js                      # 认证 API（登录、注册、验证、登出）
│       │   ├── chat.js                      # 聊天 API（流式输出、会话管理）
│       │   ├── code.js                      # 代码分析 API
│       │   ├── knowledge.js                 # 知识库 API（上传、查询、删除）
│       │   ├── analytics.js                 # 数据分析 API
│       │   └── user.js                      # 用户信息 API
│       │
│       ├── components/                       # Vue 组件（视图层）
│       │   ├── Login.vue                    # 登录组件
│       │   ├── Register.vue                 # 注册组件
│       │   ├── TabBar.vue                   # 顶部标签页导航
│       │   ├── ChatView.vue                 # 聊天主视图（含会话列表）
│       │   ├── ChatWindow.vue               # 聊天消息窗口
│       │   ├── ChatMessage.vue              # 单条消息气泡
│       │   ├── ChatInput.vue                # 消息输入框
│       │   ├── SessionList.vue              # 会话列表侧边栏
│       │   ├── CodeAnalyzer.vue             # 代码分析面板
│       │   ├── KnowledgeBase.vue            # 知识库管理面板
│       │   ├── UserManagement.vue           # 用户管理（管理员）
│       │   ├── ConfirmDialog.vue            # 确认对话框组件
│       │   ├── SystemTest.vue               # 系统测试组件
│       │   └── analytics/                   # 数据分析组件
│       │       ├── LearningAnalytics.vue    # 学习分析主面板
│       │       ├── OverviewPanel.vue        # 概览数据面板
│       │       ├── TrendChart.vue           # 学习趋势图
│       │       ├── ActivityHeatmap.vue      # 活跃度热力图
│       │       ├── WeaknessChart.vue        # 薄弱点分析图
│       │       ├── BaseChart.vue            # 图表基础组件
│       │       └── ReportExport.vue         # 学习报告导出
│       │
│       ├── router/                           # 路由配置
│       │   └── index.js                     # Vue Router（路由守卫）
│       │
│       ├── stores/                           # 状态管理层（Pinia）
│       │   ├── user.js                      # 用户状态（登录状态、Token、权限）
│       │   ├── chat.js                      # 聊天状态（会话列表、消息历史）
│       │   └── analytics.js                 # 分析状态（学习数据缓存）
│       │
│       └── assets/                           # 静态资源
│           └── main.css                     # 全局样式
│
├── .gitignore                                # 项目级 Git 忽略文件
└── README.md                                 # 项目说明文档（本文件）
```

---

## � 相关文档（部署与使用指南）

为保证主说明文档的精简，我们已将详细的环境搭建教程及操作手册分离至单独文件：

- 🚀 **系统部署与环境搭建**，请参阅：[安装部署说明书.md](./安装部署说明书.md)
- 📝 **系统各项功能详细操作**，请参阅：[系统使用说明书.md](./系统使用说明书.md)

---

## 🏗️ 系统架构

### 前后端分离 + RAG 架构

```
┌─────────────────────────────────────┐         ┌───────────────────────────────────────┐
│        Vue.js 前端 SPA              │         │          Flask 后端 API               │
│        (localhost:5173)             │         │          (localhost:5000)              │
├─────────────────────────────────────┤         ├───────────────────────────────────────┤
│                                     │         │                                       │
│  视图层 (Components)                 │         │  路由层 (app.py)                       │
│  ├─ Login / Register                │         │  ├─ /api/auth/*                       │
│  ├─ ChatView / ChatWindow           │         │  ├─ /api/chat/*                       │
│  ├─ CodeAnalyzer                    │         │  ├─ /api/sessions/*                   │
│  ├─ KnowledgeBase                   │  HTTP   │  ├─ /api/knowledge/*                  │
│  ├─ LearningAnalytics               │ ◄─────► │  ├─ /api/code/*                       │
│  └─ UserManagement (admin)          │  JSON   │  ├─ /api/analytics/*                  │
│                                     │  +SSE   │  └─ /api/admin/*                      │
│  状态管理 (Pinia Stores)             │         │                                       │
│  ├─ user.js                         │         │  业务逻辑层 (Services)                 │
│  ├─ chat.js                         │         │  ├─ auth_service.py                   │
│  └─ analytics.js                   │         │  ├─ llm_service.py (OpenAI SSE)        │
│                                     │         │  ├─ chat_service.py                   │
│  API 层 (Axios)                     │         │  ├─ vector_service.py (ChromaDB)      │
│  ├─ auth.js / chat.js               │         │  ├─ code_service.py (AST + AI)        │
│  ├─ code.js / knowledge.js          │         │  └─ analytics/ (报告/图表/PDF)         │
│  ├─ analytics.js / user.js          │         │                                       │
│                                     │         │  数据层 (SQLAlchemy Models)            │
│  路由管理 (Vue Router)               │         │  ├─ User / ChatSession / ChatMessage  │
│  └─ index.js (路由守卫)              │         │  ├─ KnowledgeChunk / ErrorPattern     │
│                                     │         │  └─ LearningRecord / LearningReport   │
└─────────────────────────────────────┘         └───────────────────────────────────────┘
                                                         │               │
                                                    SQLite DB       ChromaDB
                                                  (关系型数据)     (向量数据库)
```

---

### RAG 数据流向

```
用户提问
    │
    ▼
问题分类（question_classifier）
    │
    ├─── 知识类问题 ──► 向量检索（ChromaDB）──► 召回相关知识块
    │                                               │
    │                                               ▼
    └─── 直接问答 ──────────────────────► 构建 Prompt（含上下文 + 知识块）
                                                    │
                                                    ▼
                                            LLM 流式生成（OpenAI SSE）
                                                    │
                                                    ▼
                                          前端实时打字机效果展示
```

---

### 学习分析流向

```
用户交互（问答、代码提交）
    │
    ▼
数据采集（data_collector）── 写入 LearningRecord / ErrorPattern
    │
    ▼
统计计算（stats_calculator）── 活跃度、知识覆盖率、问答次数
    │
    ▼
薄弱点分析（weakness_analyzer）── 高频错误聚合
    │
    ▼
图表生成（chart_generator / matplotlib）
    │
    ▼
报告生成（report_generator）── 文字 + 图表
    │
    ▼
PDF 导出（pdf_generator / reportlab）
```

---

## 📡 API 文档

### 认证相关 API (`/api/auth/*`)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录，返回 JWT Token |
| POST | `/api/auth/logout` | 用户登出 |
| POST | `/api/auth/verify` | 验证 Token 有效性 |
| GET  | `/api/user/profile` | 获取当前用户信息 |

---

#### 用户注册

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

#### 用户登录

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
    "role": "user"
  }
}
```

---

### 聊天相关 API (`/api/chat/*`, `/api/sessions/*`)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/chat/stream` | 发送消息，SSE 流式返回 AI 回复 |
| POST | `/api/chat/clear-context` | 清除指定会话的上下文 |
| GET  | `/api/sessions` | 获取当前用户的所有会话 |
| GET  | `/api/sessions/<id>/messages` | 获取会话历史消息 |
| PUT  | `/api/sessions/<id>/rename` | 重命名会话 |
| POST | `/api/sessions/new` | 创建新会话 |
| DELETE | `/api/sessions/<id>` | 删除会话 |

---

#### 流式对话（SSE）

```http
POST /api/chat/stream
Content-Type: application/json
Authorization: Bearer <token>

{
  "message": "什么是计算思维？",
  "session_id": "uuid-1234-5678"       // 可选，不传则自动创建新会话
}
```

**响应**（Server-Sent Events）:

```
data: {"type": "session", "session_id": "uuid-1234-5678"}

data: {"type": "content", "content": "计算"}

data: {"type": "content", "content": "思维是..."}

data: {"type": "done"}
```

---

### 知识库相关 API (`/api/knowledge/*`)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET    | `/api/knowledge/documents` | 获取所有知识库文档列表 |
| GET    | `/api/knowledge/documents/<filename>` | 获取文档的所有知识块 |
| POST   | `/api/knowledge/upload` | 上传文档并自动向量化 |
| DELETE | `/api/knowledge/documents/<filename>` | 删除文档及其所有知识块 |
| GET    | `/api/knowledge/stats` | 获取知识库统计信息 |
| PUT    | `/api/knowledge/chunks/<id>` | 更新知识块内容 |
| DELETE | `/api/knowledge/chunks/<id>` | 删除单个知识块 |

---

### 代码分析 API (`/api/code/*`)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/code/analyze` | 代码静态分析（语法检查 + AI 评分） |
| POST | `/api/code/chat` | 针对代码的流式问答（SSE） |

---

#### 代码分析

```http
POST /api/code/analyze
Content-Type: application/json
Authorization: Bearer <token>

{
  "code": "def hello():\n    print('hello')",
  "analysis_type": "full"           // "syntax" | "logic" | "full"
}
```

**响应**:

```json
{
  "success": true,
  "score": 85,
  "level": "良好",
  "features": { "functions": 1, "lines": 2 },
  "syntax_check": { "valid": true, "errors": [] },
  "ai_analysis": { "summary": "...", "suggestions": ["..."] }
}
```

---

### 数据分析 API (`/api/analytics/*`)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/analytics/heartbeat` | 上报学习心跳（活跃时长） |
| GET  | `/api/analytics/overview` | 获取学习概览数据 |
| GET  | `/api/analytics/trend` | 获取学习趋势数据 |
| GET  | `/api/analytics/knowledge-mastery` | 获取知识点掌握度 |
| GET  | `/api/analytics/weakness` | 获取薄弱点分析 |
| GET  | `/api/analytics/students` | 获取所有学生数据（管理员） |
| GET  | `/api/analytics/report` | 获取学习报告 |
| GET  | `/api/analytics/report/pdf` | 下载 PDF 学习报告 |

---

### 管理员 API (`/api/admin/*`)

> ⚠️ 以下 API 需要管理员角色（`role=admin`）

| 方法 | 路径 | 描述 |
|------|------|------|
| GET  | `/api/admin/users` | 获取所有用户列表 |
| PUT  | `/api/admin/users/<id>/role` | 修改用户角色 |
| PUT  | `/api/admin/users/<id>/status` | 启用/禁用用户 |
| DELETE | `/api/admin/users/<id>` | 删除用户 |

---

## 🔧 开发指南

### 本地开发

#### 后端热重载

```bash
cd backend
export FLASK_ENV=development           # macOS/Linux
set FLASK_ENV=development              # Windows
python app.py                          # Flask debug 模式自动热重载
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
cd backend
python
>>> from app import app, db
>>> from models.user import User
>>> with app.app_context():
...     for u in User.query.all():
...         print(u.username, u.role)
```

#### 重置数据库

```bash
cd backend
rm data/app.db                         # 删除 SQLite 数据库
rm -rf data/chroma/                    # 删除 ChromaDB 向量数据库
python app.py                          # 重新创建所有表和向量集合
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

### Q1: 后端报错 `RuntimeError: Either 'SQLALCHEMY_DATABASE_URI' or 'SQLALCHEMY_BINDS' must be set.`

**A**: 检查 `backend/config.py` 中是否配置了 `SQLALCHEMY_DATABASE_URI`，以及 `.env` 文件是否正确放在 `backend/` 目录下。

---

### Q2: 前端无法连接后端

**A**: 检查：

1. 后端是否已启动（http://localhost:5000）
2. `app.py` 中 CORS 配置是否允许 `localhost:5173`
3. 前端 `.env` 中 `VITE_API_BASE_URL` 是否正确

---

### Q3: 登录后刷新页面就退出了

**A**: 检查：

1. `stores/user.js` 中的 `autoLogin()` 是否被调用
2. `App.vue` 中的 `onMounted()` 是否执行
3. 浏览器控制台是否有 Token 验证错误

---

### Q4: 流式输出不工作

**A**: 检查：

1. `config.py` 中 `ENABLE_STREAMING=True`
2. `OPENAI_API_KEY` 是否正确配置
3. 浏览器 Network 标签查看 SSE 连接状态

---

### Q5: ChromaDB / 向量检索相关错误

**A**: 检查：

1. `requirements.txt` 中 `chromadb` 已安装
2. `data/chroma/` 目录是否有写权限
3. 首次运行时 `sentence-transformers` 模型是否已下载完成

---

### Q6: 如何更换 AI 模型？

**A**: 修改 `backend/.env`：

```env
OPENAI_MODEL=gpt-4                              # 更换为 GPT-4
OPENAI_BASE_URL=https://your-custom-api.com/v1  # 使用兼容 OpenAI 的第三方 API
```

---

## 📝 License

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📧 联系方式

- **项目地址**: https://github.com/putianya/Python__GraduationProject
- **作者**: putianya

---

<p align="center">
  Made with ❤️ for 计算思维课程
</p>
