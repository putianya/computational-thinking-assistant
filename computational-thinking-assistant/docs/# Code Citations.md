# Code Citations

## License: 未知
https://github.com/hackolite/ocrflow/blob/10b6f8f8b9b1e862503a01f312fa4f9eb5cfdb09/infrastructure/apiQ/DockerfileFlask

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````
```


## License: 未知
https://github.com/hackolite/ocrflow/blob/10b6f8f8b9b1e862503a01f312fa4f9eb5cfdb09/infrastructure/apiQ/DockerfileFlask

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````
```


## License: 未知
https://github.com/hackolite/ocrflow/blob/10b6f8f8b9b1e862503a01f312fa4f9eb5cfdb09/infrastructure/apiQ/DockerfileFlask

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````
```


## License: 未知
https://github.com/hackolite/ocrflow/blob/10b6f8f8b9b1e862503a01f312fa4f9eb5cfdb09/infrastructure/apiQ/DockerfileFlask

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````
```


## License: 未知
https://github.com/hackolite/ocrflow/blob/10b6f8f8b9b1e862503a01f312fa4f9eb5cfdb09/infrastructure/apiQ/DockerfileFlask

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````
```


## License: 未知
https://github.com/hackolite/ocrflow/blob/10b6f8f8b9b1e862503a01f312fa4f9eb5cfdb09/infrastructure/apiQ/DockerfileFlask

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````
```


## License: 未知
https://github.com/hackolite/ocrflow/blob/10b6f8f8b9b1e862503a01f312fa4f9eb5cfdb09/infrastructure/apiQ/DockerfileFlask

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````
```


## License: 未知
https://github.com/Zombie1995/how-to-deploy-on-vk-cloud/blob/d40ef6fe9a99a1fe54c47186211dcc94baea229f/how-to-deploy-on-vk-cloud.tex

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```


## License: 未知
https://github.com/Zombie1995/how-to-deploy-on-vk-cloud/blob/d40ef6fe9a99a1fe54c47186211dcc94baea229f/how-to-deploy-on-vk-cloud.tex

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```


## License: 未知
https://github.com/hoijookim/bfcs-socket/blob/9bd4a0f2f0ee93318068e86515e086cc528cf1d2/Dockerfile

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
````

````yaml
```


## License: 未知
https://github.com/Zombie1995/how-to-deploy-on-vk-cloud/blob/d40ef6fe9a99a1fe54c47186211dcc94baea229f/how-to-deploy-on-vk-cloud.tex

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```


## License: 未知
https://github.com/hoijookim/bfcs-socket/blob/9bd4a0f2f0ee93318068e86515e086cc528cf1d2/Dockerfile

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
````

````yaml
```


## License: 未知
https://github.com/Zombie1995/how-to-deploy-on-vk-cloud/blob/d40ef6fe9a99a1fe54c47186211dcc94baea229f/how-to-deploy-on-vk-cloud.tex

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```


## License: 未知
https://github.com/hoijookim/bfcs-socket/blob/9bd4a0f2f0ee93318068e86515e086cc528cf1d2/Dockerfile

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
````

````yaml
```


## License: 未知
https://github.com/Zombie1995/how-to-deploy-on-vk-cloud/blob/d40ef6fe9a99a1fe54c47186211dcc94baea229f/how-to-deploy-on-vk-cloud.tex

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```


## License: 未知
https://github.com/hoijookim/bfcs-socket/blob/9bd4a0f2f0ee93318068e86515e086cc528cf1d2/Dockerfile

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
````

````yaml
```


## License: 未知
https://github.com/Zombie1995/how-to-deploy-on-vk-cloud/blob/d40ef6fe9a99a1fe54c47186211dcc94baea229f/how-to-deploy-on-vk-cloud.tex

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```


## License: 未知
https://github.com/hoijookim/bfcs-socket/blob/9bd4a0f2f0ee93318068e86515e086cc528cf1d2/Dockerfile

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
````

````yaml
```


## License: 未知
https://github.com/Zombie1995/how-to-deploy-on-vk-cloud/blob/d40ef6fe9a99a1fe54c47186211dcc94baea229f/how-to-deploy-on-vk-cloud.tex

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```


## License: 未知
https://github.com/hoijookim/bfcs-socket/blob/9bd4a0f2f0ee93318068e86515e086cc528cf1d2/Dockerfile

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
````

````yaml
```


