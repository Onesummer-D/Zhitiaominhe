from fastapi import APIRouter
from datetime import datetime, date
from models.database import get_db_connection

router = APIRouter(prefix="/api/stats", tags=["stats"])

@router.get("")
def get_stats():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 待调解总数（pending + mediating）
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM cases 
        WHERE status IN ('pending', 'mediating')
    """)
    pending = cursor.fetchone()["cnt"]

    # 今日新增
    today_str = date.today().isoformat()
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM cases 
        WHERE DATE(created_at) = ?
    """, (today_str,))
    today_new = cursor.fetchone()["cnt"]

    # 今日已结案（resolved + archived）
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM cases 
        WHERE status IN ('resolved', 'archived') 
        AND DATE(updated_at) = ?
    """, (today_str,))
    today_resolved = cursor.fetchone()["cnt"]

    conn.close()

    return {
        "pending": pending,
        "today_new": today_new,
        "today_resolved": today_resolved
    }
