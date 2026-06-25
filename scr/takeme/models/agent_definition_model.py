from sqlalchemy import Column, String, Text, JSON
from .game_model import Base


class AgentDefinition(Base):
    """智能体定义表 — 存储 AI 角色的 system_prompt 和工具配置"""
    __tablename__ = "agent_definitions"

    agent_id = Column(String, primary_key=True)
    role_name = Column(String, nullable=False)
    system_prompt = Column(Text, nullable=False)
    output_spec = Column(Text, nullable=True)
    tools_list = Column(JSON, nullable=True)