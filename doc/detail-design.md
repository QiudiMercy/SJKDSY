# 《带我玩》详细设计文档

> 版本：v1.0 | 日期：2026-05-23

---

## 一、项目概述

《带我玩》是一款 AI 驱动的成都一日游模拟 Web 游戏。用户扮演"导游"，从成都东站接虚拟角色**小爱**，通过自然语言对话决策行程，在真实成都 POI 数据（371K 条）基础上体验一天的游玩。系统通过 LLM Function Calling 驱动游戏状态变更，最终给出评分结算。

### 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python 3.12) |
| 数据库 | SQLite + SQLAlchemy ORM |
| AI 引擎 | OpenAI 兼容 API（Function Calling） |
| 前端 | 原生 HTML/CSS/JS |
| 地图 | 百度地图 JS API v3.0 + 静态图 API v2 |
| 配置管理 | pydantic-settings (.env) |

### 核心玩法循环

```
用户发送消息 → 小爱回复（拟人化分段 SSE流式） → 裁判裁定行为结果
→ 状态更新 → 地图刷新 → 循环 → 触发结束条件 → 评分结算
```

---

## 二、系统架构

### 2.1 分层架构

```
┌──────────────────────────────────────────┐
│  api/         路由控制层 (Controller)      │
│  仅做请求分发与参数校验，严禁业务逻辑        │
├──────────────────────────────────────────┤
│  services/    业务逻辑层 (Service)         │
│  协调 Agent、State、Model，串联业务流程     │
├──────────────────────────────────────────┤
│  agent/       智能体层 (Agent)             │
│  封装 OpenAI 调用、Function Calling 循环   │
├──────────────────────────────────────────┤
│  states/      游戏状态 (GameState)         │
│  封装运行时状态，带边界检查与持久化          │
├──────────────────────────────────────────┤
│  models/      数据持久层 (ORM)             │
│  SQLAlchemy Base → 4 张表                │
├──────────────────────────────────────────┤
│  tools/       工具层                       │
│  Function Calling 工具 + 裁判裁定 + 坐标转换│
├──────────────────────────────────────────┤
│  schemas/     DTO 层                      │
│  Pydantic 请求/响应模型，接口契约           │
├──────────────────────────────────────────┤
│  core/        基础设施                     │
│  配置(Settings) + 统一响应(success/error)  │
└──────────────────────────────────────────┘
```

### 2.2 目录结构

```
scr/takeme/
├── main.py                    # FastAPI 应用入口，lifespan 模式
├── core/
│   ├── config.py              # Settings(pydantic-settings)，从 .env 加载
│   └── response.py            # success() / error() 统一 JSONResponse
├── api/
│   ├── game_router.py         # POST /api/game/start, GET /state, POST /settle
│   ├── chat_router.py         # POST /api/chat/send (SSE), GET /history
│   ├── action_router.py       # GET /api/poi/search, POST /action/route, POST /map/image
│   └── record_router.py       # GET /api/records/list (分页)
├── services/
│   ├── game_service.py        # GameService: 创建游戏、状态查询、结算评分
│   ├── chat_service.py        # ChatService: 消息处理、历史查询
│   └── map_service.py         # MapService: POI 搜索、路线预估、静态图
├── agent/
│   ├── agent.py               # Agent(ABC) 基类 + ToolCall/LLMResponse 数据类
│   └── xiaoaiagent.py         # XiaoAiAgent: 小爱角色实现，多轮 tool call 循环
├── states/
│   └── state.py               # GameState: 状态封装、边界检查、持久化
├── models/
│   ├── database.py            # engine, SessionLocal, init_db()
│   ├── game_model.py          # Game ORM (games 表) + Base 声明
│   ├── chat_model.py          # ChatMessage ORM (chat_history 表)
│   ├── poi_model.py           # POI ORM (pois 表)
│   └── agent_definition_model.py  # AgentDefinition ORM
├── tools/
│   ├── tool.py                # Tool(ABC) 基类 + haversine_distance()
│   ├── xiaoaitools.py         # SendMsg, UpdateStatusTool, SearchPOITool, PlanRouteTool
│   ├── refereetools.py        # Referee: 裁定器 validate_and_apply()
│   └── coord_convert.py       # WGS-84 → GCJ-02 → BD-09 坐标转换
├── schemas/
│   ├── game_schema.py         # InitState, GameStateResponse, SettleRequest/Response
│   ├── chat_schema.py         # SendMessageRequest, ChatReplyResponse, MessageItem
│   └── action_schema.py       # RouteEstimateRequest, MapImageRequest, POIItem
└── message/
    └── message.py             # Message 数据类 (role, content, timestamp)
```

