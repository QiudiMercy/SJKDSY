from pathlib import Path
from pydantic_settings import BaseSettings
import sqlite3
import pandas as pd

map_api_key_enc = "3562396532333162656436636431633965616335346335363037393330663637"
llm_api_key_enc = "366979766d5053473065516b73636e74346b6b4766704c6758724a4d3968457a4a77306643777262325478627972435832416850347a76645544753730534e7649"

class Settings(BaseSettings):
    model_config = {
        "env_file": "",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

    database_url: str = str(Path(__file__).parent.parent.parent / "takeme.db")

    # LLM
    llm_api_key: str = bytes.fromhex(llm_api_key_enc).decode("utf-8")
    llm_base_url: str = "https://api.stepfun.com/step_plan/v1"
    llm_model: str = "step-3.7-flash"

    # 地图服务
    map_api_key: str = bytes.fromhex(map_api_key_enc).decode("utf-8")

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