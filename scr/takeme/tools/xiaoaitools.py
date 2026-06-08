from typing import Optional, List
from tools.tool import Tool, haversine_distance
from tools.coord_convert import gcj02_to_bd09
from core.config import dbmanager
import pandas as pd

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

    def execute(self, arguments: dict) -> str:
        return f"消息已发送: {arguments.get('content', '')}"


class UpdateStatusTool(Tool):
    """请求修改游戏状态数值，由裁判裁定后生效"""

    @property
    def name(self): return "update_status"

    @property
    def description(self): return "修改小爱的游戏状态（余额、体力、心情、饱食度、时间、位置）。只能修改当前游戏的状态，所有数值变更需经裁判裁定。"

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "money_delta": {"type": "integer", "description": "金额变化（正数增加，负数减少），单位元"},
                "stamina_delta": {"type": "integer", "description": "体力变化（正数恢复，负数消耗），范围-100到100"},
                "mood_delta": {"type": "integer", "description": "心情变化（正数提升，负数下降），范围-100到100"},
                "fullness_delta": {"type": "integer", "description": "饱食度变化（正数增加，负数减少），范围-100到100"},
                "time_advance_min": {"type": "integer", "description": "游戏内时间推进的分钟数"},
                "target_location_name": {"type": "string", "description": "目标地点名称"},
                "target_lng": {"type": "number", "description": "目标地点经度"},
                "target_lat": {"type": "number", "description": "目标地点纬度"},
                "reason": {"type": "string", "description": "修改状态的原因"}
            },
            "required": ["reason"]
        }

    def __init__(self, referee=None, state=None):
        self.referee = referee  # Referee 实例
        self.state = state      # GameState 实例

    def execute(self, arguments: dict) -> dict:
        if self.referee and self.state:
            return self.referee.validate_and_apply(self.state, arguments)
        return {"system_reply": "裁定器未初始化", "applied_status": None}


class SearchPOITool(Tool):
    """搜索成都 POI 地点 (基于原生 SQL 检索)"""

    @property
    def name(self): return "search_poi"

    @property
    def description(self): return "搜索成都 POI 地点。调用前应根据用户上下文自行提炼核心地点名、商圈名、景点名或类别词，不要把完整口语句子直接作为关键词。"

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "keyword": {
                    "type": "string",
                    "description": "由 AI 根据上下文提炼出的核心搜索词，例如用户说'我们去人民公园相亲角看看'时传'人民公园'或'相亲角'；用户说'附近有没有火锅'时传'火锅'。留空表示获取附近推荐。"
                }
            },
            "required": []
        }

    def __init__(self, db=dbmanager, current_lng=None, current_lat=None):
        self.db = db
        self.current_lng = current_lng
        self.current_lat = current_lat

    def _query_poi(self, where_clause: str, params: tuple, limit: int = 500) -> pd.DataFrame:
        """
        查询 POI 候选集。距离排序在 Python 中统一完成，避免 SQL 的 LIMIT 先截断导致返回远处结果。
        """
        return self.db.get_df(
            f"SELECT poi_uid, name, type, lng, lat FROM poi WHERE {where_clause} LIMIT {limit}",
            params
        )

    def _build_fuzzy_keywords(self, keyword: str) -> list[str]:
        """
        构造模糊搜索关键词：完整关键词、前缀关键词、连续 2 字/3 字片段。
        """
        kw = keyword.strip()
        fuzzy_keywords = set()
        if len(kw) > 2:
            fuzzy_keywords.add(kw[:2])
        if len(kw) > 3:
            fuzzy_keywords.add(kw[:3])
        for size in (2, 3):
            if len(kw) >= size:
                for i in range(0, len(kw) - size + 1):
                    fuzzy_keywords.add(kw[i:i + size])
        fuzzy_keywords.discard(kw)
        return [item for item in fuzzy_keywords if item.strip()]

    def _merge_poi_rows(self, rows: pd.DataFrame, match_type: str, result_map: dict) -> None:
        """
        合并精确匹配和模糊匹配结果。同一个 POI 同时命中时，保留更高优先级的匹配类型。
        """
        priority = {"exact": 0, "fuzzy": 1, "nearby": 2}
        for _, row in rows.iterrows():
            poi_uid = row["poi_uid"]
            if poi_uid not in result_map or priority[match_type] < priority[result_map[poi_uid]["match_type"]]:
                result_map[poi_uid] = {
                    "poi_uid": poi_uid,
                    "name": row["name"],
                    "type": row["type"],
                    "lng": row["lng"],
                    "lat": row["lat"],
                    "match_type": match_type
                }

    def execute(self, arguments: dict) -> dict:
        keyword = arguments.get("keyword", "")
        result_map = {}
        
        if keyword:
            search_keyword = keyword.strip()

            # 1. 精准匹配：地点名称完整包含关键词，或类型完整包含关键词。
            # 关键词由 AI 根据上下文提炼，工具不再硬编码删除语气词/地点后缀。
            exact_df = self._query_poi(
                "name LIKE ? OR type LIKE ?",
                (f"%{search_keyword}%", f"%{search_keyword}%"),
                limit=2000
            )
            self._merge_poi_rows(exact_df, "exact", result_map)

            # 2. 模糊匹配：使用 AI 提炼后的关键词生成短片段，提升召回。
            fuzzy_keywords = self._build_fuzzy_keywords(search_keyword)
            if fuzzy_keywords:
                fuzzy_clauses = " OR ".join(["name LIKE ? OR type LIKE ?" for _ in fuzzy_keywords])
                fuzzy_params = tuple(param for item in fuzzy_keywords for param in (f"%{item}%", f"%{item}%"))
                fuzzy_df = self._query_poi(fuzzy_clauses, fuzzy_params, limit=3000)
                self._merge_poi_rows(fuzzy_df, "fuzzy", result_map)
        else:
            # 附近推荐：扩大候选范围后统一按距离排序，避免数据库返回顺序影响推荐质量
            if self.current_lng and self.current_lat:
                nearby_df = self.db.get_df(
                    """
                    SELECT poi_uid, name, type, lng, lat FROM poi 
                    WHERE lng BETWEEN ? AND ? 
                      AND lat BETWEEN ? AND ? 
                    LIMIT 2000
                    """,
                    (self.current_lng - 0.15, self.current_lng + 0.15, self.current_lat - 0.15, self.current_lat + 0.15)
                )
            else:
                nearby_df = self.db.get_df(
                    "SELECT poi_uid, name, type, lng, lat FROM poi LIMIT 100"
                )
            self._merge_poi_rows(nearby_df, "nearby", result_map)
            
        pois = []
        for row in result_map.values():
            dist = haversine_distance(self.current_lng, self.current_lat, row["lng"], row["lat"]) if self.current_lng and self.current_lat else 0
            # POI 数据通常来自国内地图服务，坐标系为 GCJ-02；百度地图底图使用 BD-09。
            # 这里只做 GCJ-02 -> BD-09，避免错误地按 WGS-84 二次偏移。
            bd_lng, bd_lat = gcj02_to_bd09(row["lng"], row["lat"])
            pois.append({
                "poi_uid": row["poi_uid"],
                "name": row["name"],
                "type": row["type"],
                "lng": bd_lng,
                "lat": bd_lat,
                "distance": dist,
                "match_type": row["match_type"]
            })
            
        # 始终按距离由近到远返回；无当前位置时保持查询顺序
        if self.current_lng and self.current_lat:
            pois.sort(key=lambda x: x["distance"])
            
        formatted_pois = []
        for p in pois[:10]:
            formatted_pois.append({
                "poi_uid": p["poi_uid"],
                "name": p["name"],
                "type": p["type"],
                "lng": p["lng"],
                "lat": p["lat"],
                "distance": f"{p['distance']:.1f}km",
                "match_type": p["match_type"]
            })
            
        return {"poi_list": formatted_pois}