---

## 三、数据库设计

### 3.1 表结构总览

| 表名 | ORM 类 | 说明 | 数据量 |
|------|--------|------|--------|
| `games` | `Game` | 游戏局状态 | 动态增长 |
| `chat_history` | `ChatMessage` | 对话记录 | 动态增长 |
| `pois` | `POI` | 成都 POI 点位 | 370,998 条（CSV 导入） |
| `agent_definitions` | `AgentDefinition` | 智能体定义 | 2 条（小爱 + 裁判） |

### 3.2 `games` 表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `game_uid` | String | PK | 唯一标识，格式 `g_{12位hex}` |
| `start_time` | DateTime | 默认 utcnow | 真实开始时间 |
| `end_time` | DateTime | 可空 | 真实结束时间 |
| `current_money` | Integer | 默认 1000 | 当前余额（元） |
| `current_stamina` | Integer | 默认 100 | 体力值 0-100 |
| `current_mood` | Integer | 默认 100 | 心情值 0-100 |
| `current_fullness` | Integer | 默认 100 | 饱食度 0-100 |
| `current_time` | String | 默认 "08:00" | 游戏内时间 HH:MM |
| `current_lng` | Float | — | 当前经度（BD-09） |
| `current_lat` | Float | — | 当前纬度（BD-09） |
| `current_location_name` | String | — | 当前地点名称 |
| `is_active` | Boolean | 默认 True | 游戏是否进行中 |
| `route_summary` | Text | 可空 | 路线摘要（Python list 字符串） |
| `score` | Integer | 可空 | 最终评分 0-100 |
| `evaluation` | Text | 可空 | 评价文案 |

### 3.3 `chat_history` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer (PK, 自增) | 消息 ID |
| `game_uid` | String (FK → games) | 所属游戏 |
| `role` | String | 角色: `user` / `xiaoai` / `system` |
| `content` | Text | 消息内容 |
| `timestamp` | DateTime | 消息时间 |

### 3.4 `pois` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| `poi_uid` | String (PK) | POI 唯一标识 |
| `name` | String | 地点名称 |
| `type` | String | 类型标签（景点/餐饮/商业街...） |
| `lng` | Float | 经度（**WGS-84 存储，输出时转 BD-09**） |
| `lat` | Float | 纬度（同上） |
| `opening_hours` | String (可空) | 营业时间 |

### 3.5 `agent_definitions` 表

| 字段 | 类型 | 说明 |
|------|------|------|
| `agent_id` | String (PK) | 唯一 ID，如 `xiaoai`, `referee` |
| `role_name` | String | 角色名称 |
| `system_prompt` | Text | 角色定义（语言风格、行为规范） |
| `output_spec` | Text | 输出规范 |
| `tools_list` | JSON | 可调用的工具列表 |

---

## 四、核心模块设计

### 4.1 智能体层 (`agent/`)

#### 4.1.1 Agent 抽象基类 (`agent.py`)

