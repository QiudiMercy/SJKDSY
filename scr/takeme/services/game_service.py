import re
import uuid
from datetime import datetime
from states.state import GameState
from core.config import settings, dbmanager
import json

class GameService:
    """
    游戏服务类，负责游戏的创建、状态查询、最终结算等核心生命周期逻辑
    """

    def __init__(self):
        self.db = dbmanager
    
    def start_new_game(self) -> dict:
        """
        创建并初始化全新的一局游戏，存入 games 表
        """
        game_uid = f"g_{uuid.uuid4().hex[:12]}"
        
        # 实例化 GameState 会自动写入初始化数据到 games 表中
        state = GameState(
            game_uid=game_uid,
            db=self.db
        )
        
        from tools.coord_convert import wgs84_to_bd09
        bd_lng, bd_lat = wgs84_to_bd09(state.lng, state.lat)

        return {
            "code": 200,
            "data": {
                "game_uid": game_uid,
                "init_state": {
                    "time": state.current_time,
                    "money": state.money,
                    "stamina": state.stamina,
                    "mood": state.mood,
                    "fullness": state.fullness,
                    "location": {
                        "name": state.location_name,
                        "lng": bd_lng,
                        "lat": bd_lat,
                    }
                }
            }
        }

    def get_state(self, game_uid: str) -> dict:
        """
        查询并获取单局游戏的最新数值状态和是否结束
        """
        try:
            state = GameState(
                game_uid=game_uid,
                db=self.db
            )
            is_game_over, _ = state.check_game_over()
            
            from tools.coord_convert import wgs84_to_bd09
            bd_lng, bd_lat = wgs84_to_bd09(state.lng, state.lat)

            return {
                "code": 200,
                "data": {
                    "game_uid": game_uid,
                    "time": state.current_time,
                    "money": state.money,
                    "stamina": state.stamina,
                    "mood": state.mood,
                    "fullness": state.fullness,
                    "location": {
                        "name": state.location_name,
                        "lng": bd_lng,
                        "lat": bd_lat,
                    },
                    "is_game_over": is_game_over
                }
            }
        except Exception as e:
            return {"code": 400, "msg": f"获取游戏状态失败：{str(e)}", "data": None}
    
    def settle(self, game_uid: str) -> dict:
        """
        游戏结束结算：提取游玩线路、按计分规则算分、生成评价文案并归档持久化
        """
        try:
            state = GameState(game_uid=game_uid, db=self.db)
        except Exception:
            return {"code": 400, "msg": "游戏不存在", "data": None}

        # 标记游戏为结束状态
        if state.is_active:
            state._end_game()

        # ---- 1. 原生 SQL 检索并提取游玩路线摘要 ----
        sys_msgs_df = self.db.get_df(
            """
            SELECT content FROM chat_history 
            WHERE game_uid = ? AND role = 'system' 
            ORDER BY timestamp ASC
            """,
            (game_uid,)
        )

        route = ["成都东站"]
        for _, row in sys_msgs_df.iterrows():
            # 搜索 system 裁定中表示移动地点的关键词，如“打车前往宽窄巷子” -> “宽窄巷子”
            match = re.search(r'(?:前往|到达|移动到)\s*([^，,\s。！!]+)', row["content"])
            if match:
                place = match.group(1)
                if place not in route:
                    route.append(place)
                    
        if state.location_name not in route:
            route.append(state.location_name)

        # ---- 2. 依据《接口文档 v1.0》计算四大维度评分 ----
        # 维度 1: 余额剩余（20%）— 剩余金币/1000 × 20
        money_score = (state.money / 1000) * 20

        # 维度 2: 路线丰富度（30%）— 访问 POI 数量 / 5 × 30（上限 30）
        poi_count = len(route) - 1  # 去除起点“成都东站”
        route_score = min((poi_count / 5) * 30, 30)

        # 维度 3: 心情值（30%）— 当前心情值 / 100 × 30
        mood_score = (state.mood / 100) * 30

        # 维度 4: 时间利用率（20%）— (游玩结束时间 - 08:00) / (22:00 - 08:00) × 20
        try:
            end_h, end_m = map(int, state.current_time.split(":"))
            end_minutes = end_h * 60 + end_m
            start_minutes = 8 * 60          # 08:00
            total_minutes = 14 * 60         # 22:00 - 08:00 = 14小时 (840分钟)
            elapsed = end_minutes - start_minutes
            time_score = max(0, min(elapsed / total_minutes, 1)) * 20
        except Exception:
            time_score = 20  # 解析报错时兜底给满分

        # 四大维度求和，做 0-100 的边界防区拦截
        total_score = int(money_score + route_score + mood_score + time_score)
        total_score = max(0, min(total_score, 100))

        # ---- 3. 生成评价文案 ----
        if total_score >= 90:
            evaluation = "小爱度过了非常充实的一天，你是一个合格的导游！"
        elif total_score >= 70:
            evaluation = "小爱玩得挺开心，但还有更好的安排空间~"
        elif total_score >= 50:
            evaluation = "小爱觉得还行，但有些地方可以改进哦。"
        elif total_score >= 30:
            evaluation = "小爱有点失望，下次要做好攻略呀。"
        else:
            evaluation = "小爱非常不开心，这次游玩失败了..."

        # ---- 4. 原生参数化 SQL 将结算结果回填持久化到 games 表 ----
        self.db.execute(
            """
            UPDATE games 
            SET score = ?, evaluation = ?, route_summary = ? 
            WHERE game_uid = ?
            """,
            (total_score, evaluation, json.dumps(route, ensure_ascii=False), game_uid)
        )

        return {
            "code": 200,
            "data": {
                "score": total_score,
                "evaluation": evaluation,
                "route_summary": route
            }
        }