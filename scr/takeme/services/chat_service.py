from sqlalchemy.orm import Session
from models.chat_model import ChatMessage
from states.state import GameState
from core.response import success, error
from datetime import datetime
from agent.xiaoaiagent import XiaoAiAgent

class ChatService:
    def __init__(self, db: Session):
        self.db = db

    def handle_message(self, game_uid: str, content: str) -> dict:
        """处理用户消息，调用 Agent 并返回回复"""
        state = GameState(game_uid, self.db)
        try:
            state._ensure_loaded()
        except ValueError:
            return error(400, "游戏不存在")

        if not state.is_active:
            return error(400, "游戏已结束，无法发送消息")

        # 保存用户消息
        user_msg = ChatMessage(
            game_uid=game_uid,
            role="user",
            content=content,
            timestamp=datetime.utcnow()
        )
        self.db.add(user_msg)

        # 初始化小爱 Agent
        agent = XiaoAiAgent(state, self.db)
        # 加载最近对话历史注入 Agent（最近10条）
        history = self.db.query(ChatMessage).filter(
            ChatMessage.game_uid == game_uid
        ).order_by(ChatMessage.id.desc()).limit(10).all()
        for msg in reversed(history):
            role = msg.role
            if role == "user":
                agent.add_message("user", content=msg.content)
            elif role == "xiaoai":
                agent.add_message("assistant", content=msg.content)
            # 系统消息可酌情添加，这里跳过避免混乱

        # 调用 Agent
        agent_response = agent.handle_user_message(content)

        # 保存小爱回复
        agent_msg = ChatMessage(
            game_uid=game_uid,
            role="xiaoai",
            content=agent_response["reply"],
            timestamp=datetime.utcnow()
        )
        self.db.add(agent_msg)

        # 如果有系统裁定消息，也保存（避免空白记录）
        system_reply = agent_response.get("system_reply")
        if system_reply:
            sys_msg = ChatMessage(
                game_uid=game_uid,
                role="system",
                content=system_reply,
                timestamp=datetime.utcnow()
            )
            self.db.add(sys_msg)

        self.db.commit()

        return success({
            "reply": agent_response["reply"],
            "is_system_reply": agent_response["is_system_reply"],
            "system_reply": system_reply or "",
            "new_status": agent_response.get("new_status")
        })

    def get_history(self, game_uid: str) -> dict:
        messages = self.db.query(ChatMessage).filter(
            ChatMessage.game_uid == game_uid
        ).order_by(ChatMessage.id).all()
        return success({
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.strftime("%H:%M") if m.timestamp else ""
                } for m in messages
            ]
        })