from abc import ABC, abstractmethod
from core.config import DBManager, settings, dbmanager
from openai import OpenAI
from tools.tool import Tool
from dataclasses import dataclass
import json
from message.message import Message
from typing import Any
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_message_function_tool_call import ChatCompletionMessageFunctionToolCall
import sqlite3


@dataclass
class ToolCall:
    """
    LLM返回的工具调用响应
    """
    id: str
    name: str
    arguments: dict[str, Any]

@dataclass
class LLMResponse:
    """
    大模型响应
    """
    content: str
    tool_calls: list[ToolCall]

    @property
    def has_tool_calls(self) -> bool:
        return len(self.tool_calls) > 0

class Agent(ABC):
    """
    智能体基类
    """

    def __init__(self, id: str, dbmanager: DBManager):
        self.id = id
        self.db = dbmanager
        self.client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
        self.model = settings.llm_model
        self.tools_lists: list[Tool] = []
        self.messages: list[Message] = []

        # 从数据库初始化 agent 数据
        agent_definition = self.db.get_df(
            "SELECT role_name, system_prompt FROM agent_definitions WHERE agent_id = ?",
            (self.id,)
        )
        self.name = agent_definition["role_name"].values[0]
        self.system_prompt = agent_definition["system_prompt"].values[0]

    def _parse(self, response: ChatCompletion) -> LLMResponse:
        """
        LLM-->LLMResponse，下一步拿来执行和存库
        """
        content = response.choices[0].message.content or ""

        tool_calls = []
        for tc in response.choices[0].message.tool_calls or []:
            if not isinstance(tc, ChatCompletionMessageFunctionToolCall):
                continue
            tool_calls.append(
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments)
                    if isinstance(tc.function.arguments, str)
                    else tc.function.arguments,
                )
            )

        return LLMResponse(content=content, tool_calls=tool_calls)
    
    def execute_tool(self, tool_call: ToolCall) -> str:
        """
        执行工具调用，返回工具执行结果字符串
        """
        for tool in self.tools_lists:
            if tool.name == tool_call.name:
                return tool.execute(tool_call.arguments)
        return f"Error: Tool '{tool_call.name}' not found."
    
    @abstractmethod
    def process_msg(self):
        """
        处理消息
        """
        ...