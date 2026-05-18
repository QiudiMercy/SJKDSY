from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.response import success, error
from services.game_service import GameService
from schemas.game_schema import SettleRequest

router = APIRouter(prefix="/api/game", tags=["Game"])

def get_db():
    from models.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/start")
def start_game(db: Session = Depends(get_db)):
    service = GameService(db)
    return service.start_new_game()

@router.get("/state")
def get_state(game_uid: str, db: Session = Depends(get_db)):
    service = GameService(db)
    return service.get_state(game_uid)

@router.post("/settle")
def settle(req: SettleRequest, db: Session = Depends(get_db)):
    service = GameService(db)
    return service.settle(req.game_uid)