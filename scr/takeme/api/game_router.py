from fastapi import APIRouter
from services.game_service import GameService
from schemas.game_schema import SettleRequest

router = APIRouter(prefix="/api/game", tags=["Game"])

@router.post("/start")
def start_game():
    service = GameService()
    return service.start_new_game()

@router.get("/state")
def get_state(game_uid: str):
    service = GameService()
    return service.get_state(game_uid)

@router.post("/settle")
def settle(req: SettleRequest):
    service = GameService()
    return service.settle(req.game_uid)