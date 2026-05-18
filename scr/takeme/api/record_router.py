from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.response import success

router = APIRouter(prefix="/api/records", tags=["Records"])

def get_db():
    from models.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/list")
def get_records(page: int = 1, limit: int = 10, db: Session = Depends(get_db)):
    # 简单示例，实际可查询已结束的游戏记录
    # 这里先返回空列表，后续扩展
    return success({
        "records": []   # TODO: 从 games 表查询 is_active=False 的记录
    })