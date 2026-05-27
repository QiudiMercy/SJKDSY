# 🗺️ 《带我玩》(Take Me Out) — 成都趣味旅行社交大模型游戏

《带我玩》是一款将**大语言模型智能体（LLM Agents）**与**地理位置信息服务（GIS）**深度结合的创新数据库课程设计项目。在游戏中，玩家扮演一名富有经验的“本地导游”，带领活泼可爱的“外地虚拟游客小爱”在成都展开一场奇妙的旅行。

本项目完全遵循“数据库技术与应用”课程设计的高标准规范，**彻底剥离了 ORM 框架，全部采用手写原生 SQL 语句完成所有数据交互**，并结合 FastAPI 构建了极具美学视觉的高性能单页 Web 应用。

---

## 🌟 核心技术亮点

1. **纯手写原生 SQL 与参数化防御**：
   * 零 ORM 依赖：全站数据操作 100% 由原生 SQLite3 参数化 SQL 语句驱动，保证了最底层的数据库操作透明度。
   * SQL 注入防御：全量 SQL 语句采用参数占位符 `?` 进行查询（而非直接字符串拼接），从根本上杜绝了 SQL 注入漏洞，并保证了带有特殊字符的地理点位名称能够安全读写。
2. **双智能体（Dual-Agent）架构协同**：
   * **游客智能体小爱 (XiaoAiAgent)**：具备活泼可爱的性格模型，自动管理聊天打字机分段发送（控制在 10-20 字/条），并能够调用 POI 搜索、路径规划等工具主动探索。
   * **系统裁判智能体 (RefereeAgent)**：默默监听对话，在必要时刻（如移动、更新状态、购买道具）以零概率多余废话的机制触发“系统裁决”，动态调整游戏数值，保证系统极高的契合度。
3. **智能 POI 边界范围搜索与距离排序**：
   * 使用 **Bounding Box（经纬度范围盒过滤）** 配合 SQLite 原生参数化 LIKE 检索，保证在 37 万行巨量成都 POI 数据下实现毫秒级的高性能查询。
   * 采用标准 **Haversine 算法** 动态计算两点球面距离并按最近降序排序，实现真正实用的位置推荐。
4. **精密的双时钟运行与熔断机制**：
   * **时间流逝同步**：现实中的 `1 秒` 等同于游戏世界的 `84 秒`。小爱的行动和对话会根据移动距离、交通方式和聊天消耗时间智能累加游戏时间。
   * **健康熔断系统**：游戏时间跨越晚上 `22:00` 时，系统将自动熔断强制进入本日结算，并结合手写 SQL 归纳总结今日旅行路线，给出评分与综合考评。
5. **百度地图坐标纠偏算法集成**：
   * 从底层数据库加载的原始 POI 经纬度属于 WGS-84/GCJ-02 坐标系。系统在前端地图渲染时，自动在服务层集成了 **BD-09 坐标纠偏转换算法**，确保小爱的头像和旅行轨迹在百度地图底图上精确定位，无任何偏移误差。

---

## 🗄️ 数据库关系表结构设计

系统底层数据库 `takeme.db` 包含以下 4 张核心关系表：

### 1. 游戏实例表 (`games`)
存储玩家每局游戏的实时属性与游玩状态。
```sql
CREATE TABLE games (
    game_uid VARCHAR(64) PRIMARY KEY,       -- 游戏唯一主键 (UUID)
    score INTEGER DEFAULT 0,                 -- 战绩评分
    current_time DATETIME,                   -- 游戏内当前虚拟时间
    current_money INTEGER DEFAULT 1000,      -- 玩家金币余额
    current_mood INTEGER DEFAULT 100,        -- 小爱心情值 (0 - 100)
    current_stamina INTEGER DEFAULT 100,     -- 小爱体力值 (0 - 100)
    current_fullness INTEGER DEFAULT 80,     -- 小爱饱食度 (0 - 100)
    current_lng DOUBLE,                      -- 当前经度 (BD-09)
    current_lat DOUBLE,                      -- 当前纬度 (BD-09)
    current_location VARCHAR(255),           -- 当前所在 POI 名称
    route_summary TEXT,                      -- 总结路线轨迹
    status VARCHAR(20) DEFAULT 'playing',    -- 游戏状态 (playing / finished)
    end_time DATETIME                        -- 游戏结束现实时间
);
```

### 2. 聊天历史表 (`chat_history`)
流式存储游戏内的所有对话信息，支持以时间顺序回溯。
```sql
CREATE TABLE chat_history (
    id VARCHAR(64) PRIMARY KEY,             -- 消息 ID
    game_uid VARCHAR(64),                    -- 外键关联 games.game_uid
    role VARCHAR(20),                        -- 消息发送者角色 (user / xiaoai / system)
    content TEXT,                            -- 消息内容
    timestamp DATETIME                       -- 发送时间
);
```

