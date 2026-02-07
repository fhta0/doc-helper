# 文心雕龙·AI (DocAI) - 文档格式检查系统

基于 FastAPI + Vue 3 的文档格式检查 Web 应用，支持 .docx 文档的格式检查和自动修订。

## 功能特性

- 用户注册/登录（用户名+密码）
- 支持 .docx 文档上传
- 格式检查（页面设置、字体、段落、标题、图表等）
- **AI 内容检查**（错别字、交叉引用验证）
- **自动修订功能**（生成带修订标记的 Word 文档）
- 检查报告展示
- 每月3次免费检查
- 微信支付集成（购买检查次数）
- 访客模式（无需注册即可检查）

## 技术栈

### 后端
- FastAPI (Python 3.9+)
- MySQL 5.7+ / SQLite
- python-docx (文档解析)
- SQLAlchemy (ORM)
- OpenAI-compatible API (支持 DeepSeek、OpenAI 等)

### 前端
- Vue 3 (Composition API)
- Vite
- Element Plus
- Pinia (状态管理)
- Vue Router
- Axios
- TailwindCSS

### 部署
- Docker / Docker Compose
- Nginx (反向代理)

## 快速开始 (Docker 部署)

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+
- MySQL 5.7+ (外部或容器)

### 1. 克隆项目

```bash
git clone <repository-url>
cd doc-helper
```

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
cp backend/.env.example .env
```

编辑 `.env` 文件，配置以下关键参数：

```bash
# 数据库配置
DATABASE_URL=mysql+pymysql://root:password@your-host:3306/doc_ai

# JWT 密钥（生产环境请使用强随机密钥）
SECRET_KEY=your-secret-key-change-this-in-production

# AI 服务配置（支持 DeepSeek、OpenAI 等）
AI_BASE_URL=https://api.deepseek.com/v1
AI_API_KEY=your-api-key
AI_MODEL=deepseek-chat

# 微信支付（可选，如不需要支付功能可留空）
WECHAT_MCHID=your_mchid
WECHAT_APPID=your_appid
WECHAT_APIV3_KEY=your_apiv3_key
# ... 其他微信支付配置
```

### 3. 准备 SSL 证书（可选）

如需 HTTPS 支持，将证书文件放置在 `cert/` 目录：

```
cert/
├── star_secsmarts_com.crt
└── star_secsmarts_com.key
```

如不需要 HTTPS，可修改 `nginx/nginx.conf` 移除 HTTPS 配置。

### 4. 启动服务

```bash
# 构建并启动所有服务
docker-compose up --build -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 5. 初始化数据库

```bash
# 进入后端容器
docker-compose exec backend bash

# 初始化数据库
python init_db.py

# 退出容器
exit
```

### 6. 访问应用

- 前端：http://localhost:8080
- API 文档：http://localhost:8080/docs
- 后端 API：http://localhost:8080/api/

## 开发模式

### 后端开发

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python init_db.py

# 启动开发服务器
python main.py
# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端服务运行在 http://localhost:8000

### 前端开发

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端服务运行在 http://localhost:5173，会自动代理 `/api` 请求到后端。

## 环境变量说明

### 必需配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | MySQL 连接字符串 | - |
| `SECRET_KEY` | JWT 签名密钥 | - |

### AI 配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `AI_BASE_URL` | AI API 基础 URL | `https://api.openai.com/v1` |
| `AI_API_KEY` | AI API 密钥 | - |
| `AI_MODEL` | AI 模型名称 | `gpt-4o-mini` |
| `AI_TIMEOUT` | AI 请求超时（秒） | `60` |

### 上传配置

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `MAX_FILE_SIZE_GUEST` | 访客最大文件大小（字节） | `10485760` (10MB) |
| `MAX_FILE_SIZE_AUTHENTICATED` | 登录用户最大文件大小（字节） | `104857600` (100MB) |

### 微信支付配置（可选）

| 变量名 | 说明 |
|--------|------|
| `WECHAT_MCHID` | 微信支付商户号 |
| `WECHAT_APPID` | 微信应用ID |
| `WECHAT_APIV3_KEY` | APIv3 密钥 |
| `WECHAT_CERT_SERIAL_NO` | 商户证书序列号 |
| `WECHAT_NOTIFY_URL` | 支付回调地址 |

## 项目结构

```
doc-helper/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务逻辑
│   │   └── utils/          # 工具函数
│   ├── tests/              # 测试文件
│   ├── main.py             # 应用入口
│   ├── init_db.py          # 数据库初始化
│   ├── Dockerfile          # Docker 镜像
│   └── requirements.txt    # Python 依赖
├── frontend/               # 前端服务
│   ├── src/
│   │   ├── api/           # API 客户端
│   │   ├── components/    # 组件
│   │   ├── router/        # 路由
│   │   ├── stores/        # 状态管理
│   │   └── views/         # 页面
│   ├── Dockerfile         # Docker 镜像
│   └── package.json       # Node 依赖
├── nginx/                  # Nginx 配置
│   └── nginx.conf
├── cert/                   # SSL 证书（可选）
├── uploads/                # 上传文件目录
└── docker-compose.yml      # Docker 编排
```

## Docker 部署架构

```
                    ┌─────────────────┐
                    │   Nginx :80/443 │
                    │   (Frontend)    │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
        ┌───────▼────────┐      ┌────────▼─────────┐
        │  Frontend :80  │      │  Backend :8000   │
        │  (Vue + Nginx) │      │  (FastAPI)       │
        └────────────────┘      └────────┬─────────┘
                                          │
                                    ┌─────▼─────┐
                                    │  MySQL    │
                                    │  (外部)   │
                                    └───────────┘
```

### 服务说明

- **Frontend**：Vue 3 静态文件 + Nginx，暴露端口 80/443
- **Backend**：FastAPI 应用，容器内部端口 8000
- **Nginx**：反向代理，统一入口，处理 SSL 终止

### 端口映射

| 端口 | 说明 |
|------|------|
| 8080 | HTTP 访问端口 |
| 443 | HTTPS 访问端口 |
| 8000 | 后端 API（仅容器内部） |

## 常见问题

### 1. 数据库连接失败

检查 `DATABASE_URL` 配置是否正确，确保 MySQL 服务可访问。

### 2. AI 检查不工作

检查 `AI_API_KEY` 和 `AI_BASE_URL` 配置，确保网络可访问 AI 服务。

### 3. 文件上传失败

检查 Nginx 配置中的 `client_max_body_size` 和环境变量中的文件大小限制。

### 4. 容器无法启动

```bash
# 查看容器日志
docker-compose logs backend
docker-compose logs frontend

# 重新构建镜像
docker-compose build --no-cache
```

### 5. SSL 证书问题

如不需要 HTTPS，可修改 `nginx/nginx.conf`，移除 HTTPS server 块。

## 测试

### 后端测试

```bash
cd backend
pytest                   # 运行所有测试
pytest --cov=app        # 带覆盖率
pytest -m unit          # 单元测试
```

### 前端测试

```bash
cd frontend
npm run test            # 运行测试
npm run test:coverage   # 带覆盖率
```

## License

MIT License
