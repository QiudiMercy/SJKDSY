from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schemas.action_schema import RouteEstimateRequest
from services.map_service import MapService

router = APIRouter(prefix="/api", tags=["Action"])

def get_db():
    from models.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/poi/search")
def search_poi(keyword: str = None, lng: float = None, lat: float = None, db: Session = Depends(get_db)):
    service = MapService(db)
    return service.search_poi(keyword, lng, lat)

@router.post("/action/route")
def estimate_route(req: RouteEstimateRequest, db: Session = Depends(get_db)):
    service = MapService(db)
    return service.estimate_route(req.target_poi_uid, req.current_lng, req.current_lat)