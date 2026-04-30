from takeme.agent.agent import Agent
from takeme.states.state import State, StateParams
from takeme.agent.agent import LLMResponse
from takeme.tools.xiaoaitools import SendMsg
from takeme.tools.tool import Tool

class XiaoaiAgent(Agent):
    """
    游戏虚拟对象
    """

    system_description = ""
    tools_list: list[Tool] = []
    name = "小爱"
    state: State

    def __init__(self, state_params: StateParams = None):
        super().__init__()
        self.state = State(state_params)

        self.tools_list.append(SendMsg())
    
    def Call(self, msg: str) -> None:
        """
        Inuptes:
            msg: 用户输入消息
        Retuens:
            None
        """
        response: LLMResponse = self.LLMChat(msg=msg)
        while response.has_tool_calls:
            for tool_call in response.tool_calls:
                for tool in self.tools_list:
                    if tool.name == tool_call.name:
                        tool_result = tool.execute(tool_call.arguments)
            