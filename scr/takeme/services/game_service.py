import re
import uuid
from datetime import datetime         
from sqlalchemy.orm import Session
from models.game_model import Game
from models.chat_model import ChatMessage
from states.state import GameState
from core.config import settings
from core.response import success, error

class GameService:
    def __init__(self, db: Session):
        self.db = db

    def start_new_game(self) -> dict:
        """创建新游戏并返回初始状态"""
        game_uid = f"g_{uuid.uuid4().hex[:12]}"
        new_game = Game(
            game_uid=game_uid,
            current_money=settings.init_money,
            current_stamina=settings.init_stamina,
            current_mood=settings.init_mood,
            current_time=settings.init_time,
            current_lng=settings.init_lng,
            current_lat=settings.init_lat,
            current_location_name=settings.init_location_name,
            is_active=True
        )
        self.db.add(new_game)
        self.db.commit()
        state = GameState(game_uid, self.db)
        return success({
            "game_uid": game_uid,
            "init_state": state.to_dict()
        })

    def get_state(self, game_uid: str) -> dict:
        """查询当前游戏状态"""
        state = GameState(game_uid, self.db)
        try:
            state._ensure_loaded()
        except ValueError:
            return error(400, "游戏不存在")
        return success(state.to_dict())

    # 在 settle 方法中，替换原来的 route 构建
def settle(self, game_uid: str) -> dict:
    state = GameState(game_uid, self.db)
    try:
        state._ensure_loaded()
    except ValueError:
        return error(400, "游戏不存在")

    if state.is_active:
        state._game.is_active = False
        state._game.end_time = datetime.utcnow()
        state.save()

    # 计算评分
    score = int(
        (state.money / 1000) * 30 +
        (state.stamina / 100) * 30 +
        (state.mood / 100) * 40
    )
    if score > 100: score = 100

    # ---- 提取路线摘要 ----
    # 从系统消息中提取地点（格式如: "前往XXX，"）
    system_msgs = self.db.query(ChatMessage).filter(
        ChatMessage.game_uid == game_uid,
        ChatMessage.role == "system"
    ).order_by(ChatMessage.id).all()

    route = ["成都东站"]
    for msg in system_msgs:
        # 匹配 "前往XXX" 或 "到达XXX"
        match = re.search(r'(?:前往|到达)([^，,\s]+)', msg.content)
        if match:
            place = match.group(1)
            if place not in route:  # 去重
                route.append(place)
    # 添加最终位置
    if state.location_name not in route:
        route.append(state.location_name)

    # 评价文案
    if score >= 80:
        evaluation = "小爱度过了非常充实的一天，你是一个合格的导游！"
    elif score >= 50:
        evaluation = "小爱玩得还算开心，但总觉得少了点什么。"
    else:
        evaluation = "小爱有些失望，下次再接再厉吧。"

    return success({
        "score": score,
        "evaluation": evaluation,
        "route_summary": route
    })