```python
class Agent(ABC):
    def __init__(self, name: str, db_url: str):
        self.client = OpenAI(api_key=..., base_url=...)  # 从 settings 读取
        self.tools_lists: list[Tool] = []
        self.messages: list[Message] = []

    def _parse(response) -> LLMResponse:  # 解析 OpenAI 响应
    @abstractmethod
    def LLMChat(msg: str) -> LLMResponse: ...

@dataclass
class ToolCall:       # id, name, arguments
@dataclass
class LLMResponse:    # content, tool_calls, has_tool_calls
```

#### 4.1.2 XiaoAiAgent (`xiaoaiagent.py`)

**角色定位**：年轻女性游客，性格活泼可爱，第一次来成都。

**核心方法**：`handle_user_message(content: str) -> dict`

**处理流程**：

```
1. 添加用户消息到 self.messages
2. 更新 POI 工具中的当前位置坐标
3. 调用 LLMChat(content) → 获取 LLMResponse
4. 进入 multi-turn tool call 循环（最多 10 轮）:
   ├── 遍历 response.tool_calls
   │   ├── send_message  → 收集 segment 到 self.segments
   │   ├── update_status → 调用 Referee.validate_and_apply() → 保存 status_result
   │   ├── search_poi    → 查询数据库返回 POI 列表（BD-09 坐标）
   │   └── plan_route    → 返回路线预估（BD-09 坐标）
   ├── 将工具结果加入消息历史
   └── 调用 _continue_chat() 继续 LLM 对话
5. 返回 {"reply", "segments", "status_result"}
```

**上下文组装**：

```
[system] 小爱人设 + 【当前游戏状态】时间/余额/体力/心情/饱食度/位置
[messages] 最近 20 条历史对话
[user] 当前用户消息
→ tools=[send_message, update_status, search_poi, plan_route]
```

#### 4.1.3 裁判裁定器 (`refereetools.py`)

```python
class Referee:
    @staticmethod
    def validate_and_apply(state: GameState, updates: dict) -> dict:
```

**裁定的字段**：

| 字段 | 校验规则 | 失败处理 |
|------|---------|---------|
| `money_delta` | 余额不足时阻止 | 返回拒绝原因 |
| `stamina_delta` | 不可低于 0 | 拒绝，体力不足 |
| `mood_delta` | -100~100 | 无条件通过 |
| `fullness_delta` | -100~100 | 无条件通过 |
| `time_advance_min` | 推进后 ≥ 22:00 则截断 | 触发游戏结束 |
| `target_location_name` + `target_lng` + `target_lat` | 无条件通过 | 移动到目标位置 |

返回 `{"system_reply": string, "applied_status": dict | None}`

---

### 4.2 游戏状态管理 (`states/state.py`)

```python
class GameState:
    def __init__(self, game_uid: str, db: Session)
```

**属性访问**（均带 `_ensure_loaded()` 懒加载）：

| 属性 | 类型 | 范围 |
|------|------|------|
| `money` | int | 0~1000 |
| `stamina` | int | 0~100 |
| `mood` | int | 0~100 |
| `fullness` | int | 0~100 |
| `game_time` | str | HH:MM |
| `lng`, `lat` | float | — |
| `location_name` | str | — |
| `is_active` | bool | — |

**更新方法**：

| 方法 | 边界检查 | 游戏结束触发 |
|------|---------|------------|
| `update_money(delta)` | 最低 0 | ≤ 0 时结束 |
| `update_stamina(delta)` | 0~100 | ≤ 0 时结束 |
| `update_mood(delta)` | 0~100 | ≤ 0 时结束 |
| `update_fullness(delta)` | 0~100 | **不触发结束** |
| `advance_time(minutes)` | 最晚 22:00 | ≥ 22:00 时结束 |
| `move_to(lng, lat, name)` | 无限制 | 不触发 |

**持久化**：`save()` 方法将脏数据 commit 到数据库。

**导出**：`to_dict()` 返回 `{"time", "money", "stamina", "mood", "fullness", "location": {name, lng, lat}, "is_game_over"}`。

