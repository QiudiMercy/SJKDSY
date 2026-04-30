from dataclasses import dataclass
from datetime import datetime


@dataclass
class Response:
    """
    大模型交互的响应对象
    """
    role: str
    timestamp: datetime
    content: str