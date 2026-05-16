from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库
    database_url: str = "sqlite:///./takeme.db"
    
    # LLM
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o"
    
    # 地图服务
    map_api_key: str = ""
    
    # 游戏初始参数
    init_money: int = 1000
    init_stamina: int = 100
    init_mood: int = 100
    init_time: str = "08:00"
    end_time: str = "22:00"
    
    # 初始位置（成都东站）
    init_lng: float = 104.148151
    init_lat: float = 30.634674
    init_location_name: str = "成都东站"
    
    class Config:
        env_file = ".env"

settings = Settings()