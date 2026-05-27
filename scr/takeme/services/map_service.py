from core.config import settings, dbmanager
from tools.tool import haversine_distance
from tools.coord_convert import wgs84_to_bd09
import pandas as pd

class MapService:
    def __init__(self, db=dbmanager):
        self.db = db

    def _query_poi_with_bbox(self, kw: str, lng: float, lat: float) -> pd.DataFrame:
        """
        利用经纬度范围圈定（BBox）过滤并返回模糊检索候选集
        """
        if lng and lat:
            # 0.15 度约为 15km 范围
            df = self.db.get_df(
                """
                SELECT poi_uid, name, type, lng, lat FROM poi 
                WHERE name LIKE ? 
                  AND lng BETWEEN ? AND ? 
                  AND lat BETWEEN ? AND ? 
                LIMIT 500
                """,
                (f"%{kw}%", lng - 0.15, lng + 0.15, lat - 0.15, lat + 0.15)
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

    def search_poi(self, keyword: str = None, lng: float = None, lat: float = None) -> dict:
        """
        根据关键字搜索 POI点位，若空则检索附近的前10个推荐点位 (完全手写 SQL)
        """
        # 原生 SQL 检索
        if keyword:
            clean_keyword = keyword.strip()
            # 提炼核心名词：过滤口语、动词以及特定地点后缀
            for suffix in ["相亲角", "相亲", "那里", "这儿", "附近", "玩玩", "逛逛", "看看", "店", "门", "去", "吃", "喝", "玩"]:
                clean_keyword = clean_keyword.replace(suffix, "")
            clean_keyword = clean_keyword.strip()
            if not clean_keyword:
                clean_keyword = keyword

            # 1. 尝试清洗后的完整关键词查询
            poi_df = self._query_poi_with_bbox(clean_keyword, lng, lat)
            
            # 2. 备用降级：如果无结果且词长 > 4，截取前 4 字（如 "人民公园相亲角" 自动降级为 "人民公园"）
            if poi_df.empty and len(clean_keyword) > 4:
                poi_df = self._query_poi_with_bbox(clean_keyword[:4], lng, lat)
                
            # 3. 极速退化：如果依然无结果且词长 > 2，截取前 2 字（如 "宽窄巷子东门" -> "宽窄"）
            if poi_df.empty and len(clean_keyword) > 2:
                poi_df = self._query_poi_with_bbox(clean_keyword[:2], lng, lat)
        else:
            # 附近推荐：基于 BBox 筛选附近的点位，确保拉取到的绝对是附近最近的点位
            if lng and lat:
                poi_df = self.db.get_df(
                    """
                    SELECT poi_uid, name, type, lng, lat FROM poi 
                    WHERE lng BETWEEN ? AND ? 
                      AND lat BETWEEN ? AND ? 
                    LIMIT 200
                    """,
                    (lng - 0.08, lng + 0.08, lat - 0.08, lat + 0.08)
                )
            else:
                poi_df = self.db.get_df(
                    "SELECT poi_uid, name, type, lng, lat FROM poi LIMIT 100"
                )

        pois = []
        for _, row in poi_df.iterrows():
            dist = haversine_distance(lng, lat, row["lng"], row["lat"]) if lng and lat else 0
            bd_lng, bd_lat = wgs84_to_bd09(row["lng"], row["lat"])
            pois.append({
                "poi_uid": row["poi_uid"],
                "name": row["name"],
                "type": row["type"],
                "distance": dist,
                "lng": bd_lng,
                "lat": bd_lat
            })

        # 如果有当前定位且是空检索，按距离从近到远排序，取前10
        if lng and lat:
            pois.sort(key=lambda x: x["distance"])

        # 格式化距离并保留 10 条
        formatted_pois = []
        for p in pois[:10]:
            formatted_pois.append({
                "poi_uid": p["poi_uid"],
                "name": p["name"],
                "type": p["type"],
                "distance": f"{p['distance']:.1f}km" if lng and lat else "",
                "lng": p["lng"],
                "lat": p["lat"]
            })

        return {
            "code": 200,
            "data": {
                "poi_list": formatted_pois
            }
        }

    def estimate_route(self, target_poi_uid: str, current_lng: float, current_lat: float, transport_mode: str = "") -> dict:
        """
        根据目的地 POI 计算各种交通工具的耗时与资源消耗预估 (完全原生 SQL)
        """
        poi_df = self.db.get_df(
            "SELECT name, lng, lat FROM poi WHERE poi_uid = ?",
            (target_poi_uid,)
        )
        if poi_df.empty:
            return {"code": 400, "msg": "POI 点不存在", "data": None}

        row = poi_df.iloc[0]
        # 计算两点间直线距离 (km)
        dist_km = haversine_distance(current_lng, current_lat, row["lng"], row["lat"])

        # 简单交通消耗预估公式
        all_routes = {
            "walking": {
                "method": "walk",
                "label": "步行",
                "cost_money": 0,
                "cost_time_min": max(1, int(dist_km / 5 * 60)),
                "consume_stamina": -max(1, int(dist_km * 6))
            },
            "bicycling": {
                "method": "bicycle",
                "label": "骑行",
                "cost_money": 2,
                "cost_time_min": max(1, int(dist_km / 15 * 60)),
                "consume_stamina": -max(1, int(dist_km * 3))
            },
            "driving": {
                "method": "taxi",
                "label": "驾车",
                "cost_money": max(10, int(dist_km * 2.5)),
                "cost_time_min": max(1, int(dist_km / 40 * 60)),
                "consume_stamina": -5
            },
            "transit": {
                "method": "subway",
                "label": "公交/地铁",
                "cost_money": max(2, int(dist_km * 0.3)),
                "cost_time_min": max(1, int(dist_km / 35 * 60)) + 10,
                "consume_stamina": -15
            },
        }

        if transport_mode and transport_mode in all_routes:
            routes = [all_routes[transport_mode]]
        else:
            routes = list(all_routes.values())

        return {
            "code": 200,
            "data": {
                "routes": routes
            }
        }

    def generate_map_image(
        self,
        center_lng: float,
        center_lat: float,
        zoom: int = 14,
        markers: list = None,
        route: list = None
    ) -> dict:
        """
        生成百度地图静态图 URL API，在手写 SQL 架构中保留
        """
        import urllib.parse

        ak = settings.map_api_key
        if not ak:
            return {"code": 400, "msg": "百度地图 API Key 未配置", "data": None}

        base_url = "https://api.map.baidu.com/staticimage/v2"

        # 构建标注
        marker_params = ""
        if markers:
            marker_parts = []
            for m in markers:
                lng = m.get("lng", center_lng)
                lat = m.get("lat", center_lat)
                marker_parts.append(f"{lng},{lat}")
            if marker_parts:
                marker_params = "&".join([f"markers={p}" for p in marker_parts])

        # 构建路线参数
        path_param = ""
        if route and len(route) >= 2:
            path_points = "|".join([f"{p[0]},{p[1]}" for p in route])
            path_param = f"&path={urllib.parse.quote(path_points)}&pathStyles=0xff0000,3,1"

        # 构建完整静态 URL
        width, height = 600, 400
        center_param = f"{center_lng},{center_lat}"
        url = (
            f"{base_url}?ak={ak}&center={center_param}&width={width}&height={height}"
            f"&zoom={zoom}"
        )
        if marker_params:
            url += f"&{marker_params}"
        if path_param:
            url += path_param

        return {
            "code": 200,
            "data": {
                "image_url": url,
                "center": {"lng": center_lng, "lat": center_lat},
                "zoom": zoom
            }
        }