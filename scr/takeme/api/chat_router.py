from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from schemas.chat_schema import SendMessageRequest
from services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["Chat"])

def get_db():
    from models.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/send")
def send_message(req: SendMessageRequest, db: Session = Depends(get_db)):
    service = ChatService(db)
    return service.handle_message(req.game_uid, req.content)

@router.get("/history")
def get_history(game_uid: str, db: Session = Depends(get_db)):
    service = ChatService(db)
    return service.get_history(game_uid)