## License: 未知
https://github.com/hoijookim/bfcs-socket/blob/9bd4a0f2f0ee93318068e86515e086cc528cf1d2/Dockerfile

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
````

````yaml
```


## License: 未知
https://github.com/Zombie1995/how-to-deploy-on-vk-cloud/blob/d40ef6fe9a99a1fe54c47186211dcc94baea229f/how-to-deploy-on-vk-cloud.tex

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
````

````yaml
```


## License: 未知
https://github.com/hoijookim/bfcs-socket/blob/9bd4a0f2f0ee93318068e86515e086cc528cf1d2/Dockerfile

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
````

````yaml
```


## License: 未知
https://github.com/Zombie1995/how-to-deploy-on-vk-cloud/blob/d40ef6fe9a99a1fe54c47186211dcc94baea229f/how-to-deploy-on-vk-cloud.tex

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
````

````yaml
```


## License: 未知
https://github.com/hoijookim/bfcs-socket/blob/9bd4a0f2f0ee93318068e86515e086cc528cf1d2/Dockerfile

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
````

````yaml
```


## License: 未知
https://github.com/Zombie1995/how-to-deploy-on-vk-cloud/blob/d40ef6fe9a99a1fe54c47186211dcc94baea229f/how-to-deploy-on-vk-cloud.tex

```
# 让他人访问你的网站 - 完整指南

根据你的项目架构，需要配置**局域网访问**或**公网访问**。

---

## 方案一：局域网访问（同一WiFi/路由器）⭐ 推荐测试用

### 适用场景
- 同学在你家里/实验室
- 连接同一个WiFi
- 演示毕设答辩

### 操作步骤

#### 1. 获取你的本机IP地址

**Windows：**
```powershell
ipconfig
```

找到 `IPv4 地址`，例如：
```
无线局域网适配器 WLAN:
   IPv4 地址 . . . . . . . . . . . . : 192.168.1.100
```

**你的本机IP：`192.168.1.100`**（记下这个）

---

#### 2. 修改后端配置允许外部访问

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\app.py
# ...existing code...

if __name__ == "__main__":
    try:
        print("=" * 50)
        print("🚀 计算思维助手后端启动中...")
        print(f"📍 环境: {config.ENV}")
        print(f"🔒 CORS: {config.CORS_ORIGINS}")
        
        # ⭐⭐⭐ 修改：监听所有网络接口，允许局域网访问 ⭐⭐⭐
        app.run(
            host="0.0.0.0",  # ← 改为 0.0.0.0（原来可能是 127.0.0.1）
            port=5000,
            debug=config.DEBUG
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        raise
````

---

#### 3. 修改前端API地址配置

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\api\auth.js
// ⭐⭐⭐ 修改：使用你的本机IP ⭐⭐⭐
const API_BASE_URL = "http://192.168.1.100:5000/api";  // ← 改为你的本机IP

// ...existing code...
````

同样修改其他API文件：
- `frontend/src/api/chat.js`
- `frontend/src/api/code.js`
- `frontend/src/api/knowledge.js`
- `frontend/src/api/analytics.js`
- `frontend/src/api/user.js`

**或者统一在一个配置文件中管理**（推荐）：

````javascript
// filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\src\config.js
// ⭐ 新建配置文件
export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://192.168.1.100:5000/api";
````

然后在所有API文件中引用：
````javascript
import { API_BASE_URL } from "../config";
// 替换原来的 const API_BASE_URL = "..."
````

---

#### 4. 修改后端CORS配置

````python
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\config.py
# ...existing code...

class Config:
    # ...existing code...
    
    # ⭐⭐⭐ 修改：允许局域网内所有IP访问 ⭐⭐⭐
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://192.168.1.100:5173",  # ← 添加你的本机IP
        "http://192.168.1.*:5173",    # ← 通配符（开发环境可用）
    ]
    
    # 或者在开发环境允许所有来源（仅测试用，不推荐生产）
    if ENV == 'development':
        CORS_ORIGINS = ["*"]  # ⚠️ 允许所有来源

# ...existing code...
````

---

#### 5. 关闭Windows防火墙 或 添加规则

**方法A：临时关闭防火墙（快速测试）**

```
控制面板 → Windows Defender 防火墙 → 启用或关闭Windows防火墙
→ 专用网络：关闭
```

**方法B：添加防火墙规则（推荐）**

```powershell
# 以管理员身份运行PowerShell
New-NetFirewallRule -DisplayName "Python Flask Port 5000" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Vite Dev Server Port 5173" -Direction Inbound -LocalPort 5173 -Protocol TCP -Action Allow
```

