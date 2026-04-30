from abc import ABC, abstractmethod
from takeme.core.config import BASE_URL, MODEL_ID, API_KEY
from openai import OpenAI
from takeme.tools.tool import Tool
from dataclasses import dataclass
import json

@dataclass
class ToolCall:
    """
    工具调用响应
    """
    id: str
    name: str
    arguments: dict[str, any]

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
    智能体类
    """

    name: str
    system_description: str
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    tools_lists: list[Tool] = []

    def _parse(self, response) -> LLMResponse:
        """
        解析大模型响应
        """
        content = response.choices[0].message.content
        tool_calls = [
            ToolCall(
                id=tool_call.id,
                name=tool_call.function.name,
                arguments=json.loads(tool_call.function.arguments)
            ) for tool_call in response.choices[0].message.tool_calls
        ]
        
        return LLMResponse(content=content, tool_calls=tool_calls)

    @abstractmethod
    def LLMChat(self, msg: str) -> str:
        """
        大模型对话接口
        """
        return self._parse(
            response=self.client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {"role": "system", "content": self.system_description},
                    {"role": "user", "content": msg}
                ],
                tools=[tool.schema for tool in self.tools_lists],
            )
        )