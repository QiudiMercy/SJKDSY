from fastapi import APIRouter
from schemas.action_schema import RouteEstimateRequest, MapImageRequest
from services.map_service import MapService

router = APIRouter(prefix="/api", tags=["Action"])

@router.get("/poi/search")
def search_poi(keyword: str = None, lng: float = None, lat: float = None):
    service = MapService()
    return service.search_poi(keyword, lng, lat)

@router.post("/action/route")
def estimate_route(req: RouteEstimateRequest):
    service = MapService()
    return service.estimate_route(req.target_poi_uid, req.current_lng, req.current_lat, req.transport_mode)

@router.post("/map/image")
def generate_map_image(req: MapImageRequest):
    service = MapService()
    return service.generate_map_image(
        center_lng=req.center_lng,
        center_lat=req.center_lat,
        zoom=req.zoom or 14,
        markers=req.markers,
        route=req.route
    )