**辅助数据类**：`StateParams` — 定义初始值（money=1000, stamina=100, mood=100, fullness=100, time="08:00", 成都东站坐标）

---

### 4.3 工具层 (`tools/`)

#### 4.3.1 工具基类 (`tool.py`)

```python
class Tool(ABC):
    @property name: str
    @property description: str
    @property parameters: dict     # JSON Schema
    @property schema: dict         # OpenAI function schema
    @abstractmethod execute(arguments: dict) -> dict
```

附带 `haversine_distance(lng1, lat1, lng2, lat2) -> float` (km)。

#### 4.3.2 小爱工具 (`xiaoaitools.py`)

| 工具类 | name | 功能 | 依赖 |
|--------|------|------|------|
| `SendMsg` | `send_message` | 发送短消息到前端（拟人化分段） | 无 |
| `UpdateStatusTool` | `update_status` | 请求修改游戏状态，经 Referee 裁定 | Referee, GameState |
| `SearchPOITool` | `search_poi` | 搜索 POI，坐标转 BD-09 后返回 | DB Session |
| `PlanRouteTool` | `plan_route` | 路线预估（4种交通方式），坐标转 BD-09 | DB Session |

#### 4.3.3 坐标转换 (`coord_convert.py`)

```
WGS-84 → GCJ-02 → BD-09
```

- DB 存储：WGS-84（CSV 原始坐标）
- 对外输出：BD-09（百度地图坐标系）
- 转换点：`SearchPOITool.execute()`、`PlanRouteTool.execute()`、`MapService.search_poi()`、`GameService.start_new_game()`

---

### 4.4 API 路由 (`api/`)

| 方法 | 路径 | Router | 说明 |
|------|------|--------|------|
| POST | `/api/game/start` | game_router | 创建新游戏，返回 game_uid + 初始状态 |
| GET | `/api/game/state?game_uid=` | game_router | 查询当前游戏状态 |
| POST | `/api/game/settle` | game_router | 结算评分 |
| POST | `/api/chat/send` | chat_router | 发送消息，**SSE 流式**返回 |
| GET | `/api/chat/history?game_uid=` | chat_router | 查询历史消息 |
| GET | `/api/poi/search` | action_router | POI 搜索（关键词+坐标） |
| POST | `/api/action/route` | action_router | 路线预估（支持 transport_mode） |
| POST | `/api/map/image` | action_router | 生成百度地图静态图 URL |
| GET | `/api/records/list` | record_router | 历史战绩分页查询 |
| GET | `/` | main | 首页 index.html |
| GET | `/favicon.ico` | main | 网站图标 |

#### SSE 协议 (`/api/chat/send`)

```
event: message
data: {"segment": "好呀！", "seq": 1}

event: message
data: {"segment": "我们去哪里玩呢？", "seq": 2}

event: status
data: {"updates": {"money": 965, "stamina": 95, "location": {"name": "宽窄巷子", "lng": ..., "lat": ...}}, "system_reply": "打车花费35元，体力-5"}

event: done
data: {"reply": "好呀！我们去哪里玩呢？"}
```

---

### 4.5 时间流逝机制（1:100）

- **比率**：1 真实秒 = 100 游戏秒 ≈ 1.67 游戏分钟
- **计算位置**：前端 `script.js`
- **实现**：
  ```
  lastActivityTime (Date.now()) ← 游戏开始 / 上次发送消息
  发消息时: timePassedMin = floor((now - lastActivityTime) / 1000 * 100 / 60)
  POST body 携带 time_passed_min
  重置 lastActivityTime = now
  ```
- **后端处理**：`ChatService.handle_message()` 先调用 `state.advance_time(time_passed_min)`，再处理消息

---

### 4.6 评分系统 (`GameService.settle()`)

