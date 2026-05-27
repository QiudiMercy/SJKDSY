from datetime import datetime
from typing import List, Literal
from dataclasses import dataclass, field
from core.config import dbmanager, DBManager
import uuid

def generate_message_id() -> str:
    """
    生成一个唯一的消息 ID (12 位 16 进制字符串)
    """
    return uuid.uuid4().hex[:12]

@dataclass
class Message:
    """
    单条消息的数据模型
    """
    role: Literal['user', 'xiaoai', 'system', 'referee', 'assistant', 'tool']
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    id: str = field(default_factory=generate_message_id)

class ChatMessage:
    """
    与数据库 chat_history 表对接的类，负责读取与写入聊天消息
    """
    def __init__(self):
        self.db = dbmanager
    
    def get_all_messages(self, game_uid: str) -> List[dict]:
        """
        查询一局游戏中的所有消息 (按时间升序)
        """
        message_df = self.db.get_df(
            "SELECT role, content FROM chat_history WHERE game_uid = ? ORDER BY timestamp ASC",
            (game_uid,)
        )
        return [
            {
                "role": row["role"],
                "content": row["content"],
            }
            for _, row in message_df.iterrows()
        ]
    
    def store_message(self, message: Message, game_uid: str):
        """
        参数化写入一条消息到数据库，彻底防范 SQL 报错与注入
        """
        # 兼容 role，比如把 assistant 转回 xiaoai (如果是大模型交互需要的 role)
        role = message.role
        if role == "assistant":
            role = "xiaoai"
            
        self.db.execute(
            """
            INSERT INTO chat_history (id, game_uid, role, content, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                message.id,
                game_uid,
                role,
                message.content,
                message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            )
        )
    
chatmessage = ChatMessage()