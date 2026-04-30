from takeme.tools.tool import Tool

class SendMsg(Tool):

    name = "发消息"
    description = "给用户发送消息"

    def execute(self, msg: str) -> str:
        """
        执行工具
        """
        return f"已向用户发送消息: {msg}"

    def schema(self) -> dict:
        """
        工具模式
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "msg": {
                            "type": "string",
                            "description": "要发送的消息内容"
                        }
                    }
                },
                "required": ["msg"]
            }
        }