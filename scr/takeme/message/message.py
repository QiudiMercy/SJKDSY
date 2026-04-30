from abc import ABC
import json
from takeme.agent.agent import LLMResponse, ToolCall

class Message(ABC):
    """
    消息类
    """

    history: list[dict] = []

    def add_system(self, msg: str) -> None:
        """
        添加系统消息
        """
        self.history.append({"role": "system", "content": msg})
    
    def add_user(self, msg: str) -> None:
        """
        添加用户消息
        """
        self.history.append({"role": "user", "content": msg})
    
    def add_assistant(self, response: LLMResponse) -> None:
        """
        添加LLM回复
        """
        if response.has_tool_calls:
            self.history.append(
                {
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.name,
                                "arguments": json.dumps(tool_call.arguments)
                            }
                        } for tool_call in response.tool_calls
                    ]
                }
            )
        else:
            self.history.append(
                {"role": "assistant", "content": response.content or ""}
            )
    
    def add_tool_result(self, tool:ToolCall, result: str) -> None:
        """
        添加工具调用结果
        """
        self.history.append(
            {
                "role": "tool",
                "tool_call_id": tool.id,
                "name": tool.name,
                "content": result
            }
        )