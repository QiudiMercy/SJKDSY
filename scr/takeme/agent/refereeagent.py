from core.config import settings
from agent.agent import Agent, LLMResponse
from tools.tool import Tool
from tools.refereetools import Referee
from message.message import Message, chatmessage
from states.state import GameState
import json

class RefereeAgent(Agent):
    """
    裁判 — 游戏虚拟角色
    一个专业的裁判，负责游戏的规则执行和冲突解决
    """

    def __init__(self, gamestate: GameState, dbmanager):
        super().__init__(
            id="referee",
            dbmanager=dbmanager
        )
        self.messages = []  # 存入本次交互的消息实体 List[Message]
        
        # 初始化工具并绑定当前运行时状态机
        self.tools_lists = [
            SendMsg(self.messages),
            UpgradeState(gamestate, self)
        ]
        self.name = "裁判"
        self.upgrade_called = False
    
    def process_msg(self, game_uid: str) -> list[str]:
        """
        用户发送消息 -> 小爱回复消息 -> 裁判介入裁定系统事件并发送系统消息
        """
        # 获取所有的聊天记录，并安全地在本地进行反向查找（获取最近的一轮对话）
        history_message = chatmessage.get_all_messages(game_uid)
        history_message.reverse()  # 修复 .reverse() 原地排序返回 None 的致命 Bug
        
        dialog = []
        for msg in history_message:
            dialog.append(msg)
            if msg["role"] == "user":
                break
                
        # 翻转回正常的时间顺序传给大模型做上下文
        dialog.reverse()
        
        prompt = [
            {"role": "system", "content": self.get_system_prompt(game_uid)},
            {"role": "user", "content": json.dumps(dialog, ensure_ascii=False)}
        ]
        
        # 调用大模型生成裁判裁定
        response = self._parse(
            self.client.chat.completions.create(
                model=self.model,
                messages=prompt,
                tools=[t.schema for t in self.tools_lists],
            )
        )
        
        # 检查工具调用情况并循环
        while response.has_tool_calls:
            prompt.append({
                "role": "assistant",
                "content": response.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments, ensure_ascii=False)
                        }
                    }
                    for tc in response.tool_calls
                ]
            })
            
            for tc in response.tool_calls:
                tool_res = self.execute_tool(tc)
                if isinstance(tool_res, dict):
                    tool_res_str = json.dumps(tool_res, ensure_ascii=False)
                else:
                    tool_res_str = str(tool_res)

                prompt.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool_res_str
                })
                
            response = self._parse(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=prompt,
                    tools=[t.schema for t in self.tools_lists],
                )
            )
            
        # 存入本次产生的 System 或 Referee 消息 (只有在有状态更新时，才允许发送或存储通知)
        result = []
        import re
        if self.upgrade_called:
            for msg in self.messages:
                clean_msg_content = re.sub(r'<think>.*?</think>', '', msg.content, flags=re.DOTALL).strip()
                clean_msg_content = clean_msg_content.replace('<think>', '').replace('</think>', '').strip()
                if clean_msg_content:
                    msg.content = clean_msg_content
                    chatmessage.store_message(
                        message=msg,
                        game_uid=game_uid
                    )
                    result.append(clean_msg_content)
                
            if not result and response.content:
                clean_content = re.sub(r'<think>.*?</think>', '', response.content, flags=re.DOTALL).strip()
                clean_content = clean_content.replace('<think>', '').replace('</think>', '').strip()
                if clean_content:
                    ref_msg = Message(role="system", content=clean_content)
                    chatmessage.store_message(message=ref_msg, game_uid=game_uid)
                    result.append(clean_content)
        else:
            self.messages.clear()
            
        return result
    
    def get_system_prompt(self, game_uid: str) -> str:
        """
        原生 SQL 查询状态，拼装裁判专属 Prompt
        """
        state_df = self.db.get_df(
            """
            SELECT current_money, current_stamina, current_mood, current_fullness, games.current_time, current_location_name
            FROM games
            WHERE game_uid = ?
            """,
            (game_uid,)
        )
        if state_df.empty:
            return self.system_prompt
            
        row = state_df.iloc[0]

        # 智能时间段修饰，以绝对防止大模型将 morning (08:00) 误判为凌晨/深夜
        t_str = str(row["current_time"])
        try:
            h = int(t_str.split(":")[0])
            if 6 <= h < 12:
                time_desc = f"{t_str} (白天早上/上午)"
            elif 12 <= h < 18:
                time_desc = f"{t_str} (白天下午)"
            elif 18 <= h <= 22:
                time_desc = f"{t_str} (晚上)"
            else:
                time_desc = f"{t_str} (凌晨/深夜)"
        except Exception:
            time_desc = t_str

        prompt = f"""
当前游戏数值状态：
- 余额：{row["current_money"]}元
- 体力：{row["current_stamina"]}/100
- 心情：{row["current_mood"]}/100
- 饱食度：{row["current_fullness"]}/100
- 当前时间时刻：{time_desc}
- 当前位置：{row["current_location_name"]}
"""
        return self.system_prompt + prompt


