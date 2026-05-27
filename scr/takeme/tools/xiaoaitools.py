from typing import Optional, List
from tools.tool import Tool, haversine_distance
from tools.coord_convert import wgs84_to_bd09
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
    def description(self): return "搜索成都的 POI 地点，可指定关键词或获取附近推荐"

    @property
    def parameters(self):
        return {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "搜索关键词，如'火锅'、'公园'"}
            },
            "required": []
        }

    def __init__(self, db=dbmanager, current_lng=None, current_lat=None):
        self.db = db
        self.current_lng = current_lng
        self.current_lat = current_lat

    def _query_poi_with_bbox(self, kw: str) -> pd.DataFrame:
        """
        利用经纬度范围圈定（BBox）过滤并返回模糊检索候选集
        """
        if self.current_lng and self.current_lat:
            df = self.db.get_df(
                """
                SELECT poi_uid, name, type, lng, lat FROM poi 
                WHERE name LIKE ? 
                  AND lng BETWEEN ? AND ? 
                  AND lat BETWEEN ? AND ? 
                LIMIT 500
                """,
                (f"%{kw}%", self.current_lng - 0.15, self.current_lng + 0.15, self.current_lat - 0.15, self.current_lat + 0.15)
            )
            # 容错：如果 BBox 没搜够，退化回全局模糊检索
            if len(df) < 5:
                df = self.db.get_df(
                    "SELECT poi_uid, name, type, lng, lat FROM poi WHERE name LIKE ? LIMIT 500",
                    (f"%{kw}%",)
                )
            return df
        else:
            return self.db.get_df(
                "SELECT poi_uid, name, type, lng, lat FROM poi WHERE name LIKE ? LIMIT 500",
                (f"%{kw}%",)
            )

    def execute(self, arguments: dict) -> dict:
        keyword = arguments.get("keyword", "")
        
        # 原生 SQL 查询 'poi' 表 (引入 BBox 筛选与 500 条限制提升准确度)
        if keyword:
            clean_keyword = keyword.strip()
            # 提炼核心名词：过滤口语、动词以及特定地点后缀
            for suffix in ["相亲角", "相亲", "那里", "这儿", "附近", "玩玩", "逛逛", "看看", "店", "门", "去", "吃", "喝", "玩"]:
                clean_keyword = clean_keyword.replace(suffix, "")
            clean_keyword = clean_keyword.strip()
            if not clean_keyword:
                clean_keyword = keyword

            # 1. 尝试清洗后的完整关键词查询
            poi_df = self._query_poi_with_bbox(clean_keyword)
            
            # 2. 备用降级：如果无结果且词长 > 4，截取前 4 字（如 "人民公园相亲角" 自动降级为 "人民公园"）
            if poi_df.empty and len(clean_keyword) > 4:
                poi_df = self._query_poi_with_bbox(clean_keyword[:4])
                
            # 3. 极速退化：如果依然无结果且词长 > 2，截取前 2 字（如 "宽窄巷子东门" -> "宽窄"）
            if poi_df.empty and len(clean_keyword) > 2:
                poi_df = self._query_poi_with_bbox(clean_keyword[:2])
        else:
            # 附近推荐：基于 BBox 筛选附近的点位
            if self.current_lng and self.current_lat:
                poi_df = self.db.get_df(
                    """
                    SELECT poi_uid, name, type, lng, lat FROM poi 
                    WHERE lng BETWEEN ? AND ? 
                      AND lat BETWEEN ? AND ? 
                    LIMIT 200
                    """,
                    (self.current_lng - 0.08, self.current_lng + 0.08, self.current_lat - 0.08, self.current_lat + 0.08)
                )
            else:
                poi_df = self.db.get_df(
                    "SELECT poi_uid, name, type, lng, lat FROM poi LIMIT 100"
                )
            
        pois = []
        for _, row in poi_df.iterrows():
            dist = haversine_distance(self.current_lng, self.current_lat, row["lng"], row["lat"]) if self.current_lng and self.current_lat else 0
            bd_lng, bd_lat = wgs84_to_bd09(row["lng"], row["lat"])
            pois.append({
                "poi_uid": row["poi_uid"],
                "name": row["name"],
                "type": row["type"],
                "lng": bd_lng,
                "lat": bd_lat,
                "distance": dist
            })
            
        # 如果是附近推荐，按距离排序取前10名
        if self.current_lng and self.current_lat:
            pois.sort(key=lambda x: x["distance"])
            
        # 格式化距离字符串并截断
        formatted_pois = []
        for p in pois[:10]:
            formatted_pois.append({
                "poi_uid": p["poi_uid"],
                "name": p["name"],
                "type": p["type"],
                "lng": p["lng"],
                "lat": p["lat"],
                "distance": f"{p['distance']:.1f}km"
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
        bd_lng, bd_lat = wgs84_to_bd09(row["lng"], row["lat"])
        
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