from takeme.tools.tool import Tool
from takeme.states.state import State

class SendSystemMsg(Tool):

    """
    发送系统消息工具
    """

    name = "发送系统消息"
    description = "给用户发送系统消息"

    def execute(self, msg: str) -> str:
        """
        执行工具
        """
        return f"已向用户发送系统消息: {msg}"

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
                            "description": "要发送的系统消息内容，比如“触发决策：移动到十里店”"
                        }
                    }
                },
                "required": ["msg"]
            }
        }

class ModifyState(Tool):

    """
    修改状态工具
    """

    name = "修改状态"
    description = "修改小爱的状态参数"

    def __init__(self, state: State):
        super().__init__()
        self.state: State = state
    
    def execute(self, modify_state: dict) -> str:
        """
        修改状态
        """
        self.state.modify_params(**modify_state)
        return f"已修改状态: {modify_state}"

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
                        "modify_state": {
                            "type": "dict",
                            "description": "要修改的状态参数，只能是time、location、mood、power、money等中的一个或几个参数，比如{'time': +30, 'mood': -5} // 时间增加30分钟，情绪值减少5"
                        }
                    }
                },
                "required": ["modify_state"]
            }
        }