| 维度 | 权重 | 计算方式 |
|------|------|---------|
| 余额剩余 | 20% | `min(money / 1000, 1) × 20` |
| 路线丰富度 | 30% | `min(visited_poi_count / 5, 1) × 30` |
| 心情均值 | 30% | `mood / 100 × 30` |
| 时间利用率 | 20% | `(end_minutes - 480) / 840 × 20` |

**评价文案**：

| 分数 | 文案 |
|------|------|
| 90-100 | 小爱度过了非常充实的一天，你是一个合格的导游！ |
| 70-89 | 小爱玩得挺开心，但还有更好的安排空间~ |
| 50-69 | 小爱觉得还行，但有些地方可以改进哦。 |
| 30-49 | 小爱有点失望，下次要做好攻略呀。 |
| 0-29 | 小爱非常不开心，这次游玩失败了... |

### 4.7 游戏结束条件

| 条件 | 结局 | 触发位置 |
|------|------|---------|
| `game_time ≥ 22:00` | Good End | `advance_time()` |
| `money ≤ 0` | Bad End | `update_money()` |
| `stamina ≤ 0` | Bad End | `update_stamina()` |
| `mood ≤ 0` | Bad End | `update_mood()` |

注：`fullness = 0` 不触发结束，仅影响小爱的对话表现。

---

## 五、前端设计

### 5.1 视图结构

```
#view-start    → 首页：游戏简介 + 开始按钮 + 历史战绩列表
#view-game     → 主界面：顶栏状态 + 左侧地图 + 右侧搜索/聊天
#view-settle   → 结算页：评分 + 评价 + 路线回顾
```

### 5.2 全局状态变量

| 变量 | 说明 |
|------|------|
| `gameUid` | 当前游戏 UID |
| `gameState` | 缓存的最新游戏状态 |
| `map` | 百度地图实例 |
| `selectedPoi` | 当前选中的 POI |
| `isChatBusy` | AI 回复进行中 |
| `lastActivityTime` | 上次活动时间戳（计时器用） |

### 5.3 核心函数

| 函数 | 功能 |
|------|------|
| `startGame()` | POST /api/game/start → 初始化地图、加载历史 |
| `sendMessage()` | SSE 流式接收，解析 message/status/done 事件 |
| `doSearch()` | GET /api/poi/search → 渲染搜索结果 |
| `selectPoi(poi)` | 地图标注 + 显示交通按钮 |
| `fetchRoutes(mode)` | POST /api/action/route → 弹窗显示消耗 |
| `updateStatusBar(state)` | 更新顶栏 5 项数值 + 临界高亮 |
| `checkGameOver()` | 轮询状态 → 自动触发结算 |
| `doSettle()` | POST /api/game/settle → 显示结算页 |
| `loadRecords()` | GET /api/records/list → 分页渲染 |
| `panTo(lng, lat)` | 地图平移到指定坐标 |
| `addMarker(lng, lat, title, isCenter)` | 添加地图标记（蓝点=当前位置，橙水滴=POI） |

### 5.4 交通方式按钮

点击搜索结果中的 POI 后：
- 搜索面板标题旁出现 4 个圆角按钮：**步行 / 骑行 / 驾车 / 公交**
- 点击任一按钮 → 调用 `/api/action/route`（传入 `transport_mode`）→ 弹窗展示消耗预估
- 确认后自动发送"我们(方式)去(地点)吧"消息

### 5.5 地图同步

- **初始位置**：`startGame()` 后用初始坐标 init 百度地图
- **导航后同步**：SSE `status` 事件中 `updates.location` 变化时，自动 `clearMarkers()` → `addMarker()` → `panTo()`
- **选中 POI**：`selectPoi()` 时 pan 到 POI 位置并同时显示当前位置（蓝点）+ POI 位置（橙水滴）

---

## 六、数据流

### 6.1 聊天完整流程

