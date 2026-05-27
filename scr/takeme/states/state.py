from datetime import datetime, timedelta
from typing import Optional, Tuple
from core.config import settings, dbmanager, DBManager

class GameState:
    """
    一局游戏的参数和状态管理 (完全基于原生 SQL 读写)
    """

    def __init__(
            self,
            game_uid: str,
            db: DBManager = dbmanager
    ):
        self._game_uid = game_uid
        self.db = db
        
        # 尝试从数据库加载已存在的游戏数据
        game_df = self.db.get_df("SELECT * FROM games WHERE game_uid = ?", (self._game_uid,))
        if not game_df.empty:
            row = game_df.iloc[0]
            # 解析开始时间
            st = row["start_time"]
            if isinstance(st, str):
                for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
                    try:
                        self._start_time = datetime.strptime(st, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    self._start_time = datetime.now()
            else:
                self._start_time = st if isinstance(st, datetime) else datetime.now()
                
            self._is_active = bool(row["is_active"])
            self._current_money = int(row["current_money"])
            self._current_stamina = int(row["current_stamina"])
            self._current_mood = int(row["current_mood"])
            self._current_fullness = int(row["current_fullness"]) if row["current_fullness"] is not None else settings.init_fullness
            self._current_time = str(row["current_time"])
            self._current_lng = float(row["current_lng"])
            self._current_lat = float(row["current_lat"])
            self._current_location_name = str(row["current_location_name"])
        else:
            # 初始化全新游戏的参数
            self._start_time = datetime.now()
            self._is_active = True
            self._current_money = settings.init_money
            self._current_stamina = settings.init_stamina
            self._current_mood = settings.init_mood
            self._current_fullness = settings.init_fullness
            self._current_time = settings.init_time
            self._current_lng = settings.init_lng
            self._current_lat = settings.init_lat
            self._current_location_name = settings.init_location_name
            
            # 将初始化数据写入数据库
            self._write_game_data()

    def _write_game_data(self):
        """
        写入游戏数据到数据库 (原生参数化 SQL，解决拼接报错)
        """
        self.db.execute(
            """
            INSERT INTO games (
                game_uid,
                start_time,
                is_active,
                current_money,
                current_stamina,
                current_mood,
                current_fullness,
                current_time,
                current_lng,
                current_lat,
                current_location_name
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self._game_uid,
                self._start_time.strftime("%Y-%m-%d %H:%M:%S"),
                1 if self._is_active else 0,
                self._current_money,
                self._current_stamina,
                self._current_mood,
                self._current_fullness,
                self._current_time,
                self._current_lng,
                self._current_lat,
                self._current_location_name
            )
        )

    # ---------- 属性访问 (Getters) ----------
    @property
    def money(self) -> int:
        return self._current_money

    @property
    def stamina(self) -> int:
        return self._current_stamina

    @property
    def mood(self) -> int:
        return self._current_mood

    @property
    def fullness(self) -> int:
        return self._current_fullness

    @property
    def current_time(self) -> str:
        return self._current_time

    @property
    def game_time(self) -> str:
        return self._current_time

    @property
    def lng(self) -> float:
        return self._current_lng

    @property
    def lat(self) -> float:
        return self._current_lat

    @property
    def location_name(self) -> str:
        return self._current_location_name

    @property
    def is_active(self) -> bool:
        return self._is_active
    
    # ---------- 状态修改 (Setters) ----------
    @money.setter
    def money(self, value: int):
        self._current_money = max(0, int(value))
        if self._current_money <= 0:
            self._end_game()
        self.db.execute(
            "UPDATE games SET current_money = ? WHERE game_uid = ?",
            (self._current_money, self._game_uid)
        )
    
    @stamina.setter
    def stamina(self, value: int):
        self._current_stamina = max(0, int(value))
        if self._current_stamina <= 0:
            self._end_game()
        self.db.execute(
            "UPDATE games SET current_stamina = ? WHERE game_uid = ?",
            (self._current_stamina, self._game_uid)
        )
    
    @mood.setter
    def mood(self, value: int):
        self._current_mood = max(0, int(value))
        if self._current_mood <= 0:
            self._end_game()
        self.db.execute(
            "UPDATE games SET current_mood = ? WHERE game_uid = ?",
            (self._current_mood, self._game_uid)
        )
    
    @fullness.setter
    def fullness(self, value: int):
        self._current_fullness = max(0, int(value))
        if self._current_fullness <= 0:
            self._end_game()
        self.db.execute(
            "UPDATE games SET current_fullness = ? WHERE game_uid = ?",
            (self._current_fullness, self._game_uid)
        )
    
    @current_time.setter
    def current_time(self, value: str):
        val_str = str(value)
        if ":" in val_str:
            # 绝对时间设置 (如 "14:30")
            self._current_time = val_str
            try:
                curr_dt = datetime.strptime(self._current_time, "%H:%M")
                end_dt = datetime.strptime(settings.end_time, "%H:%M")
                if curr_dt >= end_dt:
                    self._end_game()
            except Exception:
                pass
        else:
            # 相对分钟推进 (如 "30" 或 30)
            try:
                mins = int(value)
                final_time = datetime.strptime(self._current_time, "%H:%M") + timedelta(minutes=mins)
                end_dt = datetime.strptime(settings.end_time, "%H:%M")
                if final_time >= end_dt:
                    self._end_game()
                    self._current_time = settings.end_time
                else:
                    self._current_time = final_time.strftime("%H:%M")
            except Exception:
                pass

        self.db.execute(
            "UPDATE games SET current_time = ? WHERE game_uid = ?",
            (self._current_time, self._game_uid)
        )
    
    @lng.setter
    def lng(self, value: float):
        self._current_lng = float(value)
        self.db.execute(
            "UPDATE games SET current_lng = ? WHERE game_uid = ?",
            (self._current_lng, self._game_uid)
        )
    
    @lat.setter
    def lat(self, value: float):
        self._current_lat = float(value)
        self.db.execute(
            "UPDATE games SET current_lat = ? WHERE game_uid = ?",
            (self._current_lat, self._game_uid)
        )
    
    @location_name.setter
    def location_name(self, value: str):
        self._current_location_name = str(value)
        self.db.execute(
            "UPDATE games SET current_location_name = ? WHERE game_uid = ?",
            (self._current_location_name, self._game_uid)
        )

    def _end_game(self):
        """
        结束游戏，更新数据库状态
        """
        self._is_active = False
        end_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute(
            "UPDATE games SET is_active = ?, end_time = ? WHERE game_uid = ?",
            (0, end_time_str, self._game_uid)
        )

    # ---------- 裁判/Service 专用增量修改方法 (提供完美双重兼容) ----------
    def update_money(self, delta: int):
        self.money = self.money + delta

    def update_stamina(self, delta: int):
        self.stamina = self.stamina + delta

    def update_mood(self, delta: int):
        self.mood = self.mood + delta

    def update_fullness(self, delta: int):
        self.fullness = self.fullness + delta

    def advance_time(self, mins: int):
        self.current_time = str(mins)

    def move_to(self, lng: float, lat: float, location_name: str):
        self.lng = lng
        self.lat = lat
        self.location_name = location_name

    def check_game_over(self) -> Tuple[bool, str]:
        """
        检查游戏是否已结束，返回 (是否结束, 结束原因)
        """
        if not self._is_active:
            return True, "游戏已结束"
        if self._current_money <= 0:
            self._end_game()
            return True, "资金已耗尽"
        if self._current_stamina <= 0:
            self._end_game()
            return True, "体力已耗尽"
        if self._current_mood <= 0:
            self._end_game()
            return True, "心情已归零"
        try:
            curr_dt = datetime.strptime(self._current_time, "%H:%M")
            end_dt = datetime.strptime(settings.end_time, "%H:%M")
            if curr_dt >= end_dt:
                self._end_game()
                return True, "时间已到晚上 22:00"
        except Exception:
            pass
        return False, ""

    def save(self):
        """
        空存根方法，防止旧 Service 调用报错 (手写 SQL 在 Setter 中即时持久化)
        """
        pass