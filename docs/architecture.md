# SoulMate-Agent 系统架构文档

## 1. 架构概览

SoulMate-Agent 采用三层协作架构：API网关 → 服务编排层 → Agent层 → 基础设施层。

```
┌─────────────────────────────────────────────────────┐
│                   CLIENT (React)                      │
│   ChatPage │ MatchPage │ ProfilePage │ AdminPage     │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP/REST
┌──────────────────────▼──────────────────────────────┐
│              API GATEWAY (FastAPI)                    │
│  /api/chat/*  /api/match/*  /api/profile/*  /admin/* │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                SERVICE LAYER                          │
│  ChatService │ MatchingService │ FacilitationService │
│  ProfileService │ AdminService                       │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                 AGENT LAYER                           │
│  ProfileMiningAgent │ MatchingDecisionAgent           │
│  FacilitationAgent                                   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              CORE INFRASTRUCTURE                      │
│  LLM Adapter │ ChromaDB │ SQLite │ Rule Engine       │
└─────────────────────────────────────────────────────┘
```

## 2. Agent设计与通信协议

### 2.1 BaseAgent

所有Agent继承自 `BaseAgent` 抽象类，通过 `AgentRequest/AgentResponse` 进行通信：

```python
class AgentRequest:
    request_id: str   # UUID追踪
    caller: str       # 调用方标识
    payload: dict     # 业务数据
    metadata: dict    # 追踪上下文

class AgentResponse:
    request_id: str
    status: str       # success/error/degraded
    payload: dict
    tokens_used: int
    latency_ms: float
```

### 2.2 Agent职责

**ProfileMiningAgent** (画像采集):
- 对话状态机管理 (7个阶段)
- 隐式偏好提取 (基于LLM的结构化输出)
- 性格特征分析 (大五人格简化维度)
- 画像增量更新与版本控制

**MatchingDecisionAgent** (匹配决策):
- 画像向量化 → ChromaDB
- 余弦相似度 + 加权多维评分
- 规则引擎硬约束过滤
- MMR多样性重排

**FacilitationAgent** (撮合辅助):
- 3风格破冰话术生成
- 可解释匹配理由生成
- 具体活动建议推荐

## 3. 数据流

### 对话流程
```
User Message → ChatService → ProfileMiningAgent
  ├→ ConversationManager (LLM: 生成回复)
  └→ ProfileExtractor (LLM: 提取画像标签)
      └→ ProfileService (更新画像 + 版本快照)
          └→ MatchingDecisionAgent (更新ChromaDB向量)
```

### 匹配流程
```
Match Request → MatchingService → MatchingDecisionAgent
  ├→ ChromaDB (向量相似度搜索)
  ├→ RuleEngine (硬约束过滤)
  ├→ Scorer (加权多维评分)
  └→ MMR (多样性重排)
      └→ Top-K 候选人列表
```

### 破冰流程
```
Icebreaker Request → MatchingService → FacilitationAgent
  ├→ MatchExplainer (LLM: 生成匹配理由)
  ├→ IcebreakerGenerator (LLM: 生成破冰话术 ×3)
  └→ ActivitySuggester (LLM: 推荐活动)
```

## 4. 数据库设计

8张核心表：users, profiles, profile_versions, conversations, messages, matches, match_feedback, icebreak_messages, matching_rules, audit_logs

详见 `backend/app/models/` 目录下的ORM定义。

## 5. 关键技术决策

| 决策 | 理由 | 权衡 |
|------|------|------|
| 单体部署 | 原型快速开发 | 生产需拆分微服务 |
| ChromaDB | 零配置嵌入 | 百万级需迁移Milvus |
| SQLite | 无需外部DB | 并发受限 |
| 直接调用协议 | 简单可追踪 | 需消息队列解耦 |
| OpenAI兼容API | 多模型切换 | — |

## 6. 扩展点

- **模型切换**: 通过 `LLMAdapterFactory` 注册新provider
- **新场景**: 通过配置文件注册新场景的prompt变体和规则
- **规则热更新**: 修改 `matching_rules` 表即可生效，无需重启