---

#### 6. 启动服务

**后端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\backend
python app.py
```

**前端：**
```powershell
cd s:\Python__GraduationProject\computational-thinking-assistant\frontend
npm run dev -- --host 0.0.0.0
```

**注意 `--host 0.0.0.0` 让Vite监听所有网络接口**

---

#### 7. 告诉同学访问地址

```
网址：http://192.168.1.100:5173
账号：zhangsan (你创建的学生账号)
密码：123456
```

---

## 方案二：公网访问（任何地方都能访问）

### 适用场景
- 需要远程演示
- 答辩委员会远程评审
- 跨城市访问

### 方案2.1：使用内网穿透工具（最简单）⭐

#### 推荐工具对比

| 工具 | 优点 | 缺点 | 免费额度 |
|------|------|------|---------|
| **ngrok** | 国际知名，稳定 | 国内速度慢 | 1个隧道 |
| **花生壳** | 国内快，中文界面 | 免费版限制多 | 1G/月流量 |
| **cpolar** | 国内快，简单 | 需实名认证 | 2条隧道 |
| **frp** | 开源免费，可控 | 需要有公网服务器 | 完全免费 |

#### 使用 cpolar 示例

**1. 下载安装：**
```
https://www.cpolar.com/
```

**2. 启动隧道：**
```powershell
# 后端隧道（Flask 5000端口）
cpolar http 5000

# 前端隧道（Vite 5173端口）
cpolar http 5173
```

**3. 获得公网地址：**
```
后端：https://abc123.cpolar.io → 转发到本地 5000
前端：https://xyz789.cpolar.io → 转发到本地 5173
```

**4. 修改前端API配置：**
````javascript
const API_BASE_URL = "https://abc123.cpolar.io/api";
````

**5. 分享给同学：**
```
网址：https://xyz789.cpolar.io
账号：zhangsan
密码：123456
```

---

### 方案2.2：部署到云服务器（生产级）

#### 推荐平台

| 平台 | 优点 | 新用户优惠 |
|------|------|-----------|
| **阿里云ECS** | 国内最稳定 | 新用户1核2G ￥99/年 |
| **腾讯云** | 学生机便宜 | 学生认证 ￥10/月 |
| **华为云** | 送免费试用 | 新用户300元代金券 |

#### 部署步骤（以阿里云为例）

**1. 购买服务器（Ubuntu 20.04）**

**2. 安装环境：**
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和依赖
sudo apt install python3 python3-pip python3-venv nginx -y

# 安装Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

**3. 上传代码：**
```powershell
# 在本地打包
cd s:\Python__GraduationProject\computational-thinking-assistant
tar -czf project.tar.gz backend frontend

# 上传到服务器（使用SCP或FTP）
scp project.tar.gz root@你的服务器IP:/root/
```

**4. 配置后端：**
```bash
cd /root
tar -xzf project.tar.gz
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 使用 Gunicorn 运行（生产级WSGI服务器）
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

**5. 配置前端：**
```bash
cd /root/frontend

# 修改API地址为服务器IP
# vim src/api/auth.js
# 改为 const API_BASE_URL = "http://你的服务器IP:5000/api";

# 构建生产版本
npm install
npm run build

# 使用Nginx托管
sudo mv dist /var/www/computational-thinking
```

**6. 配置Nginx：**
```nginx
# /etc/nginx/sites-available/default
server {
    listen 80;
    server_name 你的域名或IP;

    # 前端
    location / {
        root /var/www/computational-thinking;
        try_files $uri $uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo nginx -t
sudo systemctl restart nginx
```

**7. 开放防火墙端口：**
```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

**8. 配置开机自启：**
```bash
# 创建systemd服务
sudo vim /etc/systemd/system/ct-assistant.service
```

```ini
[Unit]
Description=Computational Thinking Assistant
After=network.target

[Service]
User=root
WorkingDirectory=/root/backend
Environment="PATH=/root/backend/venv/bin"
ExecStart=/root/backend/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable ct-assistant
sudo systemctl start ct-assistant
```

**9. 访问：**
```
http://你的服务器IP
```

---

## 方案三：Docker一键部署（最优雅）

### 创建 Docker 配置

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\backend\Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
````

````dockerfile
# filepath: s:\Python__GraduationProject\computational-thinking-assistant\frontend\Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
````

````yaml
```

