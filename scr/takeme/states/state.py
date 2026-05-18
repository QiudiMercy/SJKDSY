from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from models.game_model import Game
from core.config import settings

class GameState:
    """封装一局游戏的运行时状态，提供安全的读写和边界检查"""

    def __init__(self, game_uid: str, db: Session):
        self.game_uid = game_uid
        self.db = db
        self._game: Optional[Game] = None
        self._dirty = False # 标记是否需要保存

    # ---------- 属性访问 ----------
    @property
    def money(self) -> int:
        self._ensure_loaded()
        return self._game.current_money

    @property
    def stamina(self) -> int:
        self._ensure_loaded()
        return self._game.current_stamina

    @property
    def mood(self) -> int:
        self._ensure_loaded()
        return self._game.current_mood

    @property
    def game_time(self) -> str:
        self._ensure_loaded()
        return self._game.current_time

    @property
    def lng(self) -> float:
        self._ensure_loaded()
        return self._game.current_lng

    @property
    def lat(self) -> float:
        self._ensure_loaded()
        return self._game.current_lat

    @property
    def location_name(self) -> str:
        self._ensure_loaded()
        return self._game.current_location_name

    @property
    def is_active(self) -> bool:
        self._ensure_loaded()
        return self._game.is_active

    # ---------- 加载 ----------
    def _ensure_loaded(self):
        if self._game is None:
            self._game = self.db.query(Game).filter(Game.game_uid == self.game_uid).first()
            if self._game is None:
                raise ValueError(f"Game {self.game_uid} not found")

    # ---------- 更新方法（带边界检查） ----------
    def update_money(self, amount: int) -> int:
        """增减资金，返回最新值；耗尽时 ≤0 自动触发结束"""
        self._ensure_loaded()
        new_val = self._game.current_money + amount
        if new_val < 0:
            new_val = 0
        self._game.current_money = new_val
        self._dirty = True

        if new_val <= 0:
            self._end_game("money")
        return new_val

    def update_stamina(self, amount: int) -> int:
        """增减体力，0-100 限定"""
        self._ensure_loaded()
        new_val = self._game.current_stamina + amount
        if new_val < 0:
            new_val = 0
        elif new_val > 100:
            new_val = 100
        self._game.current_stamina = new_val
        self._dirty = True

        if new_val <= 0:
            self._end_game("stamina")
        return new_val

    def update_mood(self, amount: int) -> int:
        """增减心情，0-100 限定"""
        self._ensure_loaded()
        new_val = self._game.current_mood + amount
        if new_val < 0:
            new_val = 0
        elif new_val > 100:
            new_val = 100
        self._game.current_mood = new_val
        self._dirty = True

        if new_val <= 0:
            self._end_game("mood")
        return new_val

    def advance_time(self, minutes: int) -> str:
        """推进游戏内时间，返回 HH:MM；超过 22:00 则结束"""
        self._ensure_loaded()
        fmt = "%H:%M"
        current = datetime.strptime(self._game.current_time, fmt)
        new_time = current + timedelta(minutes=minutes)
        end = datetime.strptime(settings.end_time, fmt)
        if new_time >= end:
            new_time = end
        self._game.current_time = new_time.strftime(fmt)
        self._dirty = True

        if new_time >= end:
            self._end_game("time")
        return self._game.current_time

    def move_to(self, lng: float, lat: float, location_name: str):
        """更新当前位置"""
        self._ensure_loaded()
        self._game.current_lng = lng
        self._game.current_lat = lat
        self._game.current_location_name = location_name
        self._dirty = True

    # ---------- 结束判定 ----------
    def _end_game(self, reason: str):
        """内部：标记游戏结束并记录原因（不存库，仅状态标记和日志）"""
        self._game.is_active = False
        self._game.end_time = datetime.utcnow()
        self._dirty = True
        # 后续可以在 game_service 中根据 reason 生成不同的结算文案

    def check_game_over(self) -> Tuple[bool, Optional[str]]:
        """
        检查游戏是否已结束。
        返回 (is_over, reason) reason: "money" / "stamina" / "mood" / "time" / None
        """
        self._ensure_loaded()
        if not self._game.is_active:
            # 从数据库状态反推原因
            if self._game.current_money <= 0:
                return True, "money"
            if self._game.current_stamina <= 0:
                return True, "stamina"
            if self._game.current_mood <= 0:
                return True, "mood"
            if self._game.current_time >= settings.end_time:
                return True, "time"
            return True, "unknown" # 被动结束但没有明显原因，保留
        # 主动检查以防刚才修改时未触发结束
        if self._game.current_time >= settings.end_time:
            return True, "time"
        return False, None

    # ---------- 持久化 ----------
    def save(self):
        """将更改提交到数据库（仅在有脏数据时）"""
        if self._dirty:
            self.db.commit()
            self._dirty = False

    def rollback(self):
        """放弃未保存的更改"""
        if self._dirty:
            self.db.rollback()
            self._dirty = False

    # ---------- 便捷生成初始状态字典 ----------
    def to_dict(self) -> dict:
        """返回符合接口文档的 init_state / state 结构"""
        self._ensure_loaded()
        is_over, _ = self.check_game_over()
        return {
            "time": self.game_time,
            "money": self.money,
            "stamina": self.stamina,
            "mood": self.mood,
            "location": {
                "name": self.location_name,
                "lng": self.lng,
                "lat": self.lat,
            },
            "is_game_over": is_over
        }