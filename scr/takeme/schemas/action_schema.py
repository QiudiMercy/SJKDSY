from pydantic import BaseModel
from typing import List, Optional

class POIItem(BaseModel):
    poi_uid: str
    name: str
    type: str
    distance: str
    lng: float
    lat: float

class POISearchResponse(BaseModel):
    poi_list: List[POIItem]

class RouteEstimateRequest(BaseModel):
    target_poi_uid: str
    current_lng: float
    current_lat: float
    transport_mode: str = ""  # walking / bicycling / driving / transit，空则返回全部

class RouteOption(BaseModel):
    method: str
    label: str
    cost_money: int
    cost_time_min: int
    consume_stamina: int

class RouteEstimateResponse(BaseModel):
    routes: List[RouteOption]

class MapImageRequest(BaseModel):
    center_lng: float
    center_lat: float
    zoom: Optional[int] = 14
    markers: Optional[List[dict]] = None
    route: Optional[List[List[float]]] = None


class MapImageResponse(BaseModel):
    image_url: str
    center: dict
    zoom: int