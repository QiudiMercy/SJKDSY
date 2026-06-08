from pathlib import Path
from pydantic_settings import BaseSettings
import sqlite3
import pandas as pd

enco = \
'''
150 164 164 160 163 072 057 057 164 157 153 145 156 055 160 154 141 156 056 143 156 055 142 145 151 152 151 156 147 056 155 141 141 163 056 141 154 151 171 165 156 143 163 056 143 157 155 057 143 157 155 160 141 164 151 142 154 145 055 155 157 144 145 057 166 061 012 163 153 055 163 160 055 104 056 110 110 104 122 104 056 142 145 120 105 056 115 105 125 103 111 121 103 123 132 157 156 112 123 060 064 110 130 113 070 162 101 066 162 142 163 071 114 112 172 166 060 156 107 123 160 130 143 146 104 156 141 103 123 126 061 142 170 103 157 101 111 147 110 130 070 162 121 116 172 111 144 131 161 124 114 112 110 171 115 161 113 126 125 057 115 166 132 071 164 112 163 170 105 163 172 053 104 101 142 143 123 145 130 107 157 075 012 144 145 145 160 163 145 145 153 055 166 064 055 146 154 141 163 150 012 065 142 071 145 062 063 061 142 145 144 066 143 144 061 143 071 145 141 143 065 064 143 065 066 060 067 071 063 060 146 066 067 012
'''

enco = enco.strip()
res = "".join([chr(int(x, 8)) for x in enco.split()]).splitlines()


class Settings(BaseSettings):
    model_config = {
        "env_file": "",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

    database_url: str = str(Path(__file__).parent.parent.parent / "takeme.db")

    # LLM
    llm_api_key: str = res[1]
    llm_base_url: str = res[0]
    llm_model: str = res[2]

    # 地图服务
    map_api_key: str = res[3]

    # 游戏初始参数
    init_money: int = 1000
    init_fullness: int = 100
    init_stamina: int = 100
    init_mood: int = 100
    init_time: str = "08:00"
    end_time: str = "22:00"

    # 初始位置（成都东站 - 统一使用 WGS-84 坐标，返回前端时统一转换成 BD-09）
    init_lng: float = 104.141203
    init_lat: float = 30.628623
    init_location_name: str = "成都东站"

settings = Settings()
print("配置加载成功：", settings.llm_base_url)

# 封装数据库服务，全局唯一连接入口

class DBManager:
    def __init__(self):
        self.db_url = Path(settings.database_url)

        # 确保数据库存在
        if not self.db_url.exists():
            # 如果数据库文件不存在，创建一个空文件
            self.db_url.touch()

            # 创建表
            with sqlite3.connect(self.db_url) as conn:
                cursor = conn.cursor()

                # 智能体描述表
                cursor.execute(
                    """
                    CREATE TABLE agent_definitions (
                        agent_id VARCHAR(255) PRIMARY KEY,
                        role_name VARCHAR(255),
                        system_prompt TEXT NOT NULL
                        )
                    """
                )
                conn.commit()

                # 历史消息表
                cursor.execute(
                    """
                    CREATE TABLE chat_history (
                        id VARCHAR(255) PRIMARY KEY,
                        game_uid VARCHAR(255) REFERENCES games(game_uid),
                        role VARCHAR(255),
                        content TEXT,
                        timestamp DATETIME
                    )
                    """
                )
                conn.commit()

                # 游戏数据
                cursor.execute(
                    """
                    CREATE TABLE games (
                        game_uid VARCHAR(255) PRIMARY KEY,
                        current_money INTEGER,
                        current_stamina INTEGER,
                        current_mood INTEGER,
                        current_fullness INTEGER,
                        current_time VARCHAR(255),
                        current_lng REAL,
                        current_lat REAL,
                        current_location_name VARCHAR(255),
                        is_active BOOLEAN,
                        end_time DATETIME,
                        start_time DATETIME,
                        route_summary TEXT,
                        score INTEGER,
                        evaluation TEXT
                    )
                    """
                )
                conn.commit()

                # POI 数据表 (表名统一为 poi)
                cursor.execute(
                    """
                    CREATE TABLE poi (
                        poi_uid VARCHAR(255) PRIMARY KEY,
                        name VARCHAR(255),
                        type VARCHAR(255),
                        lng FLOAT,
                        lat FLOAT
                    )
                    """
                )
                conn.commit()

                # 建立索引
                cursor.execute(
                    """
                    CREATE INDEX idx_chat_history ON chat_history (
                        game_uid,
                        timestamp
                    )
                    """
                )
                conn.commit()

    def load_poi_data(
            self,
            poi_path: str | None = None
    ):
        """
        把POI数据添加到数据库中，默认从项目根目录下的 chengdu_poi.csv 加载
        """
        if not poi_path:
            poi_path = str(self.db_url.parent / "chengdu_poi.csv")

        poi_df = pd.read_csv(poi_path)
        with sqlite3.connect(
            self.db_url
        ) as conn:
            cursor = conn.cursor()
            for _, row in poi_df.iterrows():
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO poi (
                        poi_uid,
                        name,
                        type,
                        lng,
                        lat
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        row["poi_uid"],
                        row["name"],
                        row["type"],
                        row["lng"],
                        row["lat"]
                    )
                )
            conn.commit()
    
    def get_df(
            self,
            query: str,
            params: tuple = ()
    ) -> pd.DataFrame:
        """
        通过SQL-->查数据-->DataFrame (支持参数化查询)
        """
        with sqlite3.connect(
            self.db_url
        ) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            res = cursor.fetchall()
        return pd.DataFrame(
            res,
            columns=[desc[0] for desc in cursor.description]
        )
    
    def execute(
            self,
            sql: str,
            params: tuple = ()
    ):
        """
        通过SQL-->执行（增删改，支持参数化查询）
        """
        with sqlite3.connect(
            self.db_url
        ) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()

dbmanager = DBManager()