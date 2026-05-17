from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
import json
from datetime import datetime

from models.database import get_db_connection
from models.schemas import CaseCreate, CaseUpdate, CaseOut

router = APIRouter(prefix="/api/cases", tags=["cases"])

def generate_case_no():
    now = datetime.now()
    prefix = f"QM-{now.strftime('%Y%m%d')}"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM cases WHERE case_no LIKE ?",
        (prefix + "-%",)
    )
    count = cursor.fetchone()["cnt"] + 1
    conn.close()
    return f"{prefix}-{count:03d}"

def row_to_dict(row):
    d = dict(row)
    # 解析 JSON 字段
    for key in ["analysis_result", "generated_documents"]:
        if d.get(key):
            try:
                d[key] = json.loads(d[key])
            except:
                d[key] = None
    d["custom_law_involved"] = bool(d.get("custom_law_involved", 0))
    return d

@router.get("", response_model=List[CaseOut])
def list_cases(
    status: Optional[str] = Query(None),
    dispute_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM cases WHERE 1=1"
    params = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if dispute_type:
        query += " AND dispute_type = ?"
        params.append(dispute_type)
    if search:
        query += " AND (title LIKE ? OR applicant LIKE ? OR respondent LIKE ? OR description LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like, like, like])
    query += " ORDER BY updated_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]

@router.get("/{case_id}", response_model=CaseOut)
def get_case(case_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Case not found")
    return row_to_dict(row)

@router.post("", response_model=CaseOut)
def create_case(case: CaseCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    case_no = generate_case_no()
    now = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO cases (
            case_no, title, applicant, respondent, dispute_type,
            custom_law_involved, description, analysis_result,
            generated_documents, status, region, ethnicity,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        case_no, case.title, case.applicant, case.respondent, case.dispute_type,
        1 if case.custom_law_involved else 0,
        case.description,
        json.dumps(case.analysis_result, ensure_ascii=False) if case.analysis_result else None,
        json.dumps(case.generated_documents, ensure_ascii=False) if case.generated_documents else None,
        case.status, case.region, case.ethnicity, now, now
    ))
    conn.commit()
    case_id = cursor.lastrowid
    cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row)

@router.put("/{case_id}", response_model=CaseOut)
def update_case(case_id: int, case: CaseUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    # 先查存在
    cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Case not found")

    fields = []
    values = []
    if case.title is not None:
        fields.append("title = ?")
        values.append(case.title)
    if case.applicant is not None:
        fields.append("applicant = ?")
        values.append(case.applicant)
    if case.respondent is not None:
        fields.append("respondent = ?")
        values.append(case.respondent)
    if case.dispute_type is not None:
        fields.append("dispute_type = ?")
        values.append(case.dispute_type)
    if case.custom_law_involved is not None:
        fields.append("custom_law_involved = ?")
        values.append(1 if case.custom_law_involved else 0)
    if case.description is not None:
        fields.append("description = ?")
        values.append(case.description)
    if case.analysis_result is not None:
        fields.append("analysis_result = ?")
        values.append(json.dumps(case.analysis_result, ensure_ascii=False))
    if case.generated_documents is not None:
        fields.append("generated_documents = ?")
        values.append(json.dumps(case.generated_documents, ensure_ascii=False))
    if case.status is not None:
        fields.append("status = ?")
        values.append(case.status)
    if case.region is not None:
        fields.append("region = ?")
        values.append(case.region)
    if case.ethnicity is not None:
        fields.append("ethnicity = ?")
        values.append(case.ethnicity)

    fields.append("updated_at = ?")
    values.append(datetime.now().isoformat())
    values.append(case_id)

    sql = f"UPDATE cases SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(sql, values)
    conn.commit()

    cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
    row = cursor.fetchone()
    conn.close()
    return row_to_dict(row)

@router.delete("/{case_id}")
def delete_case(case_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cases WHERE id = ?", (case_id,))
    conn.commit()
    conn.close()
    return {"success": True}
