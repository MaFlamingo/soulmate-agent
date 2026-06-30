# SoulMate-Agent API 接口规范

Base URL: `http://localhost:8000/api`

## 1. 对话模块 `/api/chat`

### POST /chat/sessions
创建对话会话。

**Request:**
```json
{ "user_id": 1 }
```

**Response:**
```json
{
  "session_id": 1,
  "greeting_message": "嗨！👋 我是你的社交搭子助手...",
  "phase": "greeting",
  "user_id": 1
}
```

### POST /chat/sessions/{id}/messages
发送消息并获取Agent回复。

**Request:**
```json
{ "content": "我喜欢周末去徒步" }
```

**Response:**
```json
{
  "message_id": 3,
  "role": "assistant",
  "content": "山里空气确实好！你喜欢什么样的徒步路线？",
  "phase": "interest_deepening",
  "extracted_tags": [...],
  "profile_updates": {...},
  "tokens_used": 245,
  "latency_ms": 1250.5
}
```

### GET /chat/sessions/{id}
获取完整对话历史。

### GET /chat/sessions
获取用户会话列表。Query: `user_id`, `page`, `limit`

---

## 2. 画像模块 `/api/profile`

### GET /profile/me
获取当前用户画像。Query: `user_id`

### GET /profile/me/versions
获取画像版本历史。

### GET /profile/me/versions/{v}
获取特定版本快照。

### POST /profile/me/export
GDPR数据导出。

### DELETE /profile/me
删除画像数据。

---

## 3. 匹配模块 `/api/match`

### POST /match/request
触发匹配。

**Request:**
```json
{ "user_id": 1, "k": 5 }
```

**Response:**
```json
{
  "request_id": 1,
  "candidates": [
    {
      "match_id": 1,
      "candidate_id": 2,
      "candidate_name": "Bob",
      "total_score": 84.1,
      "rank": 1,
      "shared_interests": ["hiking", "coffee"],
      "score_breakdown": {
        "interest_score": 42.5,
        "personality_score": 21.6,
        "social_score": 20.0
      },
      "brief_reason": "高度匹配，共同兴趣: hiking, coffee，性格互补"
    }
  ],
  "total_candidates_searched": 8,
  "filters_applied": ["same_city_filter (filtered 2)"],
  "latency_ms": 385.2
}
```

### GET /match/results
获取匹配历史。Query: `user_id`, `limit`, `offset`

### GET /match/{match_id}
获取匹配详情（含解释+破冰话术）。

### POST /match/{match_id}/feedback
提交匹配反馈。
```json
{ "accepted": true, "feedback_text": "很匹配！" }
```

### POST /match/{match_id}/icebreaker
生成破冰话术（3种风格）。

### GET /match/{match_id}/icebreakers
获取已有的破冰话术。

---

## 4. 管理模块 `/api/admin`

### GET /admin/dashboard
获取系统监控数据。

### GET /admin/rules
列出所有匹配规则。

### POST /admin/rules
创建新规则。

### PUT /admin/rules/{id}
更新规则（热配置）。

### DELETE /admin/rules/{id}
删除规则。

### GET /admin/audit-logs
查询审计日志。Query: `user_id`, `action`, `page`, `limit`

### GET /admin/users
用户列表。Query: `page`, `limit`

### DELETE /admin/users/{id}
停用用户。

### POST /admin/reset-vector-store
重置向量存储。
