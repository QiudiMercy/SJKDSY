"""
通用 LLM Agent，负责上下文管理、调用 API、解析 Function Calling
"""
import json
from openai import OpenAI
from core.config import settings
from typing import List, Dict, Any

class BaseAgent:
    def __init__(self, system_prompt: str, tools: List[Dict] = None):
        self.client = OpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url
        )
        self.model = settings.llm_model
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.conversation_history: List[Dict] = []

    def add_message(self, role: str, content: str = None, tool_calls: List = None, tool_call_id: str = None, name: str = None):
        """向对话历史中添加消息"""
        msg = {"role": role}
        if content is not None:
            msg["content"] = content
        if tool_calls:
            msg["tool_calls"] = tool_calls
        if tool_call_id:
            msg["tool_call_id"] = tool_call_id
        if name:
            msg["name"] = name
        self.conversation_history.append(msg)

    def call_llm(self) -> dict:
        """调用 LLM，返回响应消息字典"""
        messages = [{"role": "system", "content": self.system_prompt}] + self.conversation_history
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=self.tools if self.tools else None,
            tool_choice="auto" if self.tools else None
        )
        choice = response.choices[0]
        return choice.message.model_dump()