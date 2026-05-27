from core.config import dbmanager
from states.state import GameState
from agent.xiaoaiagent import XiaoAiAgent
from message.message import Message, chatmessage

class ChatService:
    def __init__(self):
        self.db = dbmanager

    def handle_message(self, game_uid: str, content: str, time_passed_min: int = 0) -> dict:
        """
        处理玩家发送的自然语言消息，调用 XiaoAiAgent，并返回回复与最新的游戏快照
        """
        # 加载实时游戏状态
        state = GameState(game_uid=game_uid, db=self.db)
        if not state.is_active:
            return {"code": 400, "msg": "游戏已结束，无法发送消息", "data": None}

        # 推进游戏内的流逝时间 (1:100)
        if time_passed_min > 0:
            state.advance_time(time_passed_min)
            # 检查是否熔断触发游戏结束
            is_over, reason = state.check_game_over()
            if is_over:
                return {"code": 400, "msg": f"游戏已自动结束：{reason}", "data": None}

        # 初始化小爱智能体
        agent = XiaoAiAgent(dbmanager=self.db)
        
        # 1. 调用小爱智能体，生成自然语言对话回复并持久化
        segments = agent.process_msg(content, game_uid)

        # 2. 紧接着调用系统裁判智能体，实时评估对话并进行数值裁决、地理坐标迁移
        from agent.refereeagent import RefereeAgent
        referee = RefereeAgent(gamestate=state, dbmanager=self.db)
        referee_results = referee.process_msg(game_uid)

        # 仅获取当前回合由裁判新产生的系统通知，若无则为空，防止重复显示上一回合的通知气泡
        system_reply = referee_results[0] if referee_results else ""

        # 服务端统一将底层 WGS-84 坐标转换为百度 BD-09 坐标提供给前端地图渲染
        from tools.coord_convert import wgs84_to_bd09
        bd_lng, bd_lat = wgs84_to_bd09(state.lng, state.lat)

        # 获取最新的游戏状态快照，用于前端同步状态栏
        new_status = {
            "time": state.current_time,
            "money": state.money,
            "stamina": state.stamina,
            "mood": state.mood,
            "fullness": state.fullness,
            "location": {
                "name": state.location_name,
                "lng": bd_lng,
                "lat": bd_lat
            }
        }

        full_reply = "".join(segments)

        return {
            "code": 200,
            "data": {
                "reply": full_reply,
                "segments": segments,
                "system_reply": system_reply,
                "new_status": new_status
            }
        }

    def get_history(self, game_uid: str) -> dict:
        """
        原生 SQL 查询一局游戏中全量对话历史 (按时间升序)
        """
        history_df = self.db.get_df(
            "SELECT role, content, timestamp FROM chat_history WHERE game_uid = ? ORDER BY timestamp ASC",
            (game_uid,)
        )
        
        messages = []
        for _, row in history_df.iterrows():
            ts = row["timestamp"]
            # 截取时刻部分，例如 "2026-05-27 08:30:12" -> "08:30"
            formatted_time = ts[-8:-3] if isinstance(ts, str) and len(ts) >= 8 else ""
            messages.append({
                "role": row["role"],
                "content": row["content"],
                "timestamp": formatted_time
            })
            
        return {
            "code": 200,
            "data": {
                "messages": messages
            }
        }