class PlanRouteTool(Tool):
    """规划移动路线 (基于原生 SQL 检索)"""

    @property
    def name(self): return "plan_route"

    @property
    def description(self): return "规划从当前位置到目标地点的不同交通方式（打车/地铁/步行）的耗时与消耗预估"

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "target_poi_uid": {"type": "string", "description": "目的地 POI 的 uid"}
            },
            "required": ["target_poi_uid"]
        }

    def __init__(self, db=dbmanager, current_lng=None, current_lat=None):
        self.db = db
        self.current_lng = current_lng
        self.current_lat = current_lat

    def execute(self, arguments: dict) -> dict:
        target_poi_uid = arguments.get("target_poi_uid", "")
        
        # 原生 SQL 参数化查询目的地
        poi_df = self.db.get_df("SELECT name, lng, lat FROM poi WHERE poi_uid = ?", (target_poi_uid,))
        if poi_df.empty:
            return {"error": "POI 不存在"}
            
        row = poi_df.iloc[0]
        dist = haversine_distance(self.current_lng, self.current_lat, row["lng"], row["lat"])
        # POI 数据通常来自国内地图服务，坐标系为 GCJ-02；百度地图底图使用 BD-09。
        bd_lng, bd_lat = gcj02_to_bd09(row["lng"], row["lat"])
        
        return {
            "target_name": row["name"],
            "target_lng": bd_lng,
            "target_lat": bd_lat,
            "distance_km": round(dist, 2),
            "routes": [
                {"method": "taxi", "label": "打车", "cost_money": max(10, int(dist * 2.5)), "cost_time_min": int(dist / 40 * 60), "consume_stamina": -5},
                {"method": "subway", "label": "地铁", "cost_money": max(2, int(dist * 0.3)), "cost_time_min": int(dist / 35 * 60) + 10, "consume_stamina": -15},
                {"method": "walk", "label": "步行", "cost_money": 0, "cost_time_min": int(dist / 5 * 60), "consume_stamina": -30}
            ]
        }