# 内置消息发送工具
class SendMsg(Tool):
    """
    发送一段裁判裁定短消息到前端（系统消息）
    """
    name: str = "send_message"
    description: str = "向玩家发送系统的裁定/提醒/通知消息，字数应精简（10-50字）"

    parameters: dict = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "要发送的系统裁定消息内容"
            }
        },
        "required": ["content"]
    }

    def __init__(self, messages: list):
        self.messages = messages

    def execute(self, arguments: dict) -> str:
        self.messages.append(
            Message(
                role="system",
                content=arguments.get('content', '')
            )
        )
        return f"系统消息已发送: {arguments.get('content', '')}"


# 更新游戏状态的工具
class UpgradeState(Tool):
    """
    更新游戏数值状态
    """
    name: str = "upgrade_state"
    description: str = "更新游戏内小爱的各项状态值（余额、体力、心情、饱食度、时间、位置名称）"

    parameters: dict = {
        "type": "object",
        "properties": {
            "state": {
                "type": "string",
                "description": "要更新的状态字段名",
                "enum": [
                    "current_money",
                    "current_stamina",
                    "current_mood",
                    "current_fullness",
                    "current_time",
                    "current_location_name"
                ]
            },
            "value": {
                "type": "string",
                "description": "要变更或更新的值。如果是钱、体力、心情、饱食度，则是整数变动量（如 +10, -50）；如果是时间，则是推进的分钟数（如 30）；如果是位置，则是目标位置的绝对名称（如 太古里）"
            }
        },
        "required": ["state", "value"]
    }
    
    def __init__(self, gamestate: GameState, agent: 'RefereeAgent' = None):
        self.gamestate = gamestate
        self.agent = agent

    def execute(self, arguments: dict) -> str:
        if self.agent:
            self.agent.upgrade_called = True
            
        var = arguments.get('state', '')
        val_str = arguments.get('value', '0')
        
        if not var:
            return "状态更新失败：参数缺失"
            
        try:
            if var == "current_money":
                delta = int(float(val_str))
                self.gamestate.update_money(delta)
            elif var == "current_stamina":
                delta = int(float(val_str))
                self.gamestate.update_stamina(delta)
            elif var == "current_mood":
                delta = int(float(val_str))
                self.gamestate.update_mood(delta)
            elif var == "current_fullness":
                delta = int(float(val_str))
                self.gamestate.update_fullness(delta)
            elif var == "current_time":
                delta = int(float(val_str))
                self.gamestate.advance_time(delta)
            elif var == "current_location_name":
                self.gamestate.location_name = val_str
                # 原生 SQL 智能查询：当裁判更新位置名称时，自动查询 poi 表获取经纬度，并同步更新状态坐标 (WGS-84)
                poi_df = self.gamestate.db.get_df(
                    "SELECT lng, lat FROM poi WHERE name LIKE ? LIMIT 1",
                    (f"%{val_str}%",)
                )
                if not poi_df.empty:
                    self.gamestate.lng = float(poi_df.iloc[0]["lng"])
                    self.gamestate.lat = float(poi_df.iloc[0]["lat"])
                
            return f"状态已更新: {var} -> {val_str}"
        except Exception as e:
            return f"状态更新失败：类型转换错误 {str(e)}"