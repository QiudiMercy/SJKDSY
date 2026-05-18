from sqlalchemy import Column, String, Float
from .game_model import Base

class POI(Base):
    __tablename__ = "pois"

    poi_uid = Column(String, primary_key=True)
    name = Column(String)
    type = Column(String)
    lng = Column(Float)
    lat = Column(Float)
    opening_hours = Column(String, nullable=True)