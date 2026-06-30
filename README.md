# SoulMate-Agent — 基于多智能体的对话式社交匹配系统

> 零表单、全对话：用户只需与AI聊天，系统自动构建画像并智能匹配搭子。

## 系统概述

SoulMate-Agent 采用多Agent协作架构，包含三个核心智能体：

1. **画像采集Agent** (Profile Mining Agent) — 多轮对话中隐式提取用户偏好与性格特征
2. **匹配决策Agent** (Matching Decision Agent) — 向量相似度 + 规则引擎的智能匹配
3. **撮合辅助Agent** (Facilitation Agent) — 生成个性化破冰话术与活动建议

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | Python / FastAPI |
| LLM适配 | OpenAI兼容API (支持GPT-4, DeepSeek, Qwen, Ollama) |
| 向量数据库 | ChromaDB |
| 关系数据库 | SQLite (可切换PostgreSQL) |
| Agent框架 | 自研轻量级多Agent协作 |
| 前端 | React 18 + TypeScript + Vite + Tailwind CSS |
| 部署 | Docker Compose |

## 快速开始

### 前置条件
- Python 3.11+
- Node.js 18+
- OpenAI API Key (或兼容API)

### 1. 环境配置

```bash
cp .env.example .env
# 编辑 .env 文件，填入 LLM_API_KEY
```

### 2. 安装依赖

```bash
# 后端
cd backend
pip install -r requirements.txt

# 前端
cd frontend
npm install
```

### 3. 启动服务

```bash
# 终端1: 启动后端 (默认端口8000)
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 终端2: 启动前端 (默认端口5173)
cd frontend
npm run dev
```

### 4. 访问系统

- 对话界面: http://localhost:5173/
- API文档: http://localhost:8000/docs
- 管理后台: http://localhost:5173/admin

### Docker 部署

```bash
docker-compose up --build
```

## 项目结构

```
soulmate-agent/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI 应用入口
│   │   ├── config.py             # 环境配置
│   │   ├── core/                 # 基础设施 (DB, LLM适配器, 向量存储)
│   │   ├── models/               # SQLAlchemy ORM 数据模型
│   │   ├── schemas/              # Pydantic 请求/响应模型
│   │   ├── agents/               # 三核心Agent实现
│   │   ├── prompts/              # LLM Prompt 模板
│   │   ├── services/             # 业务编排层
│   │   ├── api/                  # FastAPI 路由处理器
│   │   ├── engine/               # 算法引擎 (规则, 评分, MMR)
│   │   └── middleware/           # 审计中间件, 异常处理
│   ├── tests/                    # 测试
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/                # ChatPage, MatchPage, ProfilePage, AdminPage
│   │   ├── components/           # Chat, Profile, Match, Admin 组件
│   │   ├── hooks/                # useChat, useProfile, useMatch
│   │   ├── api/                  # Axios API 客户端
│   │   └── types/                # TypeScript 类型定义
│   └── package.json
├── docs/                         # 项目文档
├── docker-compose.yml
└── .env.example
```

## 使用流程

1. **对话采集** — 在聊天界面与AI自然对话，系统自动提取兴趣标签和性格特征
2. **智能匹配** — 点击"开始匹配"，系统基于画像向量 + 规则引擎返回Top-5候选人
3. **查看详情** — 查看匹配得分的详细分解和推荐理由
4. **破冰沟通** — 选择幽默/正式/温暖风格的破冰话术，附带活动建议

## API 概览

- `POST /api/chat/sessions` — 创建对话会话
- `POST /api/chat/sessions/{id}/messages` — 发送消息
- `GET /api/profile/me` — 获取画像
- `POST /api/match/request` — 触发匹配
- `GET /api/match/{id}` — 匹配详情
- `POST /api/match/{id}/icebreaker` — 生成破冰话术
- `GET /api/admin/dashboard` — 管理仪表盘

完整API文档: http://localhost:8000/docs

## 运行测试

```bash
cd backend
python -m pytest tests/ -v
```
