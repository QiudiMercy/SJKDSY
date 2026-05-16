from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .game_model import Base

class ChatMessage(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_uid = Column(String, ForeignKey("games.game_uid"), nullable=False)
    role = Column(String)          # "user", "xiaoai", "system"
    content = Column(Text)
    timestamp = Column(DateTime)
    game = relationship("Game", backref="messages")





    