### 3. 智能体提示词表 (`agent_definitions`)
实现智能体人设配置的持久化，摆脱代码硬编码。
```sql
CREATE TABLE agent_definitions (
    agent_id VARCHAR(50) PRIMARY KEY,        -- 智能体身份标识 (xiaoai / referee)
    role_name VARCHAR(50),                   -- 角色名称
    system_prompt TEXT                       -- 大模型系统级提示词配置
);
```

### 4. 成都全量 POI 基础信息表 (`poi`)
预装入的 370,998 条成都全量兴趣点信息表。
```sql
CREATE TABLE poi (
    poi_uid VARCHAR(64) PRIMARY KEY,         -- POI 全局唯一 ID
    name VARCHAR(255),                       -- 地点/店铺名称
    type VARCHAR(100),                       -- 分类标签 (餐饮 / 风景名胜等)
    lng DOUBLE,                              -- WGS-84/GCJ-02 经度
    lat DOUBLE                               -- WGS-84/GCJ-02 纬度
);
```

---

## 📂 项目模块结构树

```text
SJKDSY/                       # 项目根目录
├── .env                      # 环境变量 (配置 LLM 密钥与底层 API 常量)
├── .gitignore                # Git 忽略配置
├── pyproject.toml            # 现代依赖声明元数据
├── requirements.txt          # 项目依赖列表 (FastAPI, Uvicorn, SQLite, OpenAI 等)
├── index.html                # 游戏前端 HTML5 单页
├── style.css                 # 游戏前端 CSS3 样式表 (HSL 动态美学)
├── script.js                 # 游戏前端 JS 逻辑引擎
├── uipict.png                # 地图遮罩等 UI 资产
├── favicon.svg               # 项目图标
├── iconfont.css / iconfont.js# 矢量图标库资产
├── takeme.db                 # SQLite 核心预装载数据库 (36.5 MB)
├── 成都市_县.geojson         # 成都行政边界数据
│
├── scr/                      # 核心后端代码库 (纯原生 SQL 驱动)
│   └── takeme/
│       ├── api/              # 接口路由层 (game_router, chat_router, etc.)
│       ├── services/         # 业务服务层 (chat_service, game_service, map_service)
│       ├── agent/            # 智能体逻辑 (xiaoaiagent, refereeagent)
│       ├── models/           # 数据库配置与手写 SQL 基类封装
│       ├── schemas/          # Pydantic 传输模型校验
│       ├── states/           # 参数化 GameState 状态机管理
│       ├── tools/            # 智能体工具箱 (Haversine 测距、BD-09 坐标转换等)
│       ├── core/             # 全局环境配置与 DB 实例管理
│       ├── message/          # 统一消息定义
│       └── main.py           # 后端服务唯一启动入口
│
├── scripts/                  # 辅助开发工具与初始化脚本归档
│   └── import_poi.py         # 智能适配的 POI 批量解析导入脚本 (支持 CSV 逆向检测)
│
└── doc/                      # 深度文档归口
    ├── demand.md             # 需求规格说明书
    ├── detail-design.md      # 关系数据库与表结构详细设计
    ├── progress.md           # 模块开发进度与架构对齐记录
    ├── analyst.md            # 开发演进与完整性分析报告
    └── 百度地图_API_DOC.md   # 第三方地图服务对接规约
```

---

## 🚀 快速启动指南

### 1. 硬件与软件环境准备
* 系统要求：Windows / macOS / Linux。
* Python 环境：推荐使用 **Python 3.12+**。

### 2. 依赖项安装
在项目根目录下打开命令行终端，执行以下命令安装运行所需的第三方 Python 库：
```bash
pip install -r requirements.txt
```

### 3. 环境变量配置
在项目根目录下，确保存在一个命名为 `.env` 的配置文件，并填入您的 OpenAI 兼容平台 API Key 及大模型信息：
```ini
LLM_API_KEY="您的 MaaS 平台 API Key"
LLM_BASE_URL="https://compatible-mode.v1.xxx.com/v1" # 接口的基础 URL
LLM_MODEL="deepseek-v4-flash"                        # 拟使用的大模型型号
```

### 4. 启动后端服务器
在项目根目录下，运行后端主入口文件（默认端口为 `8000`）：
```bash
python scr/takeme/main.py
```
若需要确保中文控制台无乱码，推荐以 UTF-8 方式运行：
```bash
python -X utf8 scr/takeme/main.py
```

### 5. 游玩体验
服务器拉起后，在浏览器中输入：
👉 **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

即可瞬间开启极致丝滑的《带我玩》成都大模型探险之旅！
