from abc import ABC, abstractmethod
import math


class Tool(ABC):
    """LLM Function Calling 工具基类"""

    name: str
    description: str
    parameters: dict

    @property
    def schema(self) -> dict:
        """返回 OpenAI 兼容的 function schema"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }

    @abstractmethod
    def execute(self, arguments: dict) -> str:
        """执行工具，返回结果"""
        ...

def haversine_distance(lng1, lat1, lng2, lat2):
    """计算两点间直线距离（km）"""
    R = 6371.0
    lng1, lat1, lng2, lat2 = map(math.radians, [lng1, lat1, lng2, lat2])
    dlon = lng2 - lng1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def insert_mock_poi(db):
    from models.poi_model import POI
    mock_data = [
        POI(poi_uid="p_001", name="成都远洋太古里", type="商业街", lng=104.091122, lat=30.658688),
        POI(poi_uid="p_002", name="宽窄巷子", type="景点", lng=104.059491, lat=30.669532),
        POI(poi_uid="p_003", name="锦里", type="景点", lng=104.053633, lat=30.648847),
    ]
    db.add_all(mock_data)
    db.commit()