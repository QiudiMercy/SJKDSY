# 《带我玩》Web游戏 - 后端系统架构设计

基于项目《计划书》与《接口文档》，系统后端建议采用经典且契合 AI Agent 开发的分层架构设计（Controller - Service - Agent - Model）。此架构便于独立维护基础业务逻辑与大模型 Function Calling（工具调用）的结合。

## 目录结构树

```text
backend/
├── main.py                 # 程序入口 (如 FastAPI/Flask 应用初始化)
├── core/                   # 核心配置层
│   ├── config.py           # 环境变量与全局配置 (数据库配置, LLM Key)
│   └── response.py         # 统一JSON返回结构封装体 ({code, msg, data})
├── api/                    # 路由控制层 (Controller - 对应接口文档)
│   ├── game_router.py      # 模块一：游戏状态API接口
│   ├── chat_router.py      # 模块二：AI聊天互动API接口
│   ├── action_router.py    # 模块三：地图与行动决策API接口
│   └── record_router.py    # 模块四：战绩记录API接口
├── services/               # 业务逻辑层 (Service - 处理具体逻辑)
│   ├── game_service.py     # 游戏生命周期管理与数值计算
│   ├── chat_service.py     # 聊天历史持久化与状态更新协同
│   └── map_service.py      # POI数据库查询与多流派路线耗时计算
├── agent/                  # 智能体核心层 (Agent - 对应计划书中"智能体")
│   ├── xiaoai_bot.py       # 小爱Agent主体类 (Prompt与上下文管理)
│   ├── tools.py            # 注册给LLM的Function Calling工具箱
│   └── status_interceptor.py# 系统裁定拦截器 (处理LLM生成的变动数值)
├── models/                 # 数据库模型层 (Model - 对应计划书"数据库存储")
│   ├── game_model.py       # 后台战绩表与游玩状态实体类
│   ├── chat_model.py       # 对话历史历史记录表实体类
│   └── poi_model.py        # 成都本地点位表(地理空间字段)实体类
└── schemas/                # 数据交互检验层 (DTO/请求验证)
    ├── game_schema.py      # InitState, SettleRequest 等
    ├── chat_schema.py      # SendMessageRequest, ChatReplyResponse 等
    └── action_schema.py    # RouteEstimateRequest 等
```

---

## 核心文件与其核心类/方法说明

### 1. `api/` (路由控制层)
直接映射《接口文档》暴露的4个模块RESTful节点，只做请求分发，不处理重度业务。
* **`api/game_router.py`**
  * `start_game()`: 处理 `POST /api/game/start`
  * `get_game_state()`: 处理 `GET /api/game/state`
  * `settle_game()`: 处理 `POST /api/game/settle`
* **`api/chat_router.py`**
  * `send_chat()`: 处理 `POST /api/chat/send` (可能以SSE流式下发)
  * `get_history()`: 处理 `GET /api/chat/history`
* **`api/action_router.py`**
  * `search_poi()`: 处理 `GET /api/poi/search`
  * `plan_route()`: 处理 `POST /api/action/route`
* **`api/record_router.py`**
  * `get_records()`: 处理 `GET /api/records/list`

### 2. `services/` (业务逻辑层)
负责承上(Router)启下(Model)。
* **`GameService`** (位于 `game_service.py`)
  * `create_new_game()`: 拼装游戏初始状态对象（time 08:00, money 1000等），写入数据库并生成唯一 `game_uid`。
  * `check_game_over()`: 校验单一游戏是否越界（金钱为0、22:00等），主动触发 Bad End 或 Good End。
  * `calculate_score()`: 关卡结算算法，基于保留资金、心情和体力值折算总评分。
* **`ChatService`** (位于 `chat_service.py`)
  * `process_user_message()`: 调度 `XiaoaiAgent`，将获得的回复再调度 `save_message()` 进行存储，并修改当前游戏状态参数。
  * `fetch_history()`: 按时间线查询单局通信的所有历史(User/Xiaoai/System)。
* **`MapService`** (位于 `map_service.py`)
  * `search_nearby_pois(lng, lat, keyword)`: 通过基于空间索引的数据库测算，返回 POI 数据。
  * `estimate_route_cost(method, target_poi)`: 生成交通/体力/心情的影响权重预估列表。

### 3. `agent/` (智能体AI核心处理)
《计划书》说明需要支持Agent主动调用工具来更新游戏要素。
* **`XiaoaiAgent`** (位于 `xiaoai_bot.py`)
  * `generate_reply(user_input, game_state, history)`: 向大语言模型组装系统人设 Prompt，传入小爱当前血条、状态，获取自然语言回应和潜在的函数调用。
* **`AgentTools`** (位于 `tools.py`)
  * 提供给 Agent 决策使用的数据与能力基类（Function Calling定义）：
  * `tool_update_game_status(...)`: 如果当前聊天发生矛盾(扣心情)、或者聊天愉快(加心情)、决定逛街(扣体力)，Agent有权调用此工具强行改写系统变量。
  * `tool_search_chengdu_poi(...)`: 提供给 Agent 用于在回答用户“附近有啥好吃的”时自行查询。
* **`StatusInterceptor`** (位于 `status_interceptor.py`)
  * `parse_system_verdict()`: 将大模型调用的 `tool_update_game_status` 被动转化构造为向前端输出的 `is_system_reply` 以及 `system_reply` 裁定说明。 

### 4. `models/` (数据ORM持久层)
基于《计划书》的“数据库存储”设计ORM模型。
* **`GameRecordModel`** (位于 `game_model.py`)
  * 核心字段: `game_uid`, `start_time` (现实时间), `remain_money` (最后余额), `score` (评级), `route_summary` (走过的路径JSON)。
* **`ChatMessageModel`** (位于 `chat_model.py`)
  * 核心字段: `msg_id`, `game_uid`, `role` (user 代表玩家, xiaoai 代表主控, system 代表状态更新), `content`, `game_time` (游戏内时刻)。
* **`POIModel`** (位于 `poi_model.py`)
  * 核心字段: `poi_uid`, `name`, `type`, `lng`, `lat`, `business_hours`。

### 5. `core/response.py` (统一结构体)
确保遵循文档规范。
* **`ResponseHelper`**
  * `success(data, msg="success")`: 自动化打入 `{"code": 200, "msg": msg, "data": data}`
  * `bad_request(msg)`: 格式化包裹400错误。