from pydantic import BaseModel
from typing import Optional, List

class InitState(BaseModel):
    time: str
    money: int
    stamina: int
    mood: int
    fullness: int
    location: dict

class GameStartResponse(BaseModel):
    game_uid: str
    init_state: InitState

class GameStateResponse(BaseModel):
    time: str
    money: int
    stamina: int
    mood: int
    fullness: int
    location: dict
    is_game_over: bool

class SettleRequest(BaseModel):
    game_uid: str

class SettleResponse(BaseModel):
    score: int
    evaluation: str
    route_summary: List[str]