from fastapi import APIRouter
from core.config import dbmanager

router = APIRouter(prefix="/api/records", tags=["Records"])

@router.get("/list")
def get_records(page: int = 1, limit: int = 10):
    """
    原生 SQL 分页检索已结束的游玩战绩记录
    """
    # 统计总数
    total_df = dbmanager.get_df("SELECT COUNT(*) as total FROM games WHERE is_active = 0")
    total = int(total_df.iloc[0]["total"]) if not total_df.empty else 0
    
    offset = (page - 1) * limit
    
    # 分页检索
    games_df = dbmanager.get_df(
        """
        SELECT game_uid, start_time, score, current_money, evaluation 
        FROM games 
        WHERE is_active = 0 
        ORDER BY end_time DESC 
        LIMIT ? OFFSET ?
        """,
        (limit, offset)
    )
    
    records = []
    for _, row in games_df.iterrows():
        st = row["start_time"]
        # 转换时间显示格式
        formatted_start = st[:16] if isinstance(st, str) else ""
        records.append({
            "game_uid": row["game_uid"],
            "start_time": formatted_start,
            "score": int(row["score"]) if row["score"] is not None else 0,
            "remain_money": int(row["current_money"]),
            "evaluation": row["evaluation"] if row["evaluation"] is not None else ""
        })

    return {
        "code": 200,
        "data": {
            "records": records,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if total > 0 else 1
        }
    }