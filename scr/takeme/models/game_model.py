from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Game(Base):
    __tablename__ = "games"

    game_uid = Column(String, primary_key=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    current_money = Column(Integer, default=1000)
    current_stamina = Column(Integer, default=100)
    current_mood = Column(Integer, default=100)
    current_time = Column(String, default="08:00")    # "HH:MM" 格式
    current_lng = Column(Float)
    current_lat = Column(Float)
    current_location_name = Column(String)
    is_active = Column(Boolean, default=True)
    current_fullness = Column(Integer, default=100)
    route_summary = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    evaluation = Column(Text, nullable=True)