```
[用户输入] "我们去宽窄巷子吧"
    │
    ▼
script.js: sendMessage()
    │ 计算 timePassedMin，POST /api/chat/send
    ▼
chat_router.send_message(req)
    │ 转发到 ChatService
    ▼
ChatService.handle_message(game_uid, content, time_passed_min)
    │ 1. 加载 GameState
    │ 2. 推进时间: state.advance_time(time_passed_min)
    │ 3. 保存用户消息到 chat_history
    │ 4. 加载最近 20 条历史 → 注入 XiaoAiAgent
    │ 5. agent.handle_user_message(content)
    │    ├── LLM 生成回复
    │    ├── LLM 调用 plan_route → 获取路线
    │    ├── LLM 调用 update_status → Referee 裁定 → 应用变更
    │    └── LLM 调用 send_message × N → 分段消息
    │ 6. 保存 AI 回复 + 系统裁定消息到 chat_history
    │ 7. state.save()
    │ 8. 返回 {reply, segments, system_reply, new_status}
    ▼
chat_router: StreamingResponse
    │ SSE: message → status → done
    ▼
script.js: 解析 SSE 流
    │ 逐段渲染小爱消息
    │ 状态更新 → updateStatusBar() + 地图同步
    ▼
[前端展示完成]
```

### 6.2 POI 搜索流程

```
[用户输入关键词]
    ▼
script.js: doSearch() → GET /api/poi/search?keyword=xxx&lng=...&lat=...
    ▼
MapService.search_poi()
    │ 1. 查 pois 表: name LIKE %keyword%
    │ 2. haversine 计算距离
    │ 3. wgs84_to_bd09 转换每项坐标
    │ 4. 返回 poi_list (按距离排序)
    ▼
script.js: 渲染悬浮结果列表
    │ 点击某项 → selectPoi(poi)
    │ 地图标注 → 显示交通按钮 → 用户选择方式 → fetchRoutes(mode)
    ▼
MapService.estimate_route()
    │ 返回指定交通方式的成本预估
    ▼
script.js: 弹窗展示 → 用户确认 → sendMessage("我们XX去YY吧")
```

---

## 七、配置清单

### `.env` 文件

| 键 | 说明 | 示例值 |
|----|------|--------|
| `LLM_API_KEY` | LLM API 密钥 | `sk-...` |
| `LLM_BASE_URL` | LLM API 地址 | `https://api.openai.com/v1` |
| `LLM_MODEL` | 模型名称 | `deepseek-v4-flash` |
| `MAP_API_KEY` | 百度地图 API Key | `5b...` |
| `DATABASE_URL` | 数据库连接（自动计算绝对路径） | `sqlite:///.../takeme.db` |

### 游戏初始参数（`Settings` 类）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `init_money` | 1000 | 初始余额 |
| `init_stamina` | 100 | 初始体力 |
| `init_mood` | 100 | 初始心情 |
| `init_fullness` | 100 | 初始饱食度 |
| `init_time` | "08:00" | 游戏起始时间 |
| `end_time` | "22:00" | 游戏结束时间 |
| `init_lng` | 104.148151 | 成都东站 WGS-84 经度 |
| `init_lat` | 30.634674 | 成都东站 WGS-84 纬度 |
| `init_location_name` | "成都东站" | 起始位置名 |

---

## 八、接口契约规范

所有 API 返回统一格式：

```json
{
  "code": 200,    // 200 成功, 400 参数错误
  "msg": "success",
  "data": { ... }
}
```

所有返回值通过 `core/response.py` 的 `success(data, msg)` / `error(code, msg)` 构建。

---

## 九、启动方式

```bash
cd scr/takeme
python main.py
# → http://127.0.0.1:8000
```

依赖：`fastapi`, `uvicorn`, `sqlalchemy`, `openai`, `pydantic-settings`

服务启动时 `lifespan` 回调自动执行 `init_db()`：
1. 创建所有表（`Base.metadata.create_all`）
2. 如 `pois` 表为空，插入 8 条 mock POI
3. 如 `agent_definitions` 表为空，插入小爱 + 裁判定义