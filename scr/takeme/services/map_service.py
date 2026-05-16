from core.config import settings
from core.response import success, error
from models.poi_model import POI
from sqlalchemy.orm import Session
from tools.tool import haversine_distance  # 通用距离计算

class MapService:
    def __init__(self, db: Session):
        self.db = db

    def search_poi(self, keyword: str = None, lng: float = None, lat: float = None) -> dict:
        """搜索POI，若无 keyword 则返回附近推荐"""
        query = self.db.query(POI)
        if keyword:
            query = query.filter(POI.name.contains(keyword))
        else:
            # 附近推荐：按距离排序取前10（简单实现）
            # 实际可结合数据库空间函数或地图API
            all_pois = query.all()
            # 计算距离并排序
            def distance(poi):
                return haversine_distance(lng, lat, poi.lng, poi.lat)
            all_pois.sort(key=distance)
            all_pois = all_pois[:10]
            # 因为已经取了所有数据，可以手动格式化
            poi_list = []
            for p in all_pois:
                dist = distance(p) if lng and lat else 0
                poi_list.append({
                    "poi_uid": p.poi_uid,
                    "name": p.name,
                    "type": p.type,
                    "distance": f"{dist:.1f}km",
                    "lng": p.lng,
                    "lat": p.lat
                })
            return success({"poi_list": poi_list})

        # 关键词查询结果
        results = query.all()
        poi_list = []
        for p in results:
            dist = ""
            if lng and lat:
                dist = f"{haversine_distance(lng, lat, p.lng, p.lat):.1f}km"
            poi_list.append({
                "poi_uid": p.poi_uid,
                "name": p.name,
                "type": p.type,
                "distance": dist,
                "lng": p.lng,
                "lat": p.lat
            })
        return success({"poi_list": poi_list})

    def estimate_route(self, target_poi_uid: str, current_lng: float, current_lat: float) -> dict:
        """为指定目的地计算不同交通方式的消耗预估"""
        poi = self.db.query(POI).filter(POI.poi_uid == target_poi_uid).first()
        if not poi:
            return error(400, "POI不存在")

        # 计算直线距离（km）
        dist_km = haversine_distance(current_lng, current_lat, poi.lng, poi.lat)

        # 简单估算公式（实际应调用地图API得到真实路线）
        # 打车：每公里 2.5 元，速度 40km/h，体力消耗 -5
        taxi_money = max(10, dist_km * 2.5)
        taxi_time = dist_km / 40 * 60
        taxi_stamina = -5

        # 地铁：每公里 0.3 元，速度 35km/h，体力消耗 -15
        subway_money = max(2, dist_km * 0.3)
        subway_time = dist_km / 35 * 60 + 10  # 进出站时间
        subway_stamina = -15

        # 步行：0 元，速度 5km/h，体力消耗 -30
        walk_money = 0
        walk_time = dist_km / 5 * 60
        walk_stamina = -30

        routes = [
            {"method": "taxi", "label": "打车",
             "cost_money": int(taxi_money), "cost_time_min": int(taxi_time),
             "consume_stamina": taxi_stamina},
            {"method": "subway", "label": "地铁",
             "cost_money": int(subway_money), "cost_time_min": int(subway_time),
             "consume_stamina": subway_stamina},
            {"method": "walk", "label": "步行",
             "cost_money": int(walk_money), "cost_time_min": int(walk_time),
             "consume_stamina": walk_stamina}
        ]
        return success({"routes": routes})