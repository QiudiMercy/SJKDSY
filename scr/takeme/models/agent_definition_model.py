from sqlalchemy import Column, String, Text, JSON
from .game_model import Base


class AgentDefinition(Base):
    """智能体定义表 — 存储 AI 角色的 system_prompt 和工具配置"""
    __tablename__ = "agent_definitions"

    agent_id = Column(String, primary_key=True)       # 如 "xiaoai", "referee"
    role_name = Column(String, nullable=False)         # 如 "小爱", "裁判"
    system_prompt = Column(Text, nullable=False)       # 角色定义（语言风格、行为规范）
    output_spec = Column(Text, nullable=True)          # 输出规范
    tools_list = Column(JSON, nullable=True)           # 可调用的 Function Calling 工具列表