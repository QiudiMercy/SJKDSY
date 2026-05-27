from core.config import settings
from agent.agent import Agent, LLMResponse
from tools.xiaoaitools import UpdateStatusTool, SearchPOITool, PlanRouteTool
from tools.tool import Tool
from tools.refereetools import Referee
from message.message import Message, chatmessage
import json
import re

def split_short_segments(text: str, min_len: int = 10, max_len: int = 20) -> list[str]:
    # 彻底过滤 <think>...</think> 标签及其包裹的所有推理链路
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    # 同时过滤裸露的 <think> 和 </think> 标签防止残留
    text = text.replace('<think>', '').replace('</think>', '').strip()
    
    if not text:
        return []
        
    # 按标点符号（，。！？、~～；) 对文本进行初步切割
    pattern = re.compile(r'([^，。！？、~～；\s,.\!?~;]+[，。！？、~～；,\.!\?~;]*)')
    raw_clauses = pattern.findall(text)
    if not raw_clauses:
        raw_clauses = [text]
        
    segments = []
    current_seg = ""
    for clause in raw_clauses:
        clause = clause.strip()
        if not clause:
            continue
        if len(current_seg) + len(clause) <= max_len:
            current_seg += clause
        else:
            if current_seg:
                segments.append(current_seg)
            # 如果单句就已经超长，按 max_len 切片
            while len(clause) > max_len:
                segments.append(clause[:max_len])
                clause = clause[max_len:]
            current_seg = clause
    if current_seg:
        segments.append(current_seg)
        
    return [s.strip() for s in segments if s.strip()]

class XiaoAiAgent(Agent):
    """
    小爱 — 游戏虚拟角色
    从外地来成都的年轻女性，第一次在成都游玩，性格活泼可爱，会有自然的情绪变化
    """

    def __init__(self, dbmanager):
        super().__init__(
            id="xiaoai",
            dbmanager=dbmanager
        )
        self.name = "小爱"
        self.messages = []  # 存入本次交互的消息实体 List[Message]

    def process_msg(self, content: str, game_uid: str) -> list[str]:
        """
        用户发送消息 -> 小爱处理决策 -> 返回分段消息文本列表
        """
        # 1. 动态加载最新的运行时游戏状态
        from states.state import GameState
        state = GameState(game_uid=game_uid, db=self.db)

        # 2. 动态注入当前位置坐标以初始化工具 (小爱不应该有修改/更新 status 的工具，该功能仅限裁判拥有)
        self.tools_lists = [
            SendMsg(self.messages),
            SearchPOITool(db=self.db, current_lng=state.lng, current_lat=state.lat),
            PlanRouteTool(db=self.db, current_lng=state.lng, current_lat=state.lat)
        ]

        # 3. 读取近期的聊天上下文 (还原为大模型所需的 assistant 角色)
        history_message = chatmessage.get_all_messages(game_uid)
        for msg in history_message:
            if msg["role"] == "xiaoai":
                msg["role"] = "assistant"

        # 4. 构建 System Prompt 并拼接上下文
        prompt = [
            {
                "role": "system",
                "content": self.get_system_prompt(game_uid)
            }
        ] + history_message + [{"role": "user", "content": content}]

        # 5. 调用大模型获取响应
        response = self._parse(
            self.client.chat.completions.create(
                model=self.model,
                messages=prompt,
                tools=[t.schema for t in self.tools_lists],
            )
        )

        # 6. 大模型请求工具调用时的递归处理环 (支持 role: tool 消息追加)
        while response.has_tool_calls:
            # 追加 assistant 消息及其 tool_calls 定义
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

            # 执行工具调用，并将返回值填回 prompt 历史
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

            # 重新投喂给大模型
            response = self._parse(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=prompt,
                    tools=[t.schema for t in self.tools_lists],
                )
            )

        # 7. 保存本次交互的 User 消息到数据库
        user_msg = Message(role="user", content=content)
        chatmessage.store_message(message=user_msg, game_uid=game_uid)

        # 8. 保存小爱通过 send_message 产生的拟人分段消息并回传 (进行强制 10-20 字极短拆分)
        result = []
        for msg in self.messages:
            split_contents = split_short_segments(msg.content, min_len=10, max_len=20)
            for chunk in split_contents:
                chunk_msg = Message(role="xiaoai", content=chunk)
                chatmessage.store_message(message=chunk_msg, game_uid=game_uid)
                result.append(chunk)

        # 9. 容错与段落智能拆分：如果大模型直接吐出了带有换行的纯文本回复，我们按照换行符进行切割，
        # 并强制拆分成 10-20 字极短句消息写入数据库并回传。
        if not result and response.content:
            split_contents = split_short_segments(response.content, min_len=10, max_len=20)
            for chunk in split_contents:
                ai_msg = Message(role="xiaoai", content=chunk)
                chatmessage.store_message(message=ai_msg, game_uid=game_uid)
                result.append(chunk)

        return result

    def get_system_prompt(self, game_uid: str) -> str:
        """
        原生 SQL 查询实时游戏状态并拼装 System Prompt
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
- 当前所在位置：{row["current_location_name"]}
"""
        return self.system_prompt + prompt


# 内部依赖工具 SendMsg (在 execute 时向消息实体数组注入实体)
class SendMsg(Tool):
    """
    发送一段短消息到前端（拟人化分段发送）
    """
    name: str = "send_message"
    description: str = "给用户发送消息，一般情况下字数介于10-50之间"

    parameters: dict = {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "要发送的消息内容"
            }
        },
        "required": ["content"]
    }

    def __init__(self, messages: list):
        self.messages = messages

    def execute(self, arguments: dict) -> str:
        self.messages.append(
            Message(
                role="xiaoai",
                content=arguments.get('content', '')
            )
        )
        return f"消息已发送: {arguments.